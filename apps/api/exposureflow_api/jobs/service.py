import asyncio
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.database import async_session_factory
from exposureflow_api.jobs.celery_app import celery_app
from exposureflow_api.jobs.handlers import dispatch_job_run
from exposureflow_api.billing import quota as billing_quota
from exposureflow_api.execution.capacity import record_usage_event
from exposureflow_api.reliability.backpressure import assert_queue_capacity
from exposureflow_api.models import JobDefinition, JobRun

JOB_TYPE_QUOTA_METRIC: dict[str, str] = {
    "gsc.sync": "gsc_rows",
    "serp.snapshot": "serp_snapshots",
    "content.generate.grounded_draft": "content_generation_runs",
    "content.publish_gate.check": "claim_verification_runs",
    "knowledge.fact.embed": "knowledge_embedding",
    "knowledge.source.ingest": "knowledge_sources",
    "report.monthly.generate": "report_exports",
}


async def _get_job_definition(db: AsyncSession, job_type: str) -> JobDefinition | None:
    result = await db.execute(select(JobDefinition).where(JobDefinition.job_type == job_type))
    return result.scalar_one_or_none()


async def _find_job_by_idempotency_key(
    db: AsyncSession, workspace_id: UUID, idempotency_key: str
) -> JobRun | None:
    result = await db.execute(
        select(JobRun).where(
            JobRun.workspace_id == workspace_id,
            JobRun.idempotency_key == idempotency_key,
        )
    )
    return result.scalar_one_or_none()


def _requeue_existing_run(run: JobRun) -> None:
    run.status = "queued"
    run.error_code = None
    run.error_message = None
    run.output_json = {}
    run.started_at = None
    run.completed_at = None
    celery_app.send_task(
        "exposureflow_api.jobs.tasks.execute_job_run",
        args=[str(run.id)],
        queue="default",
    )


async def enqueue_job(
    db: AsyncSession,
    *,
    workspace_id: UUID,
    job_type: str,
    site_id: UUID | None = None,
    input_json: dict | None = None,
    idempotency_key: str | None = None,
) -> JobRun:
    if idempotency_key:
        existing = await _find_job_by_idempotency_key(db, workspace_id, idempotency_key)
        if existing is not None:
            if existing.status == "failed":
                _requeue_existing_run(existing)
                await db.flush()
            return existing

    metric = JOB_TYPE_QUOTA_METRIC.get(job_type)
    if metric:
        await billing_quota.check_quota(db, workspace_id, metric)

    await assert_queue_capacity(db, workspace_id)

    definition = await _get_job_definition(db, job_type)
    run = JobRun(
        workspace_id=workspace_id,
        site_id=site_id,
        job_definition_id=definition.id if definition else None,
        job_type=job_type,
        status="queued",
        idempotency_key=idempotency_key,
        input_json=input_json or {},
    )
    db.add(run)
    await db.flush()

    if metric:
        await record_usage_event(
            db,
            workspace_id=workspace_id,
            metric=metric,
            site_id=site_id,
            idempotency_key=idempotency_key or f"job-run-{run.id}",
        )

    celery_app.send_task(
        "exposureflow_api.jobs.tasks.execute_job_run",
        args=[str(run.id)],
        queue="default",
    )
    return run


async def _execute_job_run_async(job_run_id: UUID) -> None:
    async with async_session_factory() as db:
        result = await db.execute(select(JobRun).where(JobRun.id == job_run_id))
        run = result.scalar_one_or_none()
        if run is None:
            return

        run.status = "running"
        run.started_at = datetime.now(UTC)
        await db.commit()

        try:
            await dispatch_job_run(db, run)
        except Exception as exc:  # noqa: BLE001
            run.status = "failed"
            run.error_code = "JOB_EXECUTION_FAILED"
            run.error_message = str(exc)
            run.completed_at = datetime.now(UTC)
        await db.commit()


def execute_job_run_sync(job_run_id: str) -> None:
    asyncio.run(_execute_job_run_async(UUID(job_run_id)))
