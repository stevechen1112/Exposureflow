from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.auth.jwt import AuthContext
from exposureflow_api.auth.permissions import require_permission
from exposureflow_api.database import get_db
from exposureflow_api.exposure import service
from exposureflow_api.exposure.deps import get_site_in_workspace
from exposureflow_api.exposure.owner_classification import (
    classify_url_owner,
    load_competitor_domains,
)
from exposureflow_api.exposure.schemas import (
    DashboardResponse,
    ExposureAssetResponse,
    MergeAssetsRequest,
    OpportunityResponse,
)
from exposureflow_api.models import ExposureAsset, ExposureOpportunity

router = APIRouter(prefix="/api/v1/exposure", tags=["exposure"])


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    site_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    from exposureflow_api.exposure.dashboard import build_dashboard_metrics

    return await build_dashboard_metrics(db, workspace_id, site_id)


@router.post("/sites/{site_id}/assets/import-gsc")
async def import_gsc_assets(
    site_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("integration:write")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    count = await service.import_assets_from_gsc(db, workspace_id, site_id)
    await db.commit()
    return {"assets_upserted": count}


@router.get("/sites/{site_id}/assets", response_model=list[ExposureAssetResponse])
async def list_assets(
    site_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
) -> list[ExposureAsset]:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    result = await db.execute(
        select(ExposureAsset).where(
            ExposureAsset.workspace_id == workspace_id,
            ExposureAsset.site_id == site_id,
            ExposureAsset.status != "merged",
        )
    )
    return list(result.scalars().all())


@router.post("/sites/{site_id}/assets/merge", response_model=ExposureAssetResponse)
async def merge_assets(
    site_id: UUID,
    body: MergeAssetsRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
) -> ExposureAsset:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    canonical = await service.merge_duplicate_assets(
        db, workspace_id, site_id, body.canonical_asset_id, body.duplicate_asset_ids
    )
    await db.commit()
    await db.refresh(canonical)
    return canonical


@router.post("/sites/{site_id}/opportunities/generate")
async def generate_opportunities(
    site_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("job:write")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    count = await service.generate_opportunities_from_gsc(db, workspace_id, site_id)
    await db.commit()
    return {"opportunities_created": count}


@router.get("/sites/{site_id}/opportunities", response_model=list[OpportunityResponse])
async def list_opportunities(
    site_id: UUID,
    limit: int = Query(default=100, le=500),
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
) -> list[ExposureOpportunity]:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    result = await db.execute(
        select(ExposureOpportunity)
        .where(
            ExposureOpportunity.workspace_id == workspace_id,
            ExposureOpportunity.site_id == site_id,
        )
        .order_by(ExposureOpportunity.total_opportunity_score.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


@router.post("/sites/{site_id}/classify-url")
async def classify_url(
    site_id: UUID,
    url: str = Query(...),
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    _user, _membership, workspace_id = ctx
    site = await get_site_in_workspace(db, workspace_id, site_id)
    competitors = await load_competitor_domains(db, workspace_id, site_id)
    result = classify_url_owner(url, site_domain=site.domain, competitor_domains=competitors)
    return {
        "owner_type": result.owner_type,
        "domain": result.domain,
        "is_own": result.is_own,
        "is_competitor": result.is_competitor,
        "is_third_party": result.is_third_party,
    }
