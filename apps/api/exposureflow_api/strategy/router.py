from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.auth.jwt import AuthContext
from exposureflow_api.auth.permissions import require_permission
from exposureflow_api.database import get_db
from exposureflow_api.exposure.deps import get_site_in_workspace
from exposureflow_api.jobs.service import enqueue_job
from exposureflow_api.strategy import service
from exposureflow_api.strategy.schemas import (
    BusinessFitEvaluateRequest,
    BusinessFitEvaluateResponse,
    BusinessIntakeCreate,
    BusinessIntakeResponse,
    BusinessIntakeUpdate,
    ColdStartResearchRequest,
    DeliveryCommitmentCreate,
    DeliveryCommitmentResponse,
    DeliveryCommitmentUpdate,
    KeywordPyramidNodeCreate,
    KeywordPyramidNodeResponse,
    KeywordPyramidNodeUpdate,
    ProductServiceScopeCreate,
    ProductServiceScopeResponse,
    ProductServiceScopeUpdate,
)

router = APIRouter(prefix="/api/v1/strategy", tags=["strategy"])


@router.get("/intakes", response_model=list[BusinessIntakeResponse])
async def list_intakes(
    site_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    return await service.list_intakes(db, workspace_id, site_id)


@router.post("/intakes", response_model=BusinessIntakeResponse)
async def create_intake(
    body: BusinessIntakeCreate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, body.site_id)
    row = await service.create_intake(db, workspace_id, **body.model_dump())
    await db.commit()
    await db.refresh(row)
    return row


@router.get("/intakes/{intake_id}", response_model=BusinessIntakeResponse)
async def get_intake(
    intake_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    return await service.get_intake(db, workspace_id, intake_id)


@router.patch("/intakes/{intake_id}", response_model=BusinessIntakeResponse)
async def update_intake(
    intake_id: UUID,
    body: BusinessIntakeUpdate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    row = await service.update_intake(
        db, workspace_id, intake_id, body.model_dump(exclude_unset=True)
    )
    await db.commit()
    await db.refresh(row)
    return row


@router.post("/intakes/{intake_id}/approve", response_model=BusinessIntakeResponse)
async def approve_intake(
    intake_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
):
    user, _membership, workspace_id = ctx
    row = await service.approve_intake(db, workspace_id, intake_id, user.id)
    await db.commit()
    await db.refresh(row)
    return row


@router.get("/product-scopes", response_model=list[ProductServiceScopeResponse])
async def list_product_scopes(
    site_id: UUID,
    status: str | None = None,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    return await service.list_product_scopes(db, workspace_id, site_id, status=status)


@router.post("/product-scopes", response_model=ProductServiceScopeResponse)
async def create_product_scope(
    body: ProductServiceScopeCreate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, body.site_id)
    row = await service.create_product_scope(db, workspace_id, **body.model_dump())
    await db.commit()
    await db.refresh(row)
    return row


@router.patch("/product-scopes/{scope_id}", response_model=ProductServiceScopeResponse)
async def update_product_scope(
    scope_id: UUID,
    body: ProductServiceScopeUpdate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    row = await service.update_product_scope(
        db, workspace_id, scope_id, body.model_dump(exclude_unset=True)
    )
    await db.commit()
    await db.refresh(row)
    return row


@router.get("/keyword-pyramid", response_model=list[KeywordPyramidNodeResponse])
async def list_keyword_pyramid(
    site_id: UUID,
    status: str | None = None,
    market: str | None = None,
    language: str | None = None,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    return await service.list_keyword_pyramid(
        db, workspace_id, site_id, status=status, market=market, language=language
    )


@router.post("/keyword-pyramid", response_model=KeywordPyramidNodeResponse)
async def create_keyword_node(
    body: KeywordPyramidNodeCreate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, body.site_id)
    row = await service.create_keyword_node(db, workspace_id, **body.model_dump())
    await db.commit()
    await db.refresh(row)
    return row


@router.patch("/keyword-pyramid/{node_id}", response_model=KeywordPyramidNodeResponse)
async def update_keyword_node(
    node_id: UUID,
    body: KeywordPyramidNodeUpdate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    row = await service.update_keyword_node(
        db, workspace_id, node_id, body.model_dump(exclude_unset=True)
    )
    await db.commit()
    await db.refresh(row)
    return row


@router.post("/keyword-pyramid/{node_id}/approve", response_model=KeywordPyramidNodeResponse)
async def approve_keyword_node(
    node_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
):
    user, _membership, workspace_id = ctx
    row = await service.approve_keyword_node(db, workspace_id, node_id, user.id)
    await db.commit()
    await db.refresh(row)
    return row


@router.get("/delivery-commitments", response_model=list[DeliveryCommitmentResponse])
async def list_delivery_commitments(
    site_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    return await service.list_delivery_commitments(db, workspace_id, site_id)


@router.post("/delivery-commitments", response_model=DeliveryCommitmentResponse)
async def create_delivery_commitment(
    body: DeliveryCommitmentCreate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, body.site_id)
    row = await service.create_delivery_commitment(db, workspace_id, **body.model_dump())
    await db.commit()
    await db.refresh(row)
    return row


@router.patch(
    "/delivery-commitments/{commitment_id}",
    response_model=DeliveryCommitmentResponse,
)
async def update_delivery_commitment(
    commitment_id: UUID,
    body: DeliveryCommitmentUpdate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    row = await service.update_delivery_commitment(
        db, workspace_id, commitment_id, body.model_dump(exclude_unset=True)
    )
    await db.commit()
    await db.refresh(row)
    return row


@router.post("/business-fit/evaluate", response_model=BusinessFitEvaluateResponse)
async def evaluate_business_fit(
    body: BusinessFitEvaluateRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, body.site_id)
    result = await service.evaluate_business_fit(db, workspace_id, body.site_id, body.keyword)
    return BusinessFitEvaluateResponse(
        business_fit_score=result.business_fit_score,
        business_fit_status=result.business_fit_status,
        blocked=result.blocked,
        keyword_pyramid_node_id=UUID(result.keyword_pyramid_node_id)
        if result.keyword_pyramid_node_id
        else None,
        product_service_scope_id=UUID(result.product_service_scope_id)
        if result.product_service_scope_id
        else None,
        evidence=result.evidence,
    )


@router.post("/cold-start-research")
async def cold_start_research(
    body: ColdStartResearchRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("job:write")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, body.site_id)
    job_run = await enqueue_job(
        db,
        workspace_id=workspace_id,
        site_id=body.site_id,
        job_type="strategy.cold_start_research",
        input_json={
            "market": body.market,
            "language": body.language,
            "seed_keywords": body.seed_keywords,
        },
    )
    await db.commit()
    return {"job_id": str(job_run.id), "status": "queued"}
