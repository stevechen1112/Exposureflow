"""Execution plane service — job lifecycle."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.common.errors import not_found
from exposureflow_api.execution.dispatcher import dispatch_execution_job
from exposureflow_api.models.execution_content import ExecutionJob


async def list_jobs(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
    *,
    status: str | None = None,
) -> list[ExecutionJob]:
    stmt = select(ExecutionJob).where(
        ExecutionJob.workspace_id == workspace_id,
        ExecutionJob.site_id == site_id,
    )
    if status:
        stmt = stmt.where(ExecutionJob.status == status)
    result = await db.execute(stmt.order_by(ExecutionJob.created_at.desc()))
    return list(result.scalars().all())


async def create_job(db: AsyncSession, workspace_id: UUID, **fields) -> ExecutionJob:
    row = ExecutionJob(workspace_id=workspace_id, **fields)
    db.add(row)
    await db.flush()
    return row


async def get_job(db: AsyncSession, workspace_id: UUID, job_id: UUID) -> ExecutionJob:
    row = await db.get(ExecutionJob, job_id)
    if row is None or row.workspace_id != workspace_id:
        raise not_found("Execution job")
    return row


async def cancel_job(db: AsyncSession, workspace_id: UUID, job_id: UUID) -> ExecutionJob:
    row = await get_job(db, workspace_id, job_id)
    if row.status in ("completed", "failed", "cancelled"):
        return row
    row.status = "cancelled"
    row.completed_at = datetime.now(timezone.utc)
    await db.flush()
    return row


async def retry_job(db: AsyncSession, workspace_id: UUID, job_id: UUID) -> ExecutionJob:
    row = await get_job(db, workspace_id, job_id)
    if row.status not in ("failed", "cancelled"):
        raise not_found("Execution job")
    row.status = "queued"
    row.error_message = None
    row.started_at = None
    row.completed_at = None
    await db.flush()
    return row


async def execute_job(db: AsyncSession, workspace_id: UUID, job_id: UUID) -> ExecutionJob:
    row = await get_job(db, workspace_id, job_id)
    if row.status not in ("queued", "failed", "cancelled"):
        raise not_found("Execution job")
    return await dispatch_execution_job(db, row)
