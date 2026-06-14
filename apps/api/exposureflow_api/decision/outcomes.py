"""Action outcome tracking for approved decisions."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.models import ActionCandidate, ActionDecision, RoadmapItem


async def list_action_outcomes(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
) -> list[dict]:
    rows = await db.execute(
        select(ActionDecision, ActionCandidate, RoadmapItem)
        .join(ActionCandidate, ActionCandidate.id == ActionDecision.candidate_id)
        .outerjoin(RoadmapItem, RoadmapItem.decision_id == ActionDecision.id)
        .where(
            ActionDecision.workspace_id == workspace_id,
            ActionCandidate.site_id == site_id,
            ActionDecision.decision == "approve",
        )
        .order_by(ActionDecision.created_at.desc())
        .limit(100)
    )
    outcomes: list[dict] = []
    for decision, candidate, roadmap_item in rows.all():
        keyword = candidate.action_payload_json.get("keyword") if candidate.action_payload_json else None
        delta = candidate.evidence_json.get("impressions_delta_28d") if candidate.evidence_json else None
        if delta is None and candidate.evidence_json:
            delta = candidate.evidence_json.get("impressions_delta_7d")
        outcomes.append(
            {
                "decision_id": str(decision.id),
                "candidate_id": str(candidate.id),
                "action_type": candidate.action_type,
                "keyword": keyword,
                "expected_exposure_impact": float(candidate.expected_exposure_impact or 0),
                "roadmap_status": roadmap_item.status if roadmap_item else "unscheduled",
                "week_number": roadmap_item.week_number if roadmap_item else None,
                "baseline_impressions": candidate.evidence_json.get("current_impressions", 0)
                if candidate.evidence_json
                else 0,
                "impressions_delta_7d": candidate.evidence_json.get("impressions_delta_7d")
                if candidate.evidence_json
                else None,
                "impressions_delta_28d": candidate.evidence_json.get("impressions_delta_28d")
                if candidate.evidence_json
                else None,
                "impressions_delta_90d": candidate.evidence_json.get("impressions_delta_90d")
                if candidate.evidence_json
                else None,
                "serp_slot_delta": candidate.evidence_json.get("serp_slot_delta")
                if candidate.evidence_json
                else None,
                "ai_citation_delta": candidate.evidence_json.get("ai_citation_delta")
                if candidate.evidence_json
                else None,
                "pattern_worth_replicating": candidate.evidence_json.get(
                    "pattern_worth_replicating"
                )
                if candidate.evidence_json
                else None,
                "created_at": decision.created_at.isoformat() if decision.created_at else None,
            }
        )
    return outcomes
