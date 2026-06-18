"""Content schedule API router."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.auth.jwt import AuthContext
from exposureflow_api.auth.permissions import require_permission
from exposureflow_api.content import schedule_service
from exposureflow_api.content.schedule_schemas import (
    BatchGenerateRequest,
    BatchGenerateResponse,
    ContentScheduleCreate,
    ContentScheduleResponse,
    ContentScheduleUpdate,
)
from exposureflow_api.database import get_db
from exposureflow_api.exposure.deps import get_site_in_workspace

router = APIRouter(prefix="/api/v1/content/schedule", tags=["content-schedule"])


@router.get("/{site_id}", response_model=ContentScheduleResponse | None)
async def get_schedule(
    site_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    row = await schedule_service.get_schedule(db, workspace_id, site_id)
    return row


@router.put("/{site_id}", response_model=ContentScheduleResponse)
async def upsert_schedule(
    site_id: UUID,
    body: ContentScheduleCreate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    row = await schedule_service.upsert_schedule(
        db,
        workspace_id,
        site_id=site_id,
        enabled=body.enabled,
        articles_per_week=body.articles_per_week,
        priority_filter=body.priority_filter,
        schedule_days_json=body.schedule_days_json,
        auto_approve_threshold=body.auto_approve_threshold,
    )
    await db.commit()
    await db.refresh(row)
    return row


@router.patch("/{site_id}", response_model=ContentScheduleResponse)
async def update_schedule(
    site_id: UUID,
    body: ContentScheduleUpdate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    row = await schedule_service.update_schedule(db, workspace_id, site_id, **body.model_dump(exclude_none=True))
    await db.commit()
    await db.refresh(row)
    return row


@router.post("/batch-generate", response_model=BatchGenerateResponse)
async def batch_generate(
    body: BatchGenerateRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("job:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, body.site_id)
    triggered, skipped, run_ids = await schedule_service.trigger_batch_generation(
        db,
        workspace_id,
        site_id=body.site_id,
        count=body.count,
        priority_filter=body.priority_filter,
    )
    await db.commit()
    return BatchGenerateResponse(
        triggered=triggered,
        skipped=skipped,
        run_ids=run_ids,
        message=f"已觸發 {triggered} 篇內容生成，{skipped} 篇跳過",
    )
