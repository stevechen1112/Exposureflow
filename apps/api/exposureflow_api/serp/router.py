from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.auth.jwt import AuthContext
from exposureflow_api.auth.permissions import require_permission
from exposureflow_api.common.errors import not_found
from exposureflow_api.database import get_db
from exposureflow_api.exposure.deps import get_site_in_workspace
from exposureflow_api.jobs.service import enqueue_job
from exposureflow_api.models import SerpQuerySnapshot, SerpSlotTarget
from exposureflow_api.serp import service
from exposureflow_api.serp.schemas import (
    SerpSlotTargetResponse,
    SerpSlotTargetUpdate,
    SerpSnapshotListItem,
    SerpSnapshotRunRequest,
)

router = APIRouter(prefix="/api/v1/serp", tags=["serp"])


@router.get("/snapshots", response_model=list[SerpSnapshotListItem])
async def list_snapshots(
    site_id: UUID,
    keyword: str | None = None,
    limit: int = Query(default=50, le=200),
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("integration:read")),
    db: AsyncSession = Depends(get_db),
) -> list[SerpQuerySnapshot]:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    stmt = (
        select(SerpQuerySnapshot)
        .where(
            SerpQuerySnapshot.workspace_id == workspace_id,
            SerpQuerySnapshot.site_id == site_id,
        )
        .order_by(SerpQuerySnapshot.captured_at.desc())
        .limit(limit)
    )
    if keyword:
        stmt = stmt.where(SerpQuerySnapshot.keyword.ilike(f"%{keyword}%"))
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("/snapshots/run")
async def run_snapshot(
    body: SerpSnapshotRunRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("job:write")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, body.site_id)
    run = await enqueue_job(
        db,
        workspace_id=workspace_id,
        job_type="serp.snapshot",
        site_id=body.site_id,
        input_json={
            "keyword": body.keyword,
            "country": body.country,
            "language": body.language,
            "device": body.device,
        },
    )
    await db.commit()
    return {"job_run_id": str(run.id), "status": run.status}


@router.get("/matrix")
async def get_serp_matrix(
    site_id: UUID,
    cluster_id: UUID | None = None,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    return await service.build_site_matrix(
        db, workspace_id, site_id, cluster_id=cluster_id
    )


@router.get("/slot-targets", response_model=list[SerpSlotTargetResponse])
async def list_slot_targets(
    site_id: UUID,
    keyword: str | None = None,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
) -> list[SerpSlotTarget]:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    stmt = select(SerpSlotTarget).where(
        SerpSlotTarget.workspace_id == workspace_id,
        SerpSlotTarget.site_id == site_id,
    )
    if keyword:
        stmt = stmt.where(SerpSlotTarget.keyword.ilike(f"%{keyword}%"))
    result = await db.execute(stmt.order_by(SerpSlotTarget.keyword, SerpSlotTarget.slot_type))
    return list(result.scalars().all())


@router.patch("/slot-targets/{target_id}", response_model=SerpSlotTargetResponse)
async def update_slot_target(
    target_id: UUID,
    body: SerpSlotTargetUpdate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
) -> SerpSlotTarget:
    _user, _membership, workspace_id = ctx
    target = await db.get(SerpSlotTarget, target_id)
    if target is None or target.workspace_id != workspace_id:
        raise not_found("SERP slot target")
    await get_site_in_workspace(db, workspace_id, target.site_id)
    if body.target_status is not None:
        target.target_status = body.target_status
    await db.commit()
    await db.refresh(target)
    return target


@router.post("/opportunities/generate")
async def generate_serp_opportunities(
    site_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("job:write")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    count = await service.generate_serp_opportunities(db, workspace_id, site_id)
    await db.commit()
    return {"opportunities_created": count}
