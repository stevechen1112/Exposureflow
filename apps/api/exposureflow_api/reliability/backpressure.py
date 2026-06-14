"""Queue backpressure before enqueueing jobs."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.common.errors import APIError
from exposureflow_api.models import JobRun

MAX_QUEUED_JOBS_PER_WORKSPACE = 100


async def assert_queue_capacity(db: AsyncSession, workspace_id: UUID) -> None:
    result = await db.execute(
        select(func.count())
        .select_from(JobRun)
        .where(
            JobRun.workspace_id == workspace_id,
            JobRun.status.in_(("queued", "running")),
        )
    )
    count = int(result.scalar_one())
    if count >= MAX_QUEUED_JOBS_PER_WORKSPACE:
        raise APIError(
            code="QUEUE_BACKPRESSURE",
            message="Too many pending jobs for this workspace.",
            status_code=429,
            details={"queued_or_running": count, "limit": MAX_QUEUED_JOBS_PER_WORKSPACE},
        )
