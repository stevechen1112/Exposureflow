"""Decision plane orchestration."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.common.errors import not_found
from exposureflow_api.decision.candidate_generator import generate_candidates_from_opportunities
from exposureflow_api.decision.roadmap_builder import build_roadmap_items
from exposureflow_api.decision.selector import (
    build_rule_rationale,
    rank_candidates,
    selection_confidence,
)
from exposureflow_api.models import (
    ActionCandidate,
    ActionDecision,
    ExposureOpportunity,
    Roadmap,
    RoadmapItem,
)


async def generate_action_candidates(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
) -> int:
    existing_result = await db.execute(
        select(ActionCandidate.opportunity_id).where(
            ActionCandidate.workspace_id == workspace_id,
            ActionCandidate.site_id == site_id,
        )
    )
    existing_opp_ids = {row[0] for row in existing_result.all()}

    opps_result = await db.execute(
        select(ExposureOpportunity)
        .where(
            ExposureOpportunity.workspace_id == workspace_id,
            ExposureOpportunity.site_id == site_id,
            ExposureOpportunity.status == "open",
        )
        .order_by(ExposureOpportunity.total_opportunity_score.desc())
    )
    opportunities = [
        opp for opp in opps_result.scalars().all() if opp.id not in existing_opp_ids
    ]
    generated = generate_candidates_from_opportunities(opportunities)
    created = 0
    for item in generated:
        db.add(
            ActionCandidate(
                workspace_id=workspace_id,
                site_id=site_id,
                opportunity_id=UUID(item.opportunity_id),
                action_type=item.action_type,
                target_asset_id=UUID(item.target_asset_id) if item.target_asset_id else None,
                action_payload_json=item.action_payload_json,
                expected_exposure_impact=item.expected_exposure_impact,
                risk_level=item.risk_level,
                required_inputs_json=item.required_inputs_json,
                evidence_json=item.evidence_json,
                created_by=item.created_by,
                rank_score=item.rank_score,
            )
        )
        created += 1
    await db.flush()
    return created


async def list_action_candidates(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
    *,
    status: str | None = None,
) -> list[ActionCandidate]:
    stmt = select(ActionCandidate).where(
        ActionCandidate.workspace_id == workspace_id,
        ActionCandidate.site_id == site_id,
    )
    if status:
        stmt = stmt.where(ActionCandidate.decision_status == status)
    result = await db.execute(stmt.order_by(ActionCandidate.rank_score.desc()))
    return rank_candidates(list(result.scalars().all()))


async def _get_candidate(
    db: AsyncSession, workspace_id: UUID, candidate_id: UUID
) -> ActionCandidate:
    candidate = await db.get(ActionCandidate, candidate_id)
    if candidate is None or candidate.workspace_id != workspace_id:
        raise not_found("Action candidate")
    return candidate


async def get_candidate_in_workspace(
    db: AsyncSession, workspace_id: UUID, candidate_id: UUID
) -> ActionCandidate:
    return await _get_candidate(db, workspace_id, candidate_id)


async def record_decision(
    db: AsyncSession,
    *,
    workspace_id: UUID,
    candidate_id: UUID,
    user_id: UUID,
    decision: str,
    rationale: str | None = None,
    scheduled_for: date | None = None,
    confidence: float | None = None,
) -> ActionDecision:
    candidate = await _get_candidate(db, workspace_id, candidate_id)
    if candidate.decision_status != "pending":
        raise not_found("Action candidate")

    final_rationale = rationale or build_rule_rationale(candidate)
    final_confidence = confidence if confidence is not None else selection_confidence(candidate)
    status_map = {
        "approve": "approved",
        "reject": "rejected",
        "defer": "deferred",
        "needs_review": "needs_review",
    }
    candidate.decision_status = status_map.get(decision, "needs_review")

    row = ActionDecision(
        workspace_id=workspace_id,
        candidate_id=candidate_id,
        decision=decision,
        selected_by=user_id,
        rationale=final_rationale,
        confidence=final_confidence,
        scheduled_for=scheduled_for,
    )
    db.add(row)
    await db.flush()
    return row


async def build_site_roadmap(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
    *,
    horizon_weeks: int,
    title: str | None = None,
) -> Roadmap:
    existing_items = await db.execute(
        select(RoadmapItem.decision_id).where(
            RoadmapItem.workspace_id == workspace_id,
            RoadmapItem.site_id == site_id,
        )
    )
    scheduled_decision_ids = {row[0] for row in existing_items.all()}

    approved = await db.execute(
        select(ActionDecision, ActionCandidate)
        .join(ActionCandidate, ActionCandidate.id == ActionDecision.candidate_id)
        .where(
            ActionDecision.workspace_id == workspace_id,
            ActionCandidate.site_id == site_id,
            ActionDecision.decision == "approve",
            ActionCandidate.decision_status == "approved",
        )
        .order_by(ActionCandidate.rank_score.desc())
    )
    rows = [
        row
        for row in approved.all()
        if row[0].id not in scheduled_decision_ids
    ]
    plan = build_roadmap_items(
        approved_rows=rows,
        horizon_weeks=horizon_weeks,
    )

    roadmap = Roadmap(
        workspace_id=workspace_id,
        site_id=site_id,
        horizon_weeks=horizon_weeks,
        title=title or f"{horizon_weeks}-week exposure roadmap",
        status="active",
    )
    db.add(roadmap)
    await db.flush()

    for item in plan:
        db.add(
            RoadmapItem(
                workspace_id=workspace_id,
                site_id=site_id,
                roadmap_id=roadmap.id,
                decision_id=UUID(item.decision_id),
                candidate_id=UUID(item.candidate_id),
                action_type=item.action_type,
                title=item.title,
                week_number=item.week_number,
                due_date=item.due_date,
                risk_level=item.risk_level,
                expected_exposure_impact=item.expected_exposure_impact,
                dependency_item_ids=item.dependency_item_ids,
                sort_order=item.sort_order,
            )
        )
    await db.flush()
    return roadmap


async def get_roadmap_with_items(
    db: AsyncSession,
    workspace_id: UUID,
    roadmap_id: UUID,
) -> tuple[Roadmap, list[RoadmapItem]]:
    roadmap = await db.get(Roadmap, roadmap_id)
    if roadmap is None or roadmap.workspace_id != workspace_id:
        raise not_found("Roadmap")
    items_result = await db.execute(
        select(RoadmapItem)
        .where(RoadmapItem.roadmap_id == roadmap_id)
        .order_by(RoadmapItem.sort_order)
    )
    return roadmap, list(items_result.scalars().all())


async def list_roadmaps(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
    *,
    limit: int = 10,
) -> list[Roadmap]:
    result = await db.execute(
        select(Roadmap)
        .where(
            Roadmap.workspace_id == workspace_id,
            Roadmap.site_id == site_id,
        )
        .order_by(Roadmap.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
