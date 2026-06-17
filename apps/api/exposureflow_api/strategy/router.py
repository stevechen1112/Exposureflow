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
    BusinessConstraintRuleResponse,
    BusinessIntakeCreate,
    BusinessIntakeApproveResponse,
    BusinessIntakeResponse,
    BusinessIntakeUpdate,
    ColdStartResearchRequest,
    DeliveryCommitmentCreate,
    DeliveryCommitmentResponse,
    DeliveryCommitmentUpdate,
    KeywordPyramidBulkImportRequest,
    KeywordPyramidBulkImportResponse,
    KeywordPyramidNodeCreate,
    KeywordPyramidNodeResponse,
    KeywordPyramidNodeUpdate,
    KeywordScoreBatchRequest,
    KeywordScoreBatchResponse,
    KeywordScoreRequest,
    KeywordScoreResponse,
    KeywordScoreFactorResponse,
    PyramidTopicBridgeResponse,
    ProductServiceScopeCreate,
    ProductServiceScopeResponse,
    ProductServiceScopeUpdate,
    SerpEnrichmentRequest,
    SerpEnrichmentResponse,
    SiteKeywordScoreRequest,
    SiteKeywordScoreResponse,
    StrategyImpactApplyResponse,
    StrategyImpactPreviewResponse,
)

router = APIRouter(prefix="/api/v1/strategy", tags=["strategy"])


@router.post("/intakes/current/reapply", response_model=BusinessIntakeApproveResponse)
async def reapply_current_intake(
    site_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
):
    user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    row, impact = await service.reapply_current_intake(db, workspace_id, site_id, user.user_id)
    await db.commit()
    await db.refresh(row)
    return BusinessIntakeApproveResponse(
        intake=BusinessIntakeResponse.model_validate(row),
        impact=StrategyImpactApplyResponse(**impact),
    )


