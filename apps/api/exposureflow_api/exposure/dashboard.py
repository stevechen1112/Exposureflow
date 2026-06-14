"""Exposure dashboard aggregation."""

from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.models import (
    AICitation,
    ExposureAsset,
    ExposureOpportunity,
    GscPerformanceRow,
    SerpSlotTarget,
    TechnicalIssue,
    TopicCluster,
)


async def build_dashboard_metrics(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
) -> dict:
    today = date.today()
    current_start = today - timedelta(days=28)
    previous_start = today - timedelta(days=56)

    current_impressions = await db.execute(
        select(func.coalesce(func.sum(GscPerformanceRow.impressions), 0)).where(
            GscPerformanceRow.workspace_id == workspace_id,
            GscPerformanceRow.site_id == site_id,
            GscPerformanceRow.date >= current_start,
        )
    )
    prev_impressions = await db.execute(
        select(func.coalesce(func.sum(GscPerformanceRow.impressions), 0)).where(
            GscPerformanceRow.workspace_id == workspace_id,
            GscPerformanceRow.site_id == site_id,
            GscPerformanceRow.date >= previous_start,
            GscPerformanceRow.date < current_start,
        )
    )
    total_impressions = int(current_impressions.scalar_one())
    prev_total = int(prev_impressions.scalar_one())
    if prev_total > 0:
        impressions_delta_pct = round((total_impressions - prev_total) / prev_total * 100, 1)
    else:
        impressions_delta_pct = 0.0 if total_impressions == 0 else 100.0

    query_coverage = await db.execute(
        select(func.count(func.distinct(GscPerformanceRow.query))).where(
            GscPerformanceRow.workspace_id == workspace_id,
            GscPerformanceRow.site_id == site_id,
            GscPerformanceRow.date >= current_start,
            GscPerformanceRow.impressions > 0,
        )
    )
    indexed_assets = await db.execute(
        select(func.count()).select_from(ExposureAsset).where(
            ExposureAsset.workspace_id == workspace_id,
            ExposureAsset.site_id == site_id,
            ExposureAsset.status != "merged",
        )
    )

    position_rows = await db.execute(
        select(GscPerformanceRow.query, func.avg(GscPerformanceRow.position).label("pos")).where(
            GscPerformanceRow.workspace_id == workspace_id,
            GscPerformanceRow.site_id == site_id,
            GscPerformanceRow.date >= current_start,
            GscPerformanceRow.position.isnot(None),
        ).group_by(GscPerformanceRow.query)
    )
    top_3 = top_10 = top_20 = 0
    for _query, pos in position_rows.all():
        if pos is None:
            continue
        p = float(pos)
        if p <= 3:
            top_3 += 1
        if p <= 10:
            top_10 += 1
        if p <= 20:
            top_20 += 1

    serp_slots = await db.execute(
        select(func.count()).select_from(SerpSlotTarget).where(
            SerpSlotTarget.workspace_id == workspace_id,
            SerpSlotTarget.site_id == site_id,
            SerpSlotTarget.target_status == "achieved",
        )
    )
    ai_citations = await db.execute(
        select(func.count()).select_from(AICitation).where(
            AICitation.workspace_id == workspace_id,
            AICitation.site_id == site_id,
        )
    )
    open_opps = await db.execute(
        select(func.count()).select_from(ExposureOpportunity).where(
            ExposureOpportunity.workspace_id == workspace_id,
            ExposureOpportunity.site_id == site_id,
            ExposureOpportunity.status == "open",
        )
    )
    critical_blockers = await db.execute(
        select(func.count()).select_from(TechnicalIssue).where(
            TechnicalIssue.workspace_id == workspace_id,
            TechnicalIssue.site_id == site_id,
            TechnicalIssue.status == "open",
            TechnicalIssue.severity.in_(["critical", "high"]),
        )
    )

    clusters = await db.execute(
        select(TopicCluster)
        .where(
            TopicCluster.workspace_id == workspace_id,
            TopicCluster.site_id == site_id,
        )
        .order_by(TopicCluster.total_impressions.desc())
        .limit(8)
    )
    topic_cluster_performance = [
        {
            "id": str(c.id),
            "name": c.name,
            "total_impressions": int(c.total_impressions or 0),
            "coverage_score": float(c.coverage_score or 0),
            "ai_visibility_score": float(c.ai_visibility_score or 0),
            "status": c.status,
        }
        for c in clusters.scalars().all()
    ]

    return {
        "total_impressions": total_impressions,
        "impressions_delta_pct": impressions_delta_pct,
        "query_coverage_count": int(query_coverage.scalar_one()),
        "indexed_asset_count": int(indexed_assets.scalar_one()),
        "top_3_count": top_3,
        "top_10_count": top_10,
        "top_20_count": top_20,
        "serp_slot_count": int(serp_slots.scalar_one()),
        "ai_citation_count": int(ai_citations.scalar_one()),
        "open_opportunity_count": int(open_opps.scalar_one()),
        "critical_blocker_count": int(critical_blockers.scalar_one()),
        "topic_cluster_performance": topic_cluster_performance,
    }
