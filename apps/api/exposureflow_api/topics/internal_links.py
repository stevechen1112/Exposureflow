"""Internal link suggestions from topic graph."""

from __future__ import annotations

from dataclasses import dataclass

from exposureflow_api.topics.graph_builder import jaccard_similarity, tokenize


@dataclass
class LinkSuggestion:
    source_url: str
    target_url: str
    anchor_text: str
    anchor_relevance_score: float
    evidence: dict


def anchor_relevance(source_keyword: str, target_keyword: str) -> float:
    return round(jaccard_similarity(tokenize(source_keyword), tokenize(target_keyword)), 4)


def _slugify(keyword: str) -> str:
    return "-".join(tokenize(keyword))[:80] or "page"


def suggest_internal_links(
    *,
    pillar_url: str,
    pillar_keyword: str,
    gap_nodes: list[dict],
    site_domain: str | None = None,
    min_score: float = 0.2,
) -> list[LinkSuggestion]:
    """Suggest links from pillar page to gap nodes, sorted by anchor relevance."""
    suggestions: list[LinkSuggestion] = []
    for node in gap_nodes:
        keyword = node.get("keyword", "")
        target_url = node.get("current_best_url") or node.get("target_url")
        if not target_url and site_domain:
            target_url = f"https://{site_domain}/{_slugify(keyword)}"
        if not target_url or target_url == pillar_url:
            continue
        score = anchor_relevance(pillar_keyword, keyword)
        if score < min_score:
            score = max(score, 0.15)
        evidence = {
            "pillar_keyword": pillar_keyword,
            "target_keyword": keyword,
            "node_status": node.get("status", "gap"),
        }
        if not node.get("current_best_url"):
            evidence["target_type"] = "proposed_page"
        suggestions.append(
            LinkSuggestion(
                source_url=pillar_url,
                target_url=target_url,
                anchor_text=keyword,
                anchor_relevance_score=score,
                evidence=evidence,
            )
        )
    return sorted(suggestions, key=lambda s: -s.anchor_relevance_score)
