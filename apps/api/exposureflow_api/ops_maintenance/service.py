"""Daily ops health run orchestration."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api import __version__
from exposureflow_api.config import settings
from exposureflow_api.models.ops_health import OpsHealthRun, OpsHealthSignal
from exposureflow_api.ops_maintenance.classifier import aggregate_run_status
from exposureflow_api.ops_maintenance.collector import collect_ops_health
from exposureflow_api.ops_maintenance.schemas import (
    OpsHealthRunOut,
    OpsHealthSignalOut,
    OpsMaintenanceLatestResponse,
    OpsMaintenanceRunResponse,
)
from exposureflow_api.ops_maintenance.summarizer import build_summary
from exposureflow_api.ops_maintenance.notifications import dispatch_ops_health_notifications


def _run_out(run: OpsHealthRun) -> OpsHealthRunOut:
    return OpsHealthRunOut(
        id=run.id,
        status=run.status,
        trigger=run.trigger,
        started_at=run.started_at,
        completed_at=run.completed_at,
        summary_title=run.summary_title,
        summary_markdown=run.summary_markdown,
        llm_provider=run.llm_provider,
        llm_model=run.llm_model,
    )


def _signal_out(row: OpsHealthSignal) -> OpsHealthSignalOut:
    return OpsHealthSignalOut(
        id=row.id,
        severity=row.severity,
        category=row.category,
        check_id=row.check_id,
        title=row.title,
        message=row.message,
        recommended_action=row.recommended_action,
        action_type=row.action_type,
        workspace_id=row.workspace_id,
        site_id=row.site_id,
        evidence_json=row.evidence_json or {},
    )


async def run_daily_ops_health(
    db: AsyncSession,
    *,
    trigger: str = "scheduled",
    use_llm_summary: bool = True,
) -> OpsHealthRun:
    run = OpsHealthRun(
        status="running",
        trigger=trigger,
        metadata_json={
            "app_env": settings.app_env,
            "api_version": __version__,
            "thresholds": {
                "failed_jobs_warn": 3,
                "failed_jobs_critical": 10,
            },
        },
    )
    db.add(run)
    await db.flush()

    check_results = await collect_ops_health(db)
    signal_rows: list[OpsHealthSignal] = []
    for result in check_results:
        row = OpsHealthSignal(
            run_id=run.id,
            workspace_id=result.workspace_id,
            site_id=result.site_id,
            check_id=result.check_id,
            category=result.category,
            severity=result.severity,
            title=result.title,
            message=result.message,
            evidence_json=result.evidence,
            recommended_action=result.recommended_action,
            action_type=result.action_type,
        )
        db.add(row)
        signal_rows.append(row)

    run.status = aggregate_run_status(check_results)
    title, markdown, llm_provider, llm_model = await build_summary(
        check_results,
        use_llm=use_llm_summary,
    )
    run.summary_title = title
    run.summary_markdown = markdown
    run.llm_provider = llm_provider
    run.llm_model = llm_model
    run.completed_at = datetime.now(UTC)
    notify_meta = await dispatch_ops_health_notifications(run, check_results)
    run.metadata_json = {**(run.metadata_json or {}), "notifications": notify_meta}
    await db.flush()
    return run


async def get_latest_ops_health(db: AsyncSession) -> OpsMaintenanceLatestResponse:
    run = (
        await db.execute(
            select(OpsHealthRun).order_by(OpsHealthRun.started_at.desc()).limit(1)
        )
    ).scalar_one_or_none()
    if run is None:
        return OpsMaintenanceLatestResponse(run=None, signals=[])
    signals = list(
        (
            await db.execute(
                select(OpsHealthSignal)
                .where(OpsHealthSignal.run_id == run.id)
                .order_by(OpsHealthSignal.severity.desc(), OpsHealthSignal.created_at)
            )
        ).scalars().all()
    )
    return OpsMaintenanceLatestResponse(
        run=_run_out(run),
        signals=[_signal_out(s) for s in signals],
    )


async def list_ops_health_runs(db: AsyncSession, *, limit: int = 30) -> list[OpsHealthRunOut]:
    rows = list(
        (
            await db.execute(
                select(OpsHealthRun).order_by(OpsHealthRun.started_at.desc()).limit(limit)
            )
        ).scalars().all()
    )
    return [_run_out(r) for r in rows]


async def run_ops_health_manual(
    db: AsyncSession,
    *,
    use_llm_summary: bool = True,
) -> OpsMaintenanceRunResponse:
    run = await run_daily_ops_health(db, trigger="manual", use_llm_summary=use_llm_summary)
    signals = list(
        (
            await db.execute(
                select(OpsHealthSignal).where(OpsHealthSignal.run_id == run.id)
            )
        ).scalars().all()
    )
    return OpsMaintenanceRunResponse(
        run=_run_out(run),
        signals=[_signal_out(s) for s in signals],
    )
