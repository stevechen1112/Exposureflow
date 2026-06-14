"""Deterministic opportunity scoring with evidence trace."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass
class ScoreInput:
    query_impressions_28d: int
    site_p95_query_impressions: int
    current_position: float | None
    cluster_authority_score: float = 0.0
    targetable_slot_count: int = 0
    topic_node_status: str | None = None
    business_priority: int = 3
    business_fit_score: float = 1.0
    ai_citation_score: float = 0.7
    zero_click_value_score: float = 0.7
    execution_confidence: float = 0.8


@dataclass
class ScoreResult:
    total_opportunity_score: float
    priority: str
    subscores: dict[str, float]
    evidence: dict[str, Any]


def _search_demand_score(impressions: int, site_p95: int) -> float:
    if site_p95 <= 0:
        return 0.3
    return min(1.0, math.log10(impressions + 1) / math.log10(site_p95 + 1))


def _ranking_feasibility_score(position: float | None, cluster_authority: float) -> float:
    if position is None:
        return 0.3 if cluster_authority >= 60 else 0.2
    if 4 <= position <= 10:
        return 1.0
    if 11 <= position <= 20:
        return 0.8
    if 21 <= position <= 30:
        return 0.6
    if 31 <= position <= 50:
        return 0.4
    return 0.2


def _serp_slot_score(targetable_slot_count: int) -> float:
    return min(1.0, targetable_slot_count / 4)


def _topic_contribution_score(status: str | None, business_priority: int) -> float:
    if status == "gap" and business_priority >= 4:
        return 1.0
    if status == "gap":
        return 0.8
    if status == "stale":
        return 0.6
    return 0.5


def _priority_from_score(total: float) -> str:
    if total >= 75:
        return "critical"
    if total >= 55:
        return "high"
    if total >= 35:
        return "medium"
    return "low"


def score_opportunity(data: ScoreInput) -> ScoreResult:
    business_fit = max(0.0, min(1.0, data.business_fit_score))
    search_demand = _search_demand_score(data.query_impressions_28d, data.site_p95_query_impressions)
    ranking_feasibility = _ranking_feasibility_score(
        data.current_position, data.cluster_authority_score
    )
    serp_slot = _serp_slot_score(data.targetable_slot_count)
    topic_contribution = _topic_contribution_score(data.topic_node_status, data.business_priority)
    ai_citation = max(data.ai_citation_score, 0.7)
    zero_click = max(data.zero_click_value_score, 0.7)
    execution_confidence = data.execution_confidence

    total = (
        100
        * business_fit
        * search_demand
        * ranking_feasibility
        * serp_slot
        * topic_contribution
        * execution_confidence
        * ai_citation
        * zero_click
    )
    total = round(min(100.0, max(0.0, total)), 2)

    subscores = {
        "business_fit_score": round(business_fit, 4),
        "search_demand_score": round(search_demand, 4),
        "ranking_feasibility_score": round(ranking_feasibility, 4),
        "serp_slot_score": round(serp_slot, 4),
        "topic_contribution_score": round(topic_contribution, 4),
        "ai_citation_score": round(ai_citation, 4),
        "zero_click_value_score": round(zero_click, 4),
        "execution_confidence_score": round(execution_confidence, 4),
    }
    evidence = {
        "formula": "total = 100 × business_fit × search_demand × ranking_feasibility × serp_slot × topic_contribution × execution_confidence × max(ai_citation,0.7) × max(zero_click,0.7)",
        "inputs": {
            "query_impressions_28d": data.query_impressions_28d,
            "site_p95_query_impressions": data.site_p95_query_impressions,
            "current_position": data.current_position,
            "targetable_slot_count": data.targetable_slot_count,
            "topic_node_status": data.topic_node_status,
            "business_priority": data.business_priority,
            "business_fit_score": business_fit,
        },
        "subscores": subscores,
    }
    return ScoreResult(
        total_opportunity_score=total,
        priority=_priority_from_score(total),
        subscores=subscores,
        evidence=evidence,
    )
