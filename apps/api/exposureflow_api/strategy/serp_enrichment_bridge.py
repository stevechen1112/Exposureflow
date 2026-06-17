"""SERP enrichment bridge: connect SERP snapshots to keyword pyramid nodes.

This module bridges the gap between raw SERP data (serp_query_snapshots,
serp_slots) and the keyword pyramid scoring system.

Key functions:
- enrich_keyword_from_serp: pull SERP data into keyword evidence_json
- batch_enrich_site_keywords: enrich all in-scope keywords for a site
- build_keyword_score_input: assemble KeywordScoreInput from enriched data
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.models.ingestion import SerpQuerySnapshot, SerpSlot
from exposureflow_api.models.strategy import KeywordPyramidNode
from exposureflow_api.strategy.keyword_enrichment import merge_enrichment
from exposureflow_api.strategy.keyword_scorer import (
    KeywordScoreInput,
    KeywordScoreResult,
    estimate_search_volume_from_serp,
    estimate_competition_from_slots,
    extract_serp_features_from_slots,
    score_keyword,
    score_keywords_batch,
)


async def _get_latest_snapshot_for_keyword(
    db: AsyncSession,
    site_id: UUID,
    keyword: str,
) -> SerpQuerySnapshot | None:
    """Get the most recent SERP snapshot for a keyword."""
    result = await db.execute(
        select(SerpQuerySnapshot)
        .where(
            SerpQuerySnapshot.site_id == site_id,
            func.lower(SerpQuerySnapshot.keyword) == keyword.lower().strip(),
        )
        .order_by(SerpQuerySnapshot.captured_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _get_slots_for_snapshot(
    db: AsyncSession,
    snapshot_id: UUID,
) -> list[dict[str, Any]]:
    """Get all SERP slots for a snapshot as dicts."""
    result = await db.execute(
        select(SerpSlot).where(SerpSlot.snapshot_id == snapshot_id)
    )
    slots = result.scalars().all()
    return [
        {
            "slot_type": s.slot_type,
            "position": s.position,
            "owner_domain": s.owner_domain,
            "owner_brand": s.owner_brand,
            "url": s.url,
            "title": s.title,
            "snippet": s.snippet,
            "is_own_site": s.is_own_site,
            "is_competitor": s.is_competitor,
            "is_third_party": s.is_third_party,
        }
        for s in slots
    ]


async def enrich_keyword_from_serp(
    db: AsyncSession,
    node: KeywordPyramidNode,
) -> KeywordPyramidNode:
    """Enrich a single keyword pyramid node with SERP data.

    Pulls the latest SERP snapshot, extracts volume/competition/features,
    and writes enrichment into evidence_json.

    Returns the updated node (not yet flushed).
    """
    if not node.keyword:
        return node

    snapshot = await _get_latest_snapshot_for_keyword(db, node.site_id, node.keyword)
    if snapshot is None:
        # Mark as no SERP data available
        node.evidence_json = merge_enrichment(
            node.evidence_json,
            {"serp_enrichment": {"status": "no_data", "last_checked": None}},
        )
        return node

    slots = await _get_slots_for_snapshot(db, snapshot.id)
    raw_json = snapshot.raw_json or {}

    # Extract metrics
    volume_estimate = estimate_search_volume_from_serp(raw_json)
    competitor_count, avg_da, has_strong = estimate_competition_from_slots(slots)
    features = extract_serp_features_from_slots(slots)

    # Check for AI overview presence
    ai_overview = (
        "ai_overview" in features
        or bool(raw_json.get("aiOverview"))
        or bool(raw_json.get("ai_overview"))
    )

    enrichment = {
        "serp_enrichment": {
            "status": "enriched",
            "snapshot_id": str(snapshot.id),
            "captured_at": snapshot.captured_at.isoformat() if snapshot.captured_at else None,
            "estimated_monthly_searches": volume_estimate,
            "volume_source": snapshot.raw_provider or "unknown",
            "competitor_domain_count": competitor_count,
            "avg_competitor_da_estimate": avg_da,
            "has_strong_domains": has_strong,
            "serp_features_present": features,
            "ai_overview_present": ai_overview,
            "slot_count": len(slots),
        }
    }

    node.evidence_json = merge_enrichment(node.evidence_json, enrichment)
    return node


async def batch_enrich_site_keywords(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
    *,
    only_in_scope: bool = True,
) -> list[KeywordPyramidNode]:
    """Enrich all keywords for a site with SERP data.

    Args:
        only_in_scope: if True, only enrich in_scope keywords
    """
    query = select(KeywordPyramidNode).where(
        KeywordPyramidNode.workspace_id == workspace_id,
        KeywordPyramidNode.site_id == site_id,
    )
    if only_in_scope:
        query = query.where(
            KeywordPyramidNode.business_fit_status == "in_scope"
        )

    result = await db.execute(query)
    nodes = list(result.scalars().all())

    enriched: list[KeywordPyramidNode] = []
    for node in nodes:
        try:
            enriched_node = await enrich_keyword_from_serp(db, node)
            enriched.append(enriched_node)
        except Exception:
            enriched.append(node)  # keep original on error

    await db.flush()
    return enriched


def build_keyword_score_input(
    node: KeywordPyramidNode,
    *,
    gsc_impressions: int = 0,
    gsc_clicks: int = 0,
    gsc_position: float = 99.0,
    topic_cluster_coverage: float = 0.0,
    pillar_has_page: bool = False,
) -> KeywordScoreInput:
    """Build a KeywordScoreInput from an enriched KeywordPyramidNode.

    Pulls SERP enrichment from evidence_json if available.
    """
    evidence = node.evidence_json or {}
    serp = evidence.get("enrichment", {}).get("serp_enrichment", {}) or evidence.get("serp_enrichment", {})

    return KeywordScoreInput(
        keyword=node.keyword or "",
        node_type=node.node_type or "cluster",
        intent=node.intent,
        estimated_monthly_searches=serp.get("estimated_monthly_searches", 0),
        volume_source=serp.get("volume_source", "none"),
        competitor_domain_count=serp.get("competitor_domain_count", 0),
        avg_competitor_da=float(serp.get("avg_competitor_da_estimate", 0)),
        top10_has_strong_domains=serp.get("has_strong_domains", False),
        serp_features_present=serp.get("serp_features_present", []),
        ai_overview_present=serp.get("ai_overview_present", False),
        ai_citation_signals=_extract_ai_signals(node),
        topic_cluster_id=str(node.topic_cluster_id) if node.topic_cluster_id else None,
        topic_cluster_coverage=topic_cluster_coverage,
        pillar_has_page=pillar_has_page,
        gsc_impressions_28d=gsc_impressions,
        gsc_clicks_28d=gsc_clicks,
        gsc_avg_position=gsc_position,
        business_fit_status=node.business_fit_status or "needs_review",
        is_approved=node.approved_at is not None,
    )


def _extract_ai_signals(node: KeywordPyramidNode) -> list[str]:
    """Extract AI citation signals from keyword node properties."""
    signals: list[str] = []
    evidence = node.evidence_json or {}

    # FAQ format is good for AI citation
    if node.node_type == "faq":
        signals.append("has_faq_format")

    # Clear structure (has parent = part of hierarchy)
    if node.parent_id:
        signals.append("has_clear_structure")

    # Check for original data in evidence
    enrichment = evidence.get("enrichment", {}) or {}
    serp = enrichment.get("serp_enrichment", {}) or {}
    if serp.get("serp_features_present"):
        signals.append("has_original_data")

    # Brand entity match
    if node.business_fit_status == "in_scope" and node.approved_at:
        signals.append("has_brand_entity_match")

    return signals


async def score_site_keywords(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
    *,
    only_in_scope: bool = True,
) -> list[KeywordScoreResult]:
    """Score all keywords for a site using the five-factor model.

    Enriches from SERP first, then scores each keyword.
    Returns sorted by total_score descending.
    """
    # Enrich first
    nodes = await batch_enrich_site_keywords(
        db, workspace_id, site_id, only_in_scope=only_in_scope
    )

    # Build score inputs
    inputs: list[KeywordScoreInput] = []
    for node in nodes:
        inp = build_keyword_score_input(node)
        inputs.append(inp)

    return score_keywords_batch(inputs)
