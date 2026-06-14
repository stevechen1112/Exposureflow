"""Grounded content brief builder."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.common.errors import not_found
from exposureflow_api.knowledge.service import get_brand_profile
from exposureflow_api.models.execution_content import ContentBrief, ContentSourcePack
from exposureflow_api.models.exposure import ExposureOpportunity
from exposureflow_api.strategy.business_fit import evaluate_site_keyword_fit

BRIEF_TYPE_MAP = {
    "create_page": "article",
    "solution_page": "solution_page",
    "refresh_page": "refresh",
    "enrich": "enrich",
    "add_faq": "faq",
}


async def build_content_brief(
    db: AsyncSession,
    *,
    workspace_id: UUID,
    site_id: UUID,
    opportunity_id: UUID,
    source_pack_id: UUID,
    decision_id: UUID | None = None,
) -> ContentBrief:
    opp = await db.get(ExposureOpportunity, opportunity_id)
    if opp is None or opp.workspace_id != workspace_id or opp.site_id != site_id:
        raise not_found("Exposure opportunity")

    pack = await db.get(ContentSourcePack, source_pack_id)
    if pack is None or pack.workspace_id != workspace_id:
        raise not_found("Content source pack")
    if pack.status == "needs_human_evidence":
        raise not_found("Content source pack")

    fit = await evaluate_site_keyword_fit(db, workspace_id, site_id, opp.keyword)
    if pack.site_id != site_id:
        raise not_found("Content source pack")
    if fit.blocked or fit.business_fit_status != "in_scope":
        raise not_found("Exposure opportunity")

    brand = await get_brand_profile(db, workspace_id, site_id)
    brief_type = BRIEF_TYPE_MAP.get(opp.opportunity_type, "article")
    forbidden_claims: list[str] = []
    review_policy = "editor_review"
    if brand:
        forbidden_claims = list(brand.compliance_policy_json.get("forbidden_claims", []))
        review_policy = brand.default_review_policy

    required_slots = [
        {"slot": "product_or_solution", "min_refs": 1},
        {"slot": "market_context", "min_refs": 0},
    ]
    if brief_type in ("comparison", "case_study"):
        required_slots.append({"slot": "proof_point", "min_refs": 1})

    brief_json = {
        "title_hint": opp.keyword or opp.reason,
        "opportunity_type": opp.opportunity_type,
        "search_context": opp.search_context or {},
        "target_url": opp.target_url,
        "current_url": opp.current_url,
        "business_fit": fit.evidence,
        "source_pack_coverage": float(pack.coverage_score),
        "review_policy": review_policy,
    }

    row = ContentBrief(
        workspace_id=workspace_id,
        site_id=site_id,
        opportunity_id=opportunity_id,
        decision_id=decision_id,
        source_pack_id=source_pack_id,
        brief_type=brief_type,
        market=pack.market,
        language=pack.language,
        target_persona=None,
        buyer_stage=None,
        required_evidence_slots_json=required_slots,
        forbidden_claims_json=forbidden_claims,
        brief_json=brief_json,
        status="ready",
    )
    db.add(row)
    await db.flush()
    return row
