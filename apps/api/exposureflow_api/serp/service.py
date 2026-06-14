"""SERP matrix and slot target orchestration."""

from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.common.errors import not_found
from exposureflow_api.exposure.scorer import ScoreInput, score_opportunity
from exposureflow_api.exposure.service import _build_opportunity
from exposureflow_api.models import (
    ExposureAsset,
    ExposureOpportunity,
    GscPerformanceRow,
    SerpQuerySnapshot,
    SerpSlot,
    SerpSlotTarget,
    TopicCluster,
    TopicNode,
)
from exposureflow_api.serp.matrix import (
    build_matrix_from_slots,
    recommended_action_for,
    target_status_from_matrix,
)
from exposureflow_api.serp.opportunities import (
    detect_featured_snippet_opportunity,
    detect_media_slot_opportunities,
    detect_paa_opportunities,
)


def _slot_dict(slot: SerpSlot) -> dict:
    return {
        "slot_type": slot.slot_type,
        "url": slot.url,
        "title": slot.title,
        "snippet": slot.snippet,
        "owner_domain": slot.owner_domain,
        "is_own_site": slot.is_own_site,
        "is_competitor": slot.is_competitor,
        "is_third_party": slot.is_third_party,
    }


async def sync_slot_targets_for_snapshot(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
    snapshot_id: UUID,
) -> int:
    snapshot = await db.get(SerpQuerySnapshot, snapshot_id)
    if snapshot is None or snapshot.workspace_id != workspace_id:
        return 0

    slots_result = await db.execute(select(SerpSlot).where(SerpSlot.snapshot_id == snapshot_id))
    slots = [_slot_dict(s) for s in slots_result.scalars().all()]
    cells = build_matrix_from_slots(
        keyword=snapshot.keyword,
        snapshot_id=str(snapshot_id),
        slots=slots,
    )

    cluster_id = None
    node = await db.execute(
        select(TopicNode).where(
            TopicNode.workspace_id == workspace_id,
            TopicNode.site_id == site_id,
            TopicNode.keyword == snapshot.keyword,
        )
    )
    topic_node = node.scalar_one_or_none()
    if topic_node:
        cluster_id = topic_node.topic_cluster_id

    upserted = 0
    for cell in cells:
        if cell.matrix_status == "available" and cell.slot_type == "organic":
            continue
        existing = await db.execute(
            select(SerpSlotTarget).where(
                SerpSlotTarget.workspace_id == workspace_id,
                SerpSlotTarget.site_id == site_id,
                SerpSlotTarget.keyword == cell.keyword,
                SerpSlotTarget.slot_type == cell.slot_type,
            )
        )
        target = existing.scalar_one_or_none()
        if target is None:
            target = SerpSlotTarget(
                workspace_id=workspace_id,
                site_id=site_id,
                keyword=cell.keyword,
                slot_type=cell.slot_type,
            )
            db.add(target)
        target.topic_cluster_id = cluster_id
        target.current_owner = cell.matrix_status
        target.current_owner_url = cell.owner_url
        target.target_status = target_status_from_matrix(cell.matrix_status)
        target.recommended_action = recommended_action_for(cell.matrix_status, cell.slot_type)
        target.evidence_json = {
            "snapshot_id": cell.snapshot_id,
            "owner_domain": cell.owner_domain,
            "title": cell.title,
        }
        upserted += 1
    await db.flush()
    return upserted