@router.get("/intakes/current", response_model=BusinessIntakeResponse | None)
async def get_current_intake(
    site_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    return await service.get_current_intake(db, workspace_id, site_id)


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


@router.post("/intakes/{intake_id}/fork", response_model=BusinessIntakeResponse)
async def fork_intake(
    intake_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    parent = await service.get_intake(db, workspace_id, intake_id)
    row = await service.fork_intake(db, workspace_id, parent.site_id, parent)
    await db.commit()
    await db.refresh(row)
    return row


@router.get("/intakes/{intake_id}/impact-preview", response_model=StrategyImpactPreviewResponse)
async def preview_intake_impact(
    intake_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    preview = await service.preview_intake(db, workspace_id, intake_id)
    return StrategyImpactPreviewResponse(**preview)


@router.post("/intakes/{intake_id}/approve", response_model=BusinessIntakeApproveResponse)
async def approve_intake(
    intake_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
):
    user, _membership, workspace_id = ctx
    row, impact = await service.approve_intake(db, workspace_id, intake_id, user.user_id)
    await db.commit()
    await db.refresh(row)
    return BusinessIntakeApproveResponse(
        intake=BusinessIntakeResponse.model_validate(row),
        impact=StrategyImpactApplyResponse(**impact),
    )


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


@router.get("/constraint-rules", response_model=list[BusinessConstraintRuleResponse])
async def list_constraint_rules(
    site_id: UUID,
    active_only: bool = True,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    return await service.list_constraint_rules(
        db, workspace_id, site_id, active_only=active_only
    )


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


@router.post("/keyword-pyramid/bulk-import", response_model=KeywordPyramidBulkImportResponse)
async def bulk_import_keyword_pyramid(
    body: KeywordPyramidBulkImportRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, body.site_id)
    result = await service.bulk_import_keyword_nodes(
        db,
        workspace_id,
        body.site_id,
        [row.model_dump() for row in body.rows],
        created_by=body.created_by,
    )
    await db.commit()
    return KeywordPyramidBulkImportResponse(
        created=int(result["created"]),
        skipped=int(result["skipped"]),
        errors=list(result["errors"]),
    )


@router.post("/keyword-pyramid/sync-topic-bridge", response_model=PyramidTopicBridgeResponse)
async def sync_keyword_pyramid_topic_bridge(
    site_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    stats = await service.sync_pyramid_topic_bridge(db, workspace_id, site_id)
    await db.commit()
    return PyramidTopicBridgeResponse(linked=stats["linked"], skipped=stats["skipped"])


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


@router.delete("/keyword-pyramid/{node_id}", status_code=204)
async def delete_keyword_node(
    node_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
):
    user, _membership, workspace_id = ctx
    await service.delete_keyword_node(db, workspace_id, node_id, user.user_id)
    await db.commit()


@router.post("/keyword-pyramid/{node_id}/approve", response_model=KeywordPyramidNodeResponse)
async def approve_keyword_node(
    node_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
):
    user, _membership, workspace_id = ctx
    row = await service.approve_keyword_node(db, workspace_id, node_id, user.user_id)
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


@router.post(
    "/delivery-commitments/{commitment_id}/deactivate",
    response_model=DeliveryCommitmentResponse,
)
async def deactivate_delivery_commitment(
    commitment_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    row = await service.deactivate_delivery_commitment(db, workspace_id, commitment_id)
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
            "include_paa": body.include_paa,
            "include_related": body.include_related,
            "max_expansions": body.max_expansions,
            "max_seeds": body.max_seeds,
        },
    )
    await db.commit()
    return {"job_id": str(job_run.id), "status": "queued"}


# ── Keyword Scoring & SERP Enrichment endpoints ──────────────────────────

from exposureflow_api.strategy.keyword_scorer import (
    KeywordScoreInput,
    score_keyword,
    score_keywords_batch,
)
from exposureflow_api.strategy.serp_enrichment_bridge import (
    batch_enrich_site_keywords,
    build_keyword_score_input,
    score_site_keywords,
)


@router.post("/keyword-pyramid/score", response_model=KeywordScoreResponse)
async def score_single_keyword(
    body: KeywordScoreRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
):
    """Score a single keyword using the five-factor exposure opportunity model."""
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, body.site_id)

    inp = KeywordScoreInput(
        keyword=body.keyword,
        node_type=body.node_type,
        intent=body.intent,
        estimated_monthly_searches=body.estimated_monthly_searches,
        volume_source=body.volume_source,
        competitor_domain_count=body.competitor_domain_count,
        avg_competitor_da=body.avg_competitor_da,
        top10_has_strong_domains=body.top10_has_strong_domains,
        serp_features_present=body.serp_features_present,
        ai_overview_present=body.ai_overview_present,
        ai_citation_signals=body.ai_citation_signals,
        topic_cluster_id=body.topic_cluster_id,
        topic_cluster_coverage=body.topic_cluster_coverage,
        pillar_has_page=body.pillar_has_page,
        gsc_impressions_28d=body.gsc_impressions_28d,
        gsc_clicks_28d=body.gsc_clicks_28d,
        gsc_avg_position=body.gsc_avg_position,
        business_fit_status=body.business_fit_status,
        is_approved=body.is_approved,
    )
    result = score_keyword(inp)
    return KeywordScoreResponse(
        keyword=result.keyword,
        total_score=result.total_score,
        factors=KeywordScoreFactorResponse(
            volume_score=result.volume_score,
            feasibility_score=result.feasibility_score,
            serp_diversity_score=result.serp_diversity_score,
            ai_citation_score=result.ai_citation_score,
            topic_contribution_score=result.topic_contribution_score,
        ),
        priority_tier=result.priority_tier,
        priority_label=result.priority_label,
        evidence=result.evidence,
    )


@router.post("/keyword-pyramid/score-batch", response_model=KeywordScoreBatchResponse)
async def score_keywords_batch_endpoint(
    body: KeywordScoreBatchRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
):
    """Score multiple keywords using the five-factor model."""
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, body.site_id)

    inputs = [
        KeywordScoreInput(
            keyword=k.keyword,
            node_type=k.node_type,
            intent=k.intent,
            estimated_monthly_searches=k.estimated_monthly_searches,
            volume_source=k.volume_source,
            competitor_domain_count=k.competitor_domain_count,
            avg_competitor_da=k.avg_competitor_da,
            top10_has_strong_domains=k.top10_has_strong_domains,
            serp_features_present=k.serp_features_present,
            ai_overview_present=k.ai_overview_present,
            ai_citation_signals=k.ai_citation_signals,
            topic_cluster_id=k.topic_cluster_id,
            topic_cluster_coverage=k.topic_cluster_coverage,
            pillar_has_page=k.pillar_has_page,
            gsc_impressions_28d=k.gsc_impressions_28d,
            gsc_clicks_28d=k.gsc_clicks_28d,
            gsc_avg_position=k.gsc_avg_position,
            business_fit_status=k.business_fit_status,
            is_approved=k.is_approved,
        )
        for k in body.keywords
    ]
    results = score_keywords_batch(inputs)
    return KeywordScoreBatchResponse(
        results=[
            KeywordScoreResponse(
                keyword=r.keyword,
                total_score=r.total_score,
                factors=KeywordScoreFactorResponse(
                    volume_score=r.volume_score,
                    feasibility_score=r.feasibility_score,
                    serp_diversity_score=r.serp_diversity_score,
                    ai_citation_score=r.ai_citation_score,
                    topic_contribution_score=r.topic_contribution_score,
                ),
                priority_tier=r.priority_tier,
                priority_label=r.priority_label,
                evidence=r.evidence,
            )
            for r in results
        ],
        scored_count=len(results),
    )


@router.post("/keyword-pyramid/enrich-from-serp", response_model=SerpEnrichmentResponse)
async def enrich_keywords_from_serp(
    body: SerpEnrichmentRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
):
    """Enrich all in-scope keywords with SERP data (volume, competition, features)."""
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, body.site_id)

    nodes = await batch_enrich_site_keywords(
        db, workspace_id, body.site_id, only_in_scope=body.only_in_scope
    )
    await db.commit()

    with_serp = sum(
        1 for n in nodes
        if (n.evidence_json or {}).get("enrichment", {}).get("serp_enrichment", {}).get("status") == "enriched"
    )
    return SerpEnrichmentResponse(
        enriched_count=len(nodes),
        total_keywords=len(nodes),
        keywords_with_serp_data=with_serp,
        keywords_without_serp_data=len(nodes) - with_serp,
    )


@router.post("/keyword-pyramid/score-site", response_model=SiteKeywordScoreResponse)
async def score_site_keywords_endpoint(
    body: SiteKeywordScoreRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
):
    """Score all keywords for a site with automatic SERP enrichment."""
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, body.site_id)

    results = await score_site_keywords(
        db, workspace_id, body.site_id, only_in_scope=body.only_in_scope
    )

    p1 = sum(1 for r in results if r.priority_tier == "P1")
    p2 = sum(1 for r in results if r.priority_tier == "P2")
    p3 = sum(1 for r in results if r.priority_tier == "P3")

    return SiteKeywordScoreResponse(
        results=[
            KeywordScoreResponse(
                keyword=r.keyword,
                total_score=r.total_score,
                factors=KeywordScoreFactorResponse(
                    volume_score=r.volume_score,
                    feasibility_score=r.feasibility_score,
                    serp_diversity_score=r.serp_diversity_score,
                    ai_citation_score=r.ai_citation_score,
                    topic_contribution_score=r.topic_contribution_score,
                ),
                priority_tier=r.priority_tier,
                priority_label=r.priority_label,
                evidence=r.evidence,
            )
            for r in results
        ],
        scored_count=len(results),
        p1_count=p1,
        p2_count=p2,
        p3_count=p3,
    )
