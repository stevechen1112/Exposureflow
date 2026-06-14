from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.auth.jwt import AuthContext
from exposureflow_api.auth.permissions import require_permission
from exposureflow_api.common.errors import APIError
from exposureflow_api.database import get_db
from exposureflow_api.exposure.deps import get_site_in_workspace
from exposureflow_api.knowledge import service
from exposureflow_api.knowledge.schemas import (
    BrandProfileResponse,
    BrandProfileUpdate,
    KnowledgeFactCreate,
    KnowledgeFactResponse,
    KnowledgeFactUpdate,
    KnowledgeSourceCreate,
    KnowledgeSourceResponse,
    KnowledgeSourceUpdate,
)

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


@router.get("/brand-profile", response_model=BrandProfileResponse | None)
async def get_brand_profile(
    site_id: UUID | None = None,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    if site_id:
        await get_site_in_workspace(db, workspace_id, site_id)
    return await service.get_brand_profile(db, workspace_id, site_id)


@router.patch("/brand-profile", response_model=BrandProfileResponse)
async def upsert_brand_profile(
    body: BrandProfileUpdate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
):
    user, _membership, workspace_id = ctx
    if body.site_id:
        await get_site_in_workspace(db, workspace_id, body.site_id)
    row = await service.upsert_brand_profile(
        db,
        workspace_id,
        site_id=body.site_id,
        owner_user_id=user.id,
        canonical_brand_name=body.canonical_brand_name,
        brand_voice_json=body.brand_voice_json,
        positioning_json=body.positioning_json,
        target_markets_json=body.target_markets_json,
        buyer_personas_json=body.buyer_personas_json,
        compliance_policy_json=body.compliance_policy_json,
        default_review_policy=body.default_review_policy,
    )
    await db.commit()
    await db.refresh(row)
    return row


@router.get("/sources", response_model=list[KnowledgeSourceResponse])
async def list_sources(
    site_id: UUID | None = None,
    status: str | None = None,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    if site_id:
        await get_site_in_workspace(db, workspace_id, site_id)
    return await service.list_sources(db, workspace_id, site_id, status=status)


@router.post("/sources", response_model=KnowledgeSourceResponse)
async def create_source(
    body: KnowledgeSourceCreate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
):
    user, _membership, workspace_id = ctx
    if body.site_id:
        await get_site_in_workspace(db, workspace_id, body.site_id)
    row = await service.create_source(
        db, workspace_id, owner_user_id=user.id, **body.model_dump()
    )
    await db.commit()
    await db.refresh(row)
    return row


@router.get("/sources/{source_id}", response_model=KnowledgeSourceResponse)
async def get_source(
    source_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    return await service.get_source(db, workspace_id, source_id)


@router.patch("/sources/{source_id}", response_model=KnowledgeSourceResponse)
async def update_source(
    source_id: UUID,
    body: KnowledgeSourceUpdate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    row = await service.update_source(
        db, workspace_id, source_id, body.model_dump(exclude_unset=True)
    )
    await db.commit()
    await db.refresh(row)
    return row


@router.post("/sources/{source_id}/approve", response_model=KnowledgeSourceResponse)
async def approve_source(
    source_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    row = await service.approve_source(db, workspace_id, source_id)
    await db.commit()
    await db.refresh(row)
    return row


@router.post("/sources/{source_id}/revoke", response_model=KnowledgeSourceResponse)
async def revoke_source(
    source_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    row = await service.revoke_source(db, workspace_id, source_id)
    await db.commit()
    await db.refresh(row)
    return row


@router.get("/facts", response_model=list[KnowledgeFactResponse])
async def list_facts(
    site_id: UUID | None = None,
    type: str | None = Query(default=None, alias="type"),
    status: str | None = None,
    market: str | None = None,
    language: str | None = None,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    if site_id:
        await get_site_in_workspace(db, workspace_id, site_id)
    return await service.list_facts(
        db,
        workspace_id,
        site_id,
        fact_type=type,
        status=status,
        market=market,
        language=language,
    )


@router.post("/facts", response_model=KnowledgeFactResponse)
async def create_fact(
    body: KnowledgeFactCreate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    if body.site_id:
        await get_site_in_workspace(db, workspace_id, body.site_id)
    source = await service.get_source(db, workspace_id, body.knowledge_source_id)
    if body.site_id and source.site_id and source.site_id != body.site_id:
        raise APIError(
            code="INVALID_FACT_SITE",
            message="Fact site_id must match knowledge source site.",
            status_code=400,
        )
    row = await service.create_fact(db, workspace_id, **body.model_dump())
    await db.commit()
    await db.refresh(row)
    return row


@router.patch("/facts/{fact_id}", response_model=KnowledgeFactResponse)
async def update_fact(
    fact_id: UUID,
    body: KnowledgeFactUpdate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    row = await service.update_fact(
        db, workspace_id, fact_id, body.model_dump(exclude_unset=True)
    )
    await db.commit()
    await db.refresh(row)
    return row