async def build_site_matrix(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
    *,
    cluster_id: UUID | None = None,
) -> dict:
    keywords: list[str] | None = None
    if cluster_id:
        cluster = await db.get(TopicCluster, cluster_id)
        if (
            cluster is None
            or cluster.workspace_id != workspace_id
            or cluster.site_id != site_id
        ):
            raise not_found("Topic cluster")
        nodes = await db.execute(
            select(TopicNode.keyword).where(
                TopicNode.workspace_id == workspace_id,
                TopicNode.topic_cluster_id == cluster_id,
            )
        )
        keywords = [k for (k,) in nodes.all()]

    stmt = (
        select(SerpQuerySnapshot)
        .where(
            SerpQuerySnapshot.workspace_id == workspace_id,
            SerpQuerySnapshot.site_id == site_id,
        )
        .order_by(SerpQuerySnapshot.captured_at.desc())
    )
    if keywords:
        stmt = stmt.where(SerpQuerySnapshot.keyword.in_(keywords))
    snapshots = list((await db.execute(stmt)).scalars().all())

    seen_keywords: set[str] = set()
    matrix_rows: list[dict] = []
    for snapshot in snapshots:
        if snapshot.keyword in seen_keywords:
            continue
        seen_keywords.add(snapshot.keyword)
        slots_result = await db.execute(
            select(SerpSlot).where(SerpSlot.snapshot_id == snapshot.id)
        )
        slots = [_slot_dict(s) for s in slots_result.scalars().all()]
        cells = build_matrix_from_slots(
            keyword=snapshot.keyword,
            snapshot_id=str(snapshot.id),
            slots=slots,
        )
        matrix_rows.append(
            {
                "keyword": snapshot.keyword,
                "snapshot_id": str(snapshot.id),
                "captured_at": snapshot.captured_at.isoformat(),
                "cells": [
                    {
                        "slot_type": c.slot_type,
                        "matrix_status": c.matrix_status,
                        "owner_url": c.owner_url,
                        "owner_domain": c.owner_domain,
                        "title": c.title,
                    }
                    for c in cells
                ],
            }
        )

    return {
        "site_id": str(site_id),
        "cluster_id": str(cluster_id) if cluster_id else None,
        "keywords": matrix_rows,
    }


async def _site_p75_impressions(db: AsyncSession, workspace_id: UUID, site_id: UUID) -> int:
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
    result = await db.execute(select(func.percentile_cont(0.75).within_group(subq.c.imp)))
    value = result.scalar_one_or_none()
    return int(value or 1)


async def _existing_opp_keys(db: AsyncSession, workspace_id: UUID, site_id: UUID) -> set[tuple[str, str | None, str | None, str]]:
    result = await db.execute(
        select(
            ExposureOpportunity.keyword,
            ExposureOpportunity.current_url,
            ExposureOpportunity.opportunity_type,
            ExposureOpportunity.evidence_json,
        ).where(
            ExposureOpportunity.workspace_id == workspace_id,
            ExposureOpportunity.site_id == site_id,
            ExposureOpportunity.status == "open",
        )
    )
    keys: set[tuple[str, str | None, str | None, str]] = set()
    for keyword, current_url, opp_type, evidence in result.all():
        keys.add(((evidence or {}).get("rule_id", ""), keyword, current_url, opp_type or ""))
    return keys


