"""Brand mention detection and AI visibility scoring."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BrandVisibilityMetrics:
    visibility_score: float
    total_runs: int
    our_brand_mention_rate: float
    our_url_citation_rate: float
    competitor_mention_rate: float


def collect_brand_names(
    canonical_name: str | None,
    aliases: list[str] | None,
    site_name: str | None = None,
) -> set[str]:
    names: set[str] = set()
    for value in [canonical_name, site_name, *(aliases or [])]:
        if isinstance(value, str) and value.strip():
            names.add(value.strip())
    return names


def detect_mentioned_brands(
    answer_text: str,
    explicit_brands: list[str] | None,
    known_brands: set[str],
) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    lower_answer = answer_text.lower()
    for brand in list(explicit_brands or []) + sorted(known_brands, key=len, reverse=True):
        if not isinstance(brand, str) or not brand.strip():
            continue
        key = brand.strip()
        if key.lower() in lower_answer and key not in seen:
            seen.add(key)
            found.append(key)
    return found


def classify_competitor_mentions(
    mentioned_brands: list[str],
    our_brand_names: set[str],
    competitor_names: dict[str, str],
) -> list[dict]:
    """Return competitor mentions as {name, domain} dicts."""
    results: list[dict] = []
    our_lower = {n.lower() for n in our_brand_names}
    for brand in mentioned_brands:
        if brand.lower() in our_lower:
            continue
        domain = competitor_names.get(brand.lower())
        if domain:
            results.append({"name": brand, "domain": domain})
    return results


def compute_visibility_metrics(runs: list) -> BrandVisibilityMetrics:
    if not runs:
        return BrandVisibilityMetrics(
            visibility_score=0.0,
            total_runs=0,
            our_brand_mention_rate=0.0,
            our_url_citation_rate=0.0,
            competitor_mention_rate=0.0,
        )
    total = len(runs)
    brand_hits = sum(1 for r in runs if r.our_brand_mentioned)
    url_hits = sum(1 for r in runs if r.our_url_cited)
    competitor_hits = sum(1 for r in runs if r.competitor_mentions_json)
    visible = sum(1 for r in runs if r.our_brand_mentioned or r.our_url_cited)
    return BrandVisibilityMetrics(
        visibility_score=round(100.0 * visible / total, 2),
        total_runs=total,
        our_brand_mention_rate=round(100.0 * brand_hits / total, 2),
        our_url_citation_rate=round(100.0 * url_hits / total, 2),
        competitor_mention_rate=round(100.0 * competitor_hits / total, 2),
    )
