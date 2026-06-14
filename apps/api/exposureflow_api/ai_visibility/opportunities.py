"""AI visibility opportunity rules OG-010 and OG-011."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AiOpportunityCandidate:
    rule_id: str
    opportunity_type: str
    keyword: str | None
    reason: str
    priority: str
    extra_evidence: dict


def detect_ai_citation_ready(
    *,
    prompt: str,
    runs: list,
    has_reinforceable_asset: bool,
    min_external_citation_rate: float = 0.5,
) -> AiOpportunityCandidate | None:
    """OG-010: competitor/third-party URLs cited but our site is not."""
    if not runs or not has_reinforceable_asset:
        return None
    external_cited = sum(
        1 for r in runs if getattr(r, "external_url_cited", False) and not r.our_url_cited
    )
    if external_cited / len(runs) < min_external_citation_rate:
        return None
    if any(r.our_url_cited for r in runs):
        return None
    return AiOpportunityCandidate(
        rule_id="OG-010",
        opportunity_type="ai_citation_ready",
        keyword=prompt,
        reason="OG-010: AI probes cite competitors or third parties but not our site",
        priority="high",
        extra_evidence={
            "probe_run_count": len(runs),
            "external_cited_runs": external_cited,
        },
    )


def detect_entity_fix(
    *,
    prompt: str,
    sentiment: str | None,
    our_brand_mentioned: bool,
    probe_run_id: str,
) -> AiOpportunityCandidate | None:
    """OG-011: wrong or outdated brand description in AI answer."""
    if not our_brand_mentioned or sentiment not in {"wrong_info", "negative"}:
        return None
    return AiOpportunityCandidate(
        rule_id="OG-011",
        opportunity_type="entity_fix",
        keyword=prompt,
        reason="OG-011: AI answer contains incorrect or outdated brand description",
        priority="high",
        extra_evidence={"probe_run_id": probe_run_id, "sentiment": sentiment},
    )