async def generate_serp_opportunities(db: AsyncSession, workspace_id: UUID, site_id: UUID) -> int:
    p75 = await _site_p75_impressions(db, workspace_id, site_id)
    p95 = p75 * 2 or 1

    gsc = await db.execute(
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
    query_stats: dict[str, dict] = defaultdict(lambda: {"impressions": 0, "best_url": None, "position": None})
    for query, page, impressions, position in gsc.all():
        imp = int(impressions or 0)
        query_stats[query]["impressions"] += imp
        if query_stats[query]["best_url"] is None or imp > query_stats[query].get("page_imp", 0):
            query_stats[query]["best_url"] = page
            query_stats[query]["position"] = float(position or 0)
            query_stats[query]["page_imp"] = imp

    asset_rows = list(
        (
            await db.execute(
                select(ExposureAsset).where(
                    ExposureAsset.workspace_id == workspace_id,
                    ExposureAsset.site_id == site_id,
                )
            )
        ).scalars().all()
    )
    has_image = any(a.asset_type == "image" for a in asset_rows)
    has_video = any(a.asset_type == "video" for a in asset_rows)
    has_product_schema = any(
        (a.metadata_json or {}).get("has_product_schema") for a in asset_rows
    )

    snapshots = await db.execute(
        select(SerpQuerySnapshot)
        .where(
            SerpQuerySnapshot.workspace_id == workspace_id,
            SerpQuerySnapshot.site_id == site_id,
        )
        .order_by(SerpQuerySnapshot.captured_at.desc())
    )
    snapshot_by_keyword: dict[str, SerpQuerySnapshot] = {}
    for snap in snapshots.scalars().all():
        if snap.keyword not in snapshot_by_keyword:
            snapshot_by_keyword[snap.keyword] = snap

    seen = await _existing_opp_keys(db, workspace_id, site_id)
    created = 0

    def _track(rule_id: str, keyword: str | None, url: str | None, opp_type: str = "") -> bool:
        key = (rule_id, keyword, url, opp_type)
        if key in seen:
            return False
        seen.add(key)
        return True

    for keyword, snap in snapshot_by_keyword.items():
        stats = query_stats.get(keyword, {"impressions": 0, "best_url": None, "position": None})
        impressions = stats["impressions"]
        current_url = stats.get("best_url")
        position = stats.get("position")

        slots_result = await db.execute(select(SerpSlot).where(SerpSlot.snapshot_id == snap.id))
        slots = slots_result.scalars().all()
        slot_map = {s.slot_type: _slot_dict(s) for s in slots}
        paa_slots = [_slot_dict(s) for s in slots if s.slot_type == "paa"]

        own_urls = set()
        for s in slots:
            if s.url and s.is_own_site:
                own_urls.add(s.url)
        if current_url:
            own_urls.add(current_url)

        candidates = []
        fs = detect_featured_snippet_opportunity(
            keyword=keyword,
            impressions=impressions,
            position=position,
            p75=p75,
            featured_slot=slot_map.get("featured_snippet"),
            current_url=current_url,
        )
        if fs:
            candidates.append(fs)
        candidates.extend(
            detect_paa_opportunities(
                keyword=keyword,
                current_url=current_url,
                impressions=impressions,
                paa_slots=paa_slots,
                own_urls=own_urls,
            )
        )
        candidates.extend(
            detect_media_slot_opportunities(
                keyword=keyword,
                current_url=current_url,
                impressions=impressions,
                image_slot=slot_map.get("image"),
                video_slot=slot_map.get("video"),
                has_image_asset=has_image,
                has_video_asset=has_video,
            )
        )
        product_slot = slot_map.get("product")
        if product_slot and not has_product_schema and _track("OG-009", keyword, current_url, "add_schema"):
            score = score_opportunity(
                ScoreInput(
                    query_impressions_28d=max(impressions, 1),
                    site_p95_query_impressions=p95,
                    current_position=position,
                    targetable_slot_count=1,
                )
            )
            db.add(
                _build_opportunity(
                    workspace_id,
                    site_id,
                    opportunity_type="add_schema",
                    keyword=keyword,
                    current_url=current_url,
                    impressions=impressions,
                    position=position,
                    reason="OG-009: Product rich result available but page lacks product schema",
                    rule_id="OG-009",
                    score=score,
                    extra_evidence={"slot_type": "product"},
                )
            )
            created += 1

        for cand in candidates:
            if not _track(cand.rule_id, cand.keyword, cand.current_url, cand.opportunity_type):
                continue
            score = score_opportunity(
                ScoreInput(
                    query_impressions_28d=max(impressions, 1),
                    site_p95_query_impressions=p95,
                    current_position=position,
                    targetable_slot_count=cand.targetable_slot_count,
                )
            )
            db.add(
                _build_opportunity(
                    workspace_id,
                    site_id,
                    opportunity_type=cand.opportunity_type,
                    keyword=cand.keyword,
                    current_url=cand.current_url,
                    impressions=impressions,
                    position=position,
                    reason=cand.reason,
                    rule_id=cand.rule_id,
                    score=score,
                    extra_evidence=cand.extra_evidence,
                )
            )
            created += 1

    await db.flush()
    return created
