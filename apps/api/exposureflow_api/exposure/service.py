"""Exposure asset and opportunity services."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.common.errors import not_found
from exposureflow_api.exposure.scorer import ScoreInput, score_opportunity
from exposureflow_api.models import (
    ExposureAsset,
    ExposureOpportunity,
    GscPerformanceRow,
    TechnicalIssue,
)
from exposureflow_api.models.strategy import KeywordPyramidNode
from exposureflow_api.strategy.business_fit import evaluate_site_keyword_fit


async def import_assets_from_gsc(
    db: AsyncSession, workspace_id: UUID, site_id: UUID
) -> int:
    result = await db.execute(
        select(
            GscPerformanceRow.page,
            func.sum(GscPerformanceRow.impressions).label("impressions"),
            func.sum(GscPerformanceRow.clicks).label("clicks"),
        )
        .where(
            GscPerformanceRow.workspace_id == workspace_id,
            GscPerformanceRow.site_id == site_id,
        )
        .group_by(GscPerformanceRow.page)
    )
    rows = result.all()
    count = 0
    for page, impressions, clicks in rows:
        stmt = insert(ExposureAsset).values(
            workspace_id=workspace_id,
            site_id=site_id,
            asset_type="page",
            url=page,
            status="candidate",
            total_impressions=int(impressions or 0),
            total_clicks=int(clicks or 0),
            metadata_json={"source": "gsc"},
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_exposure_asset_url",
            set_={
                "total_impressions": stmt.excluded.total_impressions,
                "total_clicks": stmt.excluded.total_clicks,
                "updated_at": datetime.now(UTC),
            },
        )
        await db.execute(stmt)
        count += 1
    await db.flush()
    return count


async def merge_duplicate_assets(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
    canonical_asset_id: UUID,
    duplicate_asset_ids: list[UUID],
) -> ExposureAsset:
    canonical = await db.get(ExposureAsset, canonical_asset_id)
    if (
        canonical is None
        or canonical.workspace_id != workspace_id
        or canonical.site_id != site_id
    ):
        raise not_found("Canonical asset")

    for dup_id in duplicate_asset_ids:
        if dup_id == canonical_asset_id:
            continue
        dup = await db.get(ExposureAsset, dup_id)
        if (
            dup is None
            or dup.workspace_id != workspace_id
            or dup.site_id != site_id
        ):
            raise not_found("Duplicate asset")
        canonical.total_impressions += dup.total_impressions
        canonical.total_clicks += dup.total_clicks
        dup.status = "merged"
        dup.metadata_json = {**dup.metadata_json, "merged_into": str(canonical_asset_id)}
    await db.flush()
    return canonical


async def _site_p95_impressions(db: AsyncSession, workspace_id: UUID, site_id: UUID) -> int:
    subq = (
        select(
            GscPerformanceRow.query,
            func.sum(GscPerformanceRow.impressions).label("imp"),
        )
        .where(
            GscPerformanceRow.workspace_id == workspace_id,
            GscPerformanceRow.site_id == site_id,
        )
        .group_by(GscPerformanceRow.query)
        .subquery()
    )
    result = await db.execute(
        select(func.percentile_cont(0.95).within_group(subq.c.imp))
    )
    value = result.scalar_one_or_none()
    return int(value or 1)


async def _existing_opportunity_keys(
    db: AsyncSession, workspace_id: UUID, site_id: UUID
) -> set[tuple[str, str | None, str | None]]:
    result = await db.execute(
        select(
            ExposureOpportunity.keyword,
            ExposureOpportunity.current_url,
            ExposureOpportunity.evidence_json,
        ).where(
            ExposureOpportunity.workspace_id == workspace_id,
            ExposureOpportunity.site_id == site_id,
            ExposureOpportunity.status == "open",
        )
    )
    keys: set[tuple[str, str | None, str | None]] = set()
    for keyword, current_url, evidence in result.all():
        rule_id = (evidence or {}).get("rule_id", "")
        keys.add((rule_id, keyword, current_url))
    return keys


async def generate_opportunities_from_gsc(
    db: AsyncSession, workspace_id: UUID, site_id: UUID
) -> int:
    p95 = await _site_p95_impressions(db, workspace_id, site_id)
    agg = await db.execute(
        select(
            GscPerformanceRow.query,
            GscPerformanceRow.page,
            func.sum(GscPerformanceRow.impressions).label("impressions"),
            func.avg(GscPerformanceRow.position).label("position"),
        )
        .where(
            GscPerformanceRow.workspace_id == workspace_id,
            GscPerformanceRow.site_id == site_id,
        )
        .group_by(GscPerformanceRow.query, GscPerformanceRow.page)
    )
    rows = agg.all()
    query_impressions: dict[str, int] = defaultdict(int)
    for query, _page, impressions, _pos in rows:
        query_impressions[query] += int(impressions or 0)
    if not query_impressions:
        return 0
    sorted_imps = sorted(query_impressions.values())
    p75 = sorted_imps[int(len(sorted_imps) * 0.75)] if sorted_imps else 0

    seen = await _existing_opportunity_keys(db, workspace_id, site_id)
    created = 0

    def _track(rule_id: str, keyword: str | None, current_url: str | None) -> bool:
        key = (rule_id, keyword, current_url)
        if key in seen:
            return False
        seen.add(key)
        return True

    # OG-001: query-level impressions above P75, page position 11-30
    for query, page, impressions, position in rows:
        query_imp = query_impressions[query]
        pos = float(position or 0)
        if query_imp >= p75 and 11 <= pos <= 30:
            fit = await evaluate_site_keyword_fit(db, workspace_id, site_id, query)
            if fit.blocked:
                continue
            if not _track("OG-001", query, page):
                continue
            score = score_opportunity(
                ScoreInput(
                    query_impressions_28d=query_imp,
                    site_p95_query_impressions=p95,
                    current_position=pos,
                    targetable_slot_count=1,
                    business_fit_score=fit.business_fit_score,
                )
            )
            db.add(
                _build_opportunity(
                    workspace_id,
                    site_id,
                    opportunity_type="refresh_page",
                    keyword=query,
                    current_url=page,
                    impressions=query_imp,
                    position=pos,
                    reason="OG-001: High impressions with avg position 11-30",
                    rule_id="OG-001",
                    score=score,
                )
            )
            created += 1

    # OG-004: same query multiple URLs
    by_query: dict[str, list] = defaultdict(list)
    for query, page, impressions, position in rows:
        by_query[query].append((page, impressions, position))
    for query, pages in by_query.items():
        unique_pages = {p[0] for p in pages}
        if len(unique_pages) >= 2:
            fit = await evaluate_site_keyword_fit(db, workspace_id, site_id, query)
            if fit.blocked:
                continue
            if not _track("OG-004", query, None):
                continue
            top = max(pages, key=lambda x: int(x[1] or 0))
            score = score_opportunity(
                ScoreInput(
                    query_impressions_28d=int(query_impressions[query]),
                    site_p95_query_impressions=p95,
                    current_position=float(top[2] or 0),
                    targetable_slot_count=1,
                    execution_confidence=0.7,
                    business_fit_score=fit.business_fit_score,
                )
            )
            db.add(
                _build_opportunity(
                    workspace_id,
                    site_id,
                    opportunity_type="merge_pages",
                    keyword=query,
                    current_url=top[0],
                    impressions=int(query_impressions[query]),
                    position=float(top[2] or 0),
                    reason="OG-004: Multiple URLs competing for same query",
                    rule_id="OG-004",
                    score=score,
                    extra_evidence={"urls": list(unique_pages)},
                )
            )
            created += 1

    # OG-005: technical issues on URLs with impressions
    tech = await db.execute(
        select(TechnicalIssue).where(
            TechnicalIssue.workspace_id == workspace_id,
            TechnicalIssue.site_id == site_id,
            TechnicalIssue.status == "open",
            TechnicalIssue.issue_type.in_(
                ["noindex", "canonical_mismatch", "robots_blocked"]
            ),
        )
    )
    for issue in tech.scalars().all():
        if not issue.url:
            continue
        if not _track("OG-005", None, issue.url):
            continue
        score = score_opportunity(
            ScoreInput(
                query_impressions_28d=1,
                site_p95_query_impressions=p95,
                current_position=None,
                targetable_slot_count=1,
                execution_confidence=0.9,
            )
        )
        opp = _build_opportunity(
            workspace_id,
            site_id,
            opportunity_type="technical_fix",
            keyword=None,
            current_url=issue.url,
            impressions=0,
            position=None,
            reason=f"OG-005: {issue.issue_type} — {issue.description}",
            rule_id="OG-005",
            score=score,
            extra_evidence={"technical_issue_id": str(issue.id)},
        )
        opp.priority = "critical"
        db.add(opp)
        created += 1

    await db.flush()
    return created


async def generate_opportunities_from_pyramid(
    db: AsyncSession, workspace_id: UUID, site_id: UUID
) -> int:
    """OG-016: Approved high-priority pyramid nodes without GSC coverage."""
    result = await db.execute(
        select(KeywordPyramidNode).where(
            KeywordPyramidNode.workspace_id == workspace_id,
            KeywordPyramidNode.site_id == site_id,
            KeywordPyramidNode.business_fit_status == "in_scope",
            KeywordPyramidNode.approved_at.is_not(None),
            KeywordPyramidNode.priority >= 4,
        )
    )
    nodes = list(result.scalars().all())
    if not nodes:
        return 0

    seen = await _existing_opportunity_keys(db, workspace_id, site_id)
    created = 0
    for node in nodes:
        enrichment = (node.evidence_json or {}).get("enrichment") or {}
        slot_count = int(enrichment.get("targetable_slot_count") or 1)
        rule_id = "OG-016"
        key = (rule_id, node.keyword, None)
        if key in seen:
            continue
        seen.add(key)
        score = score_opportunity(
            ScoreInput(
                query_impressions_28d=0,
                site_p95_query_impressions=1,
                current_position=None,
                targetable_slot_count=slot_count,
                business_priority=node.priority,
                business_fit_score=1.0,
                execution_confidence=0.6,
            )
        )
        db.add(
            _build_opportunity(
                workspace_id,
                site_id,
                opportunity_type="create_page",
                keyword=node.keyword,
                current_url=None,
                impressions=0,
                position=None,
                reason="OG-016: Approved pyramid topic without GSC coverage",
                rule_id=rule_id,
                score=score,
                extra_evidence={
                    "pyramid_node_id": str(node.id),
                    "node_type": node.node_type,
                },
            )
        )
        created += 1
    await db.flush()
    return created


def _build_opportunity(
    workspace_id: UUID,
    site_id: UUID,
    *,
    opportunity_type: str,
    keyword: str | None,
    current_url: str | None,
    impressions: int,
    position: float | None,
    reason: str,
    rule_id: str,
    score,
    extra_evidence: dict | None = None,
) -> ExposureOpportunity:
    evidence = score.evidence
    evidence["rule_id"] = rule_id
    if extra_evidence:
        evidence.update(extra_evidence)
    subs = score.subscores
    return ExposureOpportunity(
        workspace_id=workspace_id,
        site_id=site_id,
        opportunity_type=opportunity_type,
        keyword=keyword,
        current_url=current_url,
        current_impressions=impressions,
        current_position=position,
        ranking_feasibility_score=subs["ranking_feasibility_score"],
        serp_slot_score=subs["serp_slot_score"],
        ai_citation_score=subs["ai_citation_score"],
        topic_contribution_score=subs["topic_contribution_score"],
        zero_click_value_score=subs["zero_click_value_score"],
        total_opportunity_score=score.total_opportunity_score,
        priority=score.priority,
        status="open",
        reason=reason,
        evidence_json=evidence,
    )
