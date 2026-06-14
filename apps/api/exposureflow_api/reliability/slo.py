"""SLO definitions and status snapshots."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.models import JobRun
from exposureflow_api.observability.metrics import metrics_snapshot

SLO_TARGETS = {
    "api_availability_pct": 99.5,
    "job_completion_p95_seconds": 300,
    "sync_freshness_hours": 26,
}


async def compute_slo_status(db: AsyncSession) -> dict:
    since = datetime.now(UTC) - timedelta(hours=24)
    total_jobs = await db.execute(
        select(func.count()).select_from(JobRun).where(JobRun.created_at >= since)
    )
    failed_jobs = await db.execute(
        select(func.count())
        .select_from(JobRun)
        .where(JobRun.created_at >= since, JobRun.status == "failed")
    )
    total = int(total_jobs.scalar_one())
    failed = int(failed_jobs.scalar_one())
    success_rate = 100.0 if total == 0 else ((total - failed) / total) * 100

    snap = metrics_snapshot()
    error_rate = snap.get("http_error_rate_pct", 0.0)

    return {
        "targets": SLO_TARGETS,
        "current": {
            "job_success_rate_pct": round(success_rate, 2),
            "http_error_rate_pct": error_rate,
            "api_requests_24h": snap.get("http_requests_total", 0),
        },
        "status": {
            "job_success": success_rate >= SLO_TARGETS["api_availability_pct"],
            "http_errors": error_rate < (100 - SLO_TARGETS["api_availability_pct"]),
        },
    }
