"""Cannibalization detection from GSC and SERP overlap."""

from __future__ import annotations

from dataclasses import dataclass

from exposureflow_api.topics.graph_builder import QueryPageRow, aggregate_query_stats, jaccard_similarity, tokenize


@dataclass
class CannibalizationFinding:
    keyword: str
    recommendation: str
    competing_urls: list[dict]
    evidence: dict


def _recommendation(url_count: int, position_spread: float) -> str:
    if url_count >= 3 or position_spread > 15:
        return "merge"
    if position_spread > 8:
        return "differentiate"
    return "redirect"


def detect_gsc_cannibalization(
    rows: list[QueryPageRow],
    *,
    min_url_share: float = 0.15,
    min_impressions: int = 50,
) -> list[CannibalizationFinding]:
    stats = aggregate_query_stats(rows)
    findings: list[CannibalizationFinding] = []

    for query, s in stats.items():
        if s.total_impressions < min_impressions:
            continue
        competitors = [
            (url, imp)
            for url, imp in s.urls.items()
            if imp >= s.total_impressions * min_url_share
        ]
        if len(competitors) < 2:
            continue

        positions = [
            row.position
            for row in rows
            if row.query == query and row.page in dict(competitors)
        ]
        spread = max(positions) - min(positions) if positions else 0.0
        rec = _recommendation(len(competitors), spread)
        findings.append(
            CannibalizationFinding(
                keyword=query,
                recommendation=rec,
                competing_urls=[
                    {"url": url, "impressions": imp, "share": round(imp / s.total_impressions, 4)}
                    for url, imp in sorted(competitors, key=lambda x: -x[1])
                ],
                evidence={
                    "source": "gsc_query_overlap",
                    "total_impressions": s.total_impressions,
                    "position_spread": round(spread, 2),
                    "url_count": len(competitors),
                },
            )
        )
    return findings


def detect_semantic_cannibalization(
    rows: list[QueryPageRow],
    *,
    similarity_threshold: float = 0.7,
    min_impressions: int = 100,
) -> list[CannibalizationFinding]:
    """Queries with high semantic overlap competing via different URLs."""
    stats = aggregate_query_stats(rows)
    queries = [q for q, s in stats.items() if s.total_impressions >= min_impressions]
    findings: list[CannibalizationFinding] = []
    seen: set[tuple[str, str]] = set()

    for i, q1 in enumerate(queries):
        t1 = tokenize(q1)
        s1 = stats[q1]
        for q2 in queries[i + 1 :]:
            if jaccard_similarity(t1, tokenize(q2)) < similarity_threshold:
                continue
            pair = tuple(sorted((q1, q2)))
            if pair in seen:
                continue
            seen.add(pair)
            s2 = stats[q2]
            if s1.best_url and s2.best_url and s1.best_url != s2.best_url:
                findings.append(
                    CannibalizationFinding(
                        keyword=q1,
                        recommendation="differentiate",
                        competing_urls=[
                            {"url": s1.best_url, "query": q1, "impressions": s1.best_url_impressions},
                            {"url": s2.best_url, "query": q2, "impressions": s2.best_url_impressions},
                        ],
                        evidence={
                            "source": "semantic_similarity",
                            "paired_query": q2,
                            "similarity": round(jaccard_similarity(t1, tokenize(q2)), 4),
                        },
                    )
                )
    return findings
