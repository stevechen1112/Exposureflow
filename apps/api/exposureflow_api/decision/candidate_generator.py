"""Deterministic ActionCandidate generation from ExposureOpportunity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from exposureflow_api.strategy.business_fit import BusinessFitResult

PRIORITY_TO_RISK = {
    "critical": "high",
    "high": "high",
    "medium": "medium",
    "low": "low",
}

TECHNICAL_ACTION_TYPES = frozenset({"technical_fix", "fix_indexability"})


@dataclass(frozen=True)
class GeneratedCandidate:
    opportunity_id: str
    action_type: str
    target_asset_id: str | None
    action_payload_json: dict
    expected_exposure_impact: float
    risk_level: str
    required_inputs_json: list[dict]
    evidence_json: dict
    created_by: str
    rank_score: float


def _risk_from_priority(priority: str) -> str:
    return PRIORITY_TO_RISK.get(priority, "medium")


def _required_inputs(opportunity) -> list[dict]:
    inputs: list[dict] = []
    if opportunity.keyword:
        inputs.append({"field": "keyword", "value": opportunity.keyword})
    if opportunity.current_url:
        inputs.append({"field": "current_url", "value": opportunity.current_url})
    if opportunity.target_url:
        inputs.append({"field": "target_url", "value": opportunity.target_url})
    return inputs


def _action_payload(opportunity) -> dict:
    return {
        "opportunity_type": opportunity.opportunity_type,
        "keyword": opportunity.keyword,
        "current_url": opportunity.current_url,
        "target_url": opportunity.target_url,
        "search_context": opportunity.search_context,
        "priority": opportunity.priority,
    }


def opportunity_to_candidate(
    opportunity,
    fit: BusinessFitResult | None = None,
) -> GeneratedCandidate:
    """Map one open opportunity to a deterministic action candidate."""
    evidence = dict(opportunity.evidence_json or {})
    evidence.update(
        {
            "opportunity_id": str(opportunity.id),
            "opportunity_type": opportunity.opportunity_type,
            "total_opportunity_score": float(opportunity.total_opportunity_score or 0),
            "reason": opportunity.reason,
            "current_impressions": int(opportunity.current_impressions or 0),
            "current_position": float(opportunity.current_position)
            if opportunity.current_position is not None
            else None,
        }
    )
    impact = float(opportunity.total_opportunity_score or 0)
    rank_score = impact
    action_type = opportunity.opportunity_type
    risk_level = _risk_from_priority(opportunity.priority)

    if fit is not None:
        evidence["business_fit"] = fit.evidence
        evidence["business_fit_score"] = fit.business_fit_score
        rank_score *= fit.business_fit_score
        if fit.blocked:
            action_type = "no_op"
            risk_level = "blocked"
            evidence["blocked_reason"] = "OG-017: out_of_scope or blocked keyword"
            rank_score = 0.0

    if opportunity.opportunity_type in TECHNICAL_ACTION_TYPES and action_type != "no_op":
        rank_score += 25.0
    return GeneratedCandidate(
        opportunity_id=str(opportunity.id),
        action_type=action_type,
        target_asset_id=str(opportunity.exposure_asset_id)
        if opportunity.exposure_asset_id
        else None,
        action_payload_json=_action_payload(opportunity),
        expected_exposure_impact=impact,
        risk_level=risk_level,
        required_inputs_json=_required_inputs(opportunity),
        evidence_json=evidence,
        created_by="rule",
        rank_score=rank_score,
    )


def generate_candidates_from_opportunities(
    opportunities: list,
    *,
    fit_by_opp_id: dict[UUID, BusinessFitResult] | None = None,
) -> list[GeneratedCandidate]:
    """Deterministic ordering: higher rank_score first, then opportunity_id."""
    generated = [
        opportunity_to_candidate(
            opp,
            fit=(fit_by_opp_id or {}).get(opp.id),
        )
        for opp in opportunities
    ]
    return sorted(
        generated,
        key=lambda c: (-c.rank_score, c.opportunity_id),
    )
