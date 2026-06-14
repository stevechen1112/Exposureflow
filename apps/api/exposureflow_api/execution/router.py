from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.auth.jwt import AuthContext
from exposureflow_api.auth.permissions import require_permission
from exposureflow_api.database import get_db
from exposureflow_api.execution import service
from exposureflow_api.execution.schemas import ExecutionJobCreate, ExecutionJobResponse
from exposureflow_api.exposure.deps import get_site_in_workspace

router = APIRouter(prefix="/api/v1/execution", tags=["execution"])


@router.get("/jobs", response_model=list[ExecutionJobResponse])
async def list_jobs(
    site_id: UUID,
    status: str | None = None,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    return await service.list_jobs(db, workspace_id, site_id, status=status)


@router.post("/jobs", response_model=ExecutionJobResponse)
async def create_job(
    body: ExecutionJobCreate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("job:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, body.site_id)
    row = await service.create_job(db, workspace_id, **body.model_dump())
    await db.commit()
    await db.refresh(row)
    return row


@router.get("/jobs/{job_id}", response_model=ExecutionJobResponse)
async def get_job(
    job_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    return await service.get_job(db, workspace_id, job_id)


@router.post("/jobs/{job_id}/cancel", response_model=ExecutionJobResponse)
async def cancel_job(
    job_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("job:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    row = await service.cancel_job(db, workspace_id, job_id)
    await db.commit()
    await db.refresh(row)
    return row


@router.post("/jobs/{job_id}/execute", response_model=ExecutionJobResponse)
async def execute_job(
    job_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("job:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    row = await service.execute_job(db, workspace_id, job_id)
    await db.commit()
    await db.refresh(row)
    return row


@router.post("/jobs/{job_id}/retry", response_model=ExecutionJobResponse)
async def retry_job(
    job_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("job:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    row = await service.retry_job(db, workspace_id, job_id)
    await db.commit()
    await db.refresh(row)
    return row
