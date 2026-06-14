"""SLO definitions and status snapshots."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.models import JobRun

SLO_TARGETS = {
    "api_availability_pct": 99.5,
    "job_completion_p95_seconds": 300,
    "sync_freshness_hours": 26,
}


async def compute_slo_status(db: AsyncSession, workspace_id: UUID) -> dict:
    since = datetime.now(UTC) - timedelta(hours=24)
    base_filter = (JobRun.created_at >= since, JobRun.workspace_id == workspace_id)

    total_jobs = await db.execute(
        select(func.count()).select_from(JobRun).where(*base_filter)
    )
    failed_jobs = await db.execute(
        select(func.count())
        .select_from(JobRun)
        .where(*base_filter, JobRun.status == "failed")
    )
    queued_jobs = await db.execute(
        select(func.count())
        .select_from(JobRun)
        .where(*base_filter, JobRun.status == "queued")
    )
    running_jobs = await db.execute(
        select(func.count())
        .select_from(JobRun)
        .where(*base_filter, JobRun.status == "running")
    )

    total = int(total_jobs.scalar_one())
    failed = int(failed_jobs.scalar_one())
    success_rate = 100.0 if total == 0 else ((total - failed) / total) * 100

    return {
        "workspace_id": str(workspace_id),
        "targets": SLO_TARGETS,
        "current": {
            "job_success_rate_pct": round(success_rate, 2),
            "jobs_total_24h": total,
            "jobs_failed_24h": failed,
            "jobs_queued": int(queued_jobs.scalar_one()),
            "jobs_running": int(running_jobs.scalar_one()),
        },
        "status": {
            "job_success": success_rate >= SLO_TARGETS["api_availability_pct"],
        },
    }


async def workspace_job_metrics(db: AsyncSession, workspace_id: UUID) -> dict:
    """Workspace-scoped job metrics for ops dashboard (no cross-tenant HTTP counters)."""
    since = datetime.now(UTC) - timedelta(hours=24)
    by_status = await db.execute(
        select(JobRun.status, func.count())
        .where(JobRun.workspace_id == workspace_id, JobRun.created_at >= since)
        .group_by(JobRun.status)
    )
    status_counts = {row[0]: int(row[1]) for row in by_status.all()}
    total = sum(status_counts.values())
    failed = status_counts.get("failed", 0)
    return {
        "workspace_id": str(workspace_id),
        "jobs_24h_total": total,
        "jobs_24h_by_status": status_counts,
        "job_error_rate_pct": round((failed / total) * 100, 2) if total else 0.0,
    }
