"""Business Fit Gate — keyword / topic alignment with client scope."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.models.strategy import KeywordPyramidNode, ProductServiceScope

FIT_STATUS_SCORES: dict[str, float] = {
    "in_scope": 1.0,
    "needs_review": 0.5,
    "out_of_scope": 0.0,
    "blocked": 0.0,
}

SCOPE_STATUS_SCORES: dict[str, float] = {
    "active": 1.0,
    "planned": 0.8,
    "paused": 0.5,
    "out_of_scope": 0.0,
}

DEFAULT_NO_MATCH_SCORE = 0.5


def normalize_keyword(keyword: str | None) -> str:
    if not keyword:
        return ""
    return " ".join(keyword.strip().lower().split())


def score_from_fit_status(
    fit_status: str,
    *,
    scope_status: str | None = None,
    approved: bool = False,
) -> float:
    base = FIT_STATUS_SCORES.get(fit_status, DEFAULT_NO_MATCH_SCORE)
    if base == 0.0:
        return 0.0
    if scope_status:
        scope_factor = SCOPE_STATUS_SCORES.get(scope_status, 0.5)
        if scope_factor == 0.0:
            return 0.0
        base = min(base, scope_factor)
    if fit_status == "in_scope" and scope_status == "planned" and approved:
        return max(base, 0.8)
    if fit_status == "in_scope" and approved and scope_status == "active":
        return 1.0
    return base


@dataclass(frozen=True)
class BusinessFitResult:
    business_fit_score: float
    business_fit_status: str
    keyword_pyramid_node_id: str | None
    product_service_scope_id: str | None
    blocked: bool
    evidence: dict[str, Any]


def evaluate_keyword_fit(
    keyword: str | None,
    nodes_by_keyword: dict[str, KeywordPyramidNode],
    scopes_by_id: dict[UUID, ProductServiceScope],
) -> BusinessFitResult:
    normalized = normalize_keyword(keyword)
    if not normalized:
        return BusinessFitResult(
            business_fit_score=DEFAULT_NO_MATCH_SCORE,
            business_fit_status="needs_review",
            keyword_pyramid_node_id=None,
            product_service_scope_id=None,
            blocked=False,
            evidence={"reason": "no_keyword", "normalized_keyword": normalized},
        )

    node = nodes_by_keyword.get(normalized)
    if node is None:
        return BusinessFitResult(
            business_fit_score=DEFAULT_NO_MATCH_SCORE,
            business_fit_status="needs_review",
            keyword_pyramid_node_id=None,
            product_service_scope_id=None,
            blocked=False,
            evidence={
                "reason": "no_pyramid_match",
                "normalized_keyword": normalized,
            },
        )

    scope = scopes_by_id.get(node.product_service_scope_id) if node.product_service_scope_id else None
    scope_status = scope.status if scope else None
    approved = node.approved_at is not None
    score = score_from_fit_status(
        node.business_fit_status,
        scope_status=scope_status,
        approved=approved,
    )
    blocked = score == 0.0 or node.business_fit_status in ("out_of_scope", "blocked")
    return BusinessFitResult(
        business_fit_score=score,
        business_fit_status=node.business_fit_status,
        keyword_pyramid_node_id=str(node.id),
        product_service_scope_id=str(node.product_service_scope_id)
        if node.product_service_scope_id
        else None,
        blocked=blocked,
        evidence={
            "normalized_keyword": normalized,
            "keyword_pyramid_node_id": str(node.id),
            "business_fit_status": node.business_fit_status,
            "scope_status": scope_status,
            "approved": approved,
            "node_type": node.node_type,
            "priority": node.priority,
        },
    )


async def load_pyramid_index(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
) -> tuple[dict[str, KeywordPyramidNode], dict[UUID, ProductServiceScope]]:
    nodes_result = await db.execute(
        select(KeywordPyramidNode).where(
            KeywordPyramidNode.workspace_id == workspace_id,
            KeywordPyramidNode.site_id == site_id,
        )
    )
    nodes = list(nodes_result.scalars().all())
    nodes_by_keyword = {normalize_keyword(n.keyword): n for n in nodes if n.keyword}

    scope_ids = {n.product_service_scope_id for n in nodes if n.product_service_scope_id}
    scopes_by_id: dict[UUID, ProductServiceScope] = {}
    if scope_ids:
        scopes_result = await db.execute(
            select(ProductServiceScope).where(
                ProductServiceScope.workspace_id == workspace_id,
                ProductServiceScope.id.in_(scope_ids),
            )
        )
        scopes_by_id = {s.id: s for s in scopes_result.scalars().all()}
    return nodes_by_keyword, scopes_by_id


async def evaluate_site_keyword_fit(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
    keyword: str | None,
) -> BusinessFitResult:
    nodes_by_keyword, scopes_by_id = await load_pyramid_index(db, workspace_id, site_id)
    return evaluate_keyword_fit(keyword, nodes_by_keyword, scopes_by_id)
