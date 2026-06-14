"""Rank action candidates and build rule-based rationale."""

from __future__ import annotations

RISK_ORDER = {"high": 0, "medium": 1, "low": 2}


def rank_candidates(candidates: list) -> list:
    return sorted(
        candidates,
        key=lambda c: (
            -float(c.rank_score or c.expected_exposure_impact or 0),
            RISK_ORDER.get(c.risk_level, 1),
            str(c.id),
        ),
    )


def build_rule_rationale(candidate) -> str:
    """Rule-based rationale; LLM may augment later but must not invent actions."""
    keyword = (candidate.action_payload_json or {}).get("keyword") or ""
    impact = float(candidate.expected_exposure_impact or 0)
    parts = [
        f"Recommend {candidate.action_type}",
        f"with expected exposure impact {impact:.1f}",
        f"and {candidate.risk_level} risk",
    ]
    if keyword:
        parts.append(f"for keyword '{keyword}'")
    evidence = candidate.evidence_json or {}
    rule_id = evidence.get("rule_id")
    if rule_id:
        parts.append(f"(source rule {rule_id})")
    return ". ".join(parts) + "."


def selection_confidence(candidate) -> float:
    impact = float(candidate.expected_exposure_impact or 0)
    if impact >= 75:
        return 90.0
    if impact >= 55:
        return 80.0
    if impact >= 35:
        return 70.0
    return 60.0
