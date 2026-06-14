"""Entity consistency checks and entity_fix opportunity detection."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EntityInconsistency:
    source_url: str
    mention_text: str
    sentiment: str
    reason: str


@dataclass(frozen=True)
class EntityCheckResult:
    consistency_score: float
    inconsistencies: list[EntityInconsistency]
    recommended_actions: list[str]


def check_entity_consistency(
    *,
    canonical_name: str,
    description: str | None,
    aliases: list[str],
    mentions: list,
) -> EntityCheckResult:
    inconsistencies: list[EntityInconsistency] = []
    for mention in mentions:
        sentiment = getattr(mention, "sentiment", None) or ""
        if sentiment == "wrong_info":
            inconsistencies.append(
                EntityInconsistency(
                    source_url=getattr(mention, "source_url", ""),
                    mention_text=getattr(mention, "mention_text", ""),
                    sentiment=sentiment,
                    reason="Brand description conflicts with canonical entity",
                )
            )
        elif sentiment == "negative" and canonical_name.lower() in (
            getattr(mention, "mention_text", "") or ""
        ).lower():
            inconsistencies.append(
                EntityInconsistency(
                    source_url=getattr(mention, "source_url", ""),
                    mention_text=getattr(mention, "mention_text", ""),
                    sentiment=sentiment,
                    reason="Negative brand portrayal detected",
                )
            )

    wrong_count = sum(1 for i in inconsistencies if i.sentiment == "wrong_info")
    score = max(0.0, 100.0 - wrong_count * 25.0 - (len(inconsistencies) - wrong_count) * 10.0)
    actions: list[str] = []
    if wrong_count:
        actions.append("Update official brand description on high-authority sources")
        actions.append("Create entity_fix opportunity for outdated AI answers")
    return EntityCheckResult(
        consistency_score=round(score, 2),
        inconsistencies=inconsistencies,
        recommended_actions=actions,
    )


def entity_fix_candidates_from_runs(runs: list, our_brand_names: set[str]) -> list[dict]:
    """OG-011: detect wrong or outdated brand descriptions in AI answers."""
    candidates: list[dict] = []
    for run in runs:
        if run.sentiment not in {"wrong_info", "negative"}:
            continue
        if not run.our_brand_mentioned:
            continue
        candidates.append(
            {
                "rule_id": "OG-011",
                "opportunity_type": "entity_fix",
                "prompt": run.prompt,
                "surface": run.surface,
                "reason": "OG-011: AI answer contains wrong or outdated brand description",
                "probe_run_id": str(run.id),
                "sentiment": run.sentiment,
            }
        )
    return candidates
