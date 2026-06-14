"""Execute adapter-backed execution jobs."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.execution.dispatcher import dispatch_execution_job
from exposureflow_api.integrations.sync_helpers import finalize_job_run
from exposureflow_api.models import JobRun
from exposureflow_api.models.execution_content import ExecutionJob


async def run_execution_job(db: AsyncSession, run: JobRun) -> None:
    job_id = (run.input_json or {}).get("execution_job_id")
    if not job_id:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="MISSING_EXECUTION_JOB_ID",
            error_message="execution_job_id is required",
        )
        return
    job = await db.get(ExecutionJob, UUID(str(job_id)))
    if job is None or job.workspace_id != run.workspace_id:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="JOB_NOT_FOUND",
            error_message="Execution job not found",
        )
        return
    await dispatch_execution_job(db, job)
    await finalize_job_run(
        run,
        success=job.status == "completed",
        output={"execution_job_id": str(job.id), "status": job.status, **(job.output_json or {})},
        error_code=None if job.status == "completed" else "ADAPTER_FAILED",
        error_message=job.error_message,
    )
