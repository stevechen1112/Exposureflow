"""AI visibility site dashboard aggregation."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.models import (
    AIProbeRun,
    AIProbeSet,
    AICitation,
    BrandMention,
    SerpoRecord,
)


async def build_ai_visibility_dashboard(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
) -> dict:
    probe_sets = await db.execute(
        select(func.count()).select_from(AIProbeSet).where(
            AIProbeSet.workspace_id == workspace_id,
            AIProbeSet.site_id == site_id,
        )
    )
    probe_runs = await db.execute(
        select(func.count()).select_from(AIProbeRun).where(
            AIProbeRun.workspace_id == workspace_id,
            AIProbeRun.site_id == site_id,
        )
    )
    citations = await db.execute(
        select(func.count()).select_from(AICitation).where(
            AICitation.workspace_id == workspace_id,
            AICitation.site_id == site_id,
        )
    )
    brand_mentions = await db.execute(
        select(func.count()).select_from(BrandMention).where(
            BrandMention.workspace_id == workspace_id,
            BrandMention.site_id == site_id,
        )
    )
    competitor_citations = await db.execute(
        select(func.count()).select_from(AICitation).where(
            AICitation.workspace_id == workspace_id,
            AICitation.site_id == site_id,
            AICitation.is_competitor.is_(True),
        )
    )
    serpo = await db.execute(
        select(SerpoRecord)
        .where(
            SerpoRecord.workspace_id == workspace_id,
            SerpoRecord.site_id == site_id,
        )
        .order_by(SerpoRecord.captured_at.desc())
        .limit(1)
    )
    latest_serpo = serpo.scalar_one_or_none()

    recent_citations = await db.execute(
        select(AICitation)
        .where(
            AICitation.workspace_id == workspace_id,
            AICitation.site_id == site_id,
        )
        .order_by(AICitation.captured_at.desc())
        .limit(20)
    )

    sentiment_summary = {}
    if latest_serpo:
        sentiment_summary = {
            "positive": latest_serpo.first_page_positive_count,
            "neutral": latest_serpo.first_page_neutral_count,
            "negative": latest_serpo.first_page_negative_count,
            "wrong_info": latest_serpo.first_page_wrong_info_count,
        }

    return {
        "probe_set_count": int(probe_sets.scalar_one()),
        "probe_run_count": int(probe_runs.scalar_one()),
        "citation_count": int(citations.scalar_one()),
        "brand_mention_count": int(brand_mentions.scalar_one()),
        "competitor_mention_count": int(competitor_citations.scalar_one()),
        "serpo_summary": sentiment_summary,
        "recent_citations": [
            {
                "id": str(c.id),
                "surface": c.surface,
                "cited_url": c.cited_url,
                "captured_at": c.captured_at.isoformat() if c.captured_at else None,
                "is_own_site": c.is_own_site,
                "is_competitor": c.is_competitor,
            }
            for c in recent_citations.scalars().all()
        ],
    }
