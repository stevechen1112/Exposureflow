"""Keyword opportunity scoring engine.

Implements the five-factor exposure opportunity model from
organic-impressions-seo-plan.md:

    exposure_opportunity_score
    = search_volume_potential
    x ranking_feasibility
    x serp_slot_diversity
    x ai_citation_potential
    x topic_cluster_contribution

Also implements the three-tier priority classification:
    P1 (immediate): low competition + clear intent + achievable
    P2 (this quarter): medium competition, needs authority building
    P3 (long-term): high competition, needs E-E-A-T accumulation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ── Scoring constants ──────────────────────────────────────────────────────

# Search volume tiers (monthly searches, estimated)
VOLUME_TIERS: dict[str, tuple[int, int, float]] = {
    "very_high": (3000, 999_999, 1.0),
    "high": (1000, 2999, 0.85),
    "medium": (300, 999, 0.65),
    "low": (100, 299, 0.40),
    "very_low": (10, 99, 0.20),
    "negligible": (0, 9, 0.05),
}

# Competition difficulty tiers (based on competitor domain strength)
DIFFICULTY_TIERS: dict[str, tuple[float, str]] = {
    "very_low": (1.0, "P1 — immediate execution"),
    "low": (0.85, "P1 — immediate execution"),
    "medium": (0.60, "P2 — this quarter"),
    "high": (0.35, "P3 — long-term layout"),
    "very_high": (0.15, "P3 — requires E-E-A-T first"),
}

# SERP slot type weights for diversity scoring
SLOT_TYPE_WEIGHTS: dict[str, float] = {
    "featured_snippet": 0.30,
    "paa": 0.20,
    "image": 0.15,
    "video": 0.15,
    "product": 0.10,
    "ai_overview": 0.25,
    "related_search": 0.10,
    "organic": 0.05,  # baseline, always present
}

# AI citation potential factors
AI_CITATION_FACTORS: dict[str, float] = {
    "has_original_data": 0.30,
    "has_clear_structure": 0.20,
    "has_authoritative_sources": 0.25,
    "has_faq_format": 0.15,
    "has_brand_entity_match": 0.10,
}


@dataclass
class KeywordScoreInput:
    """Raw inputs for scoring a single keyword."""

    keyword: str
    node_type: str  # pillar / cluster / long_tail / faq / comparison
    intent: str | None  # informational / commercial / transactional

    # Search volume
    estimated_monthly_searches: int = 0
    volume_source: str = "none"  # serper / serpapi / gsc / manual / none

    # Competition
    competitor_domain_count: int = 0
    avg_competitor_da: float = 0.0  # estimated domain authority 0-100
    top10_has_strong_domains: bool = False  # wikipedia, gov, major brands

    # SERP features present for this keyword
    serp_features_present: list[str] = field(default_factory=list)
    # e.g. ["featured_snippet", "paa", "image", "ai_overview"]

    # AI citation signals
    ai_overview_present: bool = False
    ai_citation_signals: list[str] = field(default_factory=list)

    # Topic cluster
    topic_cluster_id: str | None = None
    topic_cluster_coverage: float = 0.0  # 0-1, how much of cluster is covered
    pillar_has_page: bool = False

    # Existing performance (from GSC)
    gsc_impressions_28d: int = 0
    gsc_clicks_28d: int = 0
    gsc_avg_position: float = 99.0

    # Business fit
    business_fit_status: str = "needs_review"  # in_scope / needs_review / out_of_scope
    is_approved: bool = False


@dataclass
class KeywordScoreResult:
    """Scored keyword with all factor breakdowns."""

    keyword: str
    total_score: float  # 0.0 - 1.0

    # Factor scores (each 0.0 - 1.0)
    volume_score: float
    feasibility_score: float
    serp_diversity_score: float
    ai_citation_score: float
    topic_contribution_score: float

    # Priority classification
    priority_tier: str  # P1 / P2 / P3
    priority_label: str  # human-readable

    # Evidence
    evidence: dict[str, Any] = field(default_factory=dict)


def _score_volume(estimated_monthly: int) -> float:
    """Score search volume potential 0.0-1.0."""
    for tier, (lo, hi, score) in VOLUME_TIERS.items():
        if lo <= estimated_monthly <= hi:
            return score
    return 0.05


def _score_feasibility(
    competitor_count: int,
    avg_da: float,
    has_strong_domains: bool,
    gsc_avg_position: float,
) -> float:
    """Score ranking feasibility 0.0-1.0.

    Higher = easier to rank. Considers competitor strength and
    existing position as a baseline signal.
    """
    # If we already rank well, feasibility is high
    if gsc_avg_position <= 10:
        return 0.95
    if gsc_avg_position <= 20:
        return 0.75

    # Start from competitor analysis
    base = 0.70

    # Many competitors reduce feasibility
    if competitor_count >= 8:
        base -= 0.25
    elif competitor_count >= 5:
        base -= 0.15
    elif competitor_count <= 2:
        base += 0.10

    # Strong domains reduce feasibility
    if has_strong_domains:
        base -= 0.15

    # High average DA reduces feasibility
    if avg_da >= 60:
        base -= 0.20
    elif avg_da >= 40:
        base -= 0.10
    elif avg_da <= 20:
        base += 0.10

    return max(0.05, min(1.0, base))


def _score_serp_diversity(features_present: list[str]) -> float:
    """Score SERP slot diversity 0.0-1.0.

    More diverse SERP features = more exposure opportunities.
    """
    if not features_present:
        return 0.10  # only organic

    total_weight = sum(
        SLOT_TYPE_WEIGHTS.get(f, 0.05) for f in features_present
    )
    # Cap at 1.0, normalize to 0-1 range
    return min(1.0, total_weight)


def _score_ai_citation(
    ai_overview_present: bool,
    citation_signals: list[str],
) -> float:
    """Score AI citation potential 0.0-1.0."""
    base = 0.10

    if ai_overview_present:
        base += 0.30  # AI overview exists for this query = high potential

    for signal in citation_signals:
        base += AI_CITATION_FACTORS.get(signal, 0.05)

    return min(1.0, base)


def _score_topic_contribution(
    node_type: str,
    cluster_coverage: float,
    pillar_has_page: bool,
) -> float:
    """Score topic cluster contribution 0.0-1.0.

    Keywords that fill gaps in under-covered clusters score higher.
    """
    base = 0.50

    # Pillar keywords are foundational
    if node_type == "pillar":
        base += 0.20
        if not pillar_has_page:
            base += 0.15  # missing pillar = urgent gap

    # Low coverage = high contribution value
    if cluster_coverage < 0.3:
        base += 0.20
    elif cluster_coverage < 0.6:
        base += 0.10
    elif cluster_coverage >= 0.9:
        base -= 0.10  # already well-covered

    return max(0.05, min(1.0, base))


def _classify_priority(total_score: float, feasibility_score: float) -> tuple[str, str]:
    """Classify into P1/P2/P3 tiers.

    Uses the scaled score (0-100) for classification.
    """
    # total_score is already scaled 0-100
    if feasibility_score >= 0.70 and total_score >= 30:
        return "P1", "P1 — immediate execution (high feasibility, good opportunity)"
    if feasibility_score >= 0.40 and total_score >= 15:
        return "P2", "P2 — this quarter (medium feasibility, build authority)"
    return "P3", "P3 — long-term layout (needs E-E-A-T accumulation)"


def score_keyword(inputs: KeywordScoreInput) -> KeywordScoreResult:
    """Score a single keyword for exposure opportunity.

    Returns a KeywordScoreResult with factor breakdowns and priority.
    """
    volume_score = _score_volume(inputs.estimated_monthly_searches)
    feasibility_score = _score_feasibility(
        inputs.competitor_domain_count,
        inputs.avg_competitor_da,
        inputs.top10_has_strong_domains,
        inputs.gsc_avg_position,
    )
    serp_diversity_score = _score_serp_diversity(inputs.serp_features_present)
    ai_citation_score = _score_ai_citation(
        inputs.ai_overview_present,
        inputs.ai_citation_signals,
    )
    topic_contribution_score = _score_topic_contribution(
        inputs.node_type,
        inputs.topic_cluster_coverage,
        inputs.pillar_has_page,
    )

    # Geometric mean of five factors (more forgiving than pure product)
    # This preserves the multiplicative relationship while normalizing
    import math
    factors = [
        max(0.01, volume_score),
        max(0.01, feasibility_score),
        max(0.01, serp_diversity_score),
        max(0.01, ai_citation_score),
        max(0.01, topic_contribution_score),
    ]
    product = 1.0
    for f in factors:
        product *= f
    total = math.pow(product, 1.0 / 5.0)  # geometric mean

    # Scale up for readability (0-100 internally)
    total_scaled = round(total * 100, 1)

    priority_tier, priority_label = _classify_priority(total_scaled, feasibility_score)

    return KeywordScoreResult(
        keyword=inputs.keyword,
        total_score=total_scaled,
        volume_score=round(volume_score, 2),
        feasibility_score=round(feasibility_score, 2),
        serp_diversity_score=round(serp_diversity_score, 2),
        ai_citation_score=round(ai_citation_score, 2),
        topic_contribution_score=round(topic_contribution_score, 2),
        priority_tier=priority_tier,
        priority_label=priority_label,
        evidence={
            "estimated_monthly_searches": inputs.estimated_monthly_searches,
            "volume_source": inputs.volume_source,
            "competitor_domain_count": inputs.competitor_domain_count,
            "avg_competitor_da": inputs.avg_competitor_da,
            "serp_features_present": inputs.serp_features_present,
            "ai_overview_present": inputs.ai_overview_present,
            "gsc_impressions_28d": inputs.gsc_impressions_28d,
            "gsc_avg_position": inputs.gsc_avg_position,
            "scoring_model": "five_factor_multiplicative_v1",
        },
    )


def score_keywords_batch(
    inputs: list[KeywordScoreInput],
) -> list[KeywordScoreResult]:
    """Score multiple keywords and return sorted by total_score descending."""
    results = [score_keyword(inp) for inp in inputs]
    results.sort(key=lambda r: r.total_score, reverse=True)
    return results


def extract_serp_features_from_slots(
    slots: list[dict[str, Any]],
) -> list[str]:
    """Extract SERP feature types present from slot data.

    Used to feed into KeywordScoreInput.serp_features_present.
    """
    features: set[str] = set()
    for slot in slots:
        slot_type = slot.get("slot_type", "")
        if slot_type:
            features.add(slot_type)
    return sorted(features)


def estimate_search_volume_from_serp(
    raw_json: dict[str, Any],
) -> int:
    """Estimate monthly search volume from SERP provider raw JSON.

    Serper.dev sometimes includes searchVolume in the response.
    SerpAPI includes search_volume in keyword_data.
    Falls back to impression-based estimation.
    """
    # Try Serper format
    sv = raw_json.get("searchVolume") or raw_json.get("search_volume")
    if sv and isinstance(sv, (int, float)) and sv > 0:
        return int(sv)

    # Try SerpAPI format
    kd = raw_json.get("search_metadata", {}) or raw_json.get("search_information", {})
    sv = kd.get("total_results") or kd.get("search_volume")
    if sv and isinstance(sv, (int, float)):
        # total_results is not monthly searches, but gives scale
        if sv > 1_000_000_000:
            return 5000  # very high
        if sv > 100_000_000:
            return 2000
        if sv > 10_000_000:
            return 800
        if sv > 1_000_000:
            return 300
        return 100

    # Fallback: estimate from organic result count
    organic = raw_json.get("organic", []) or raw_json.get("organic_results", [])
    if len(organic) >= 10:
        return 200  # full page = at least moderate volume
    if len(organic) >= 5:
        return 80
    return 30


def estimate_competition_from_slots(
    slots: list[dict[str, Any]],
) -> tuple[int, float, bool]:
    """Estimate competition level from SERP slots.

    Returns:
        competitor_count: number of distinct competitor domains
        avg_da_estimate: rough domain authority estimate 0-100
        has_strong_domains: whether top 10 includes wikipedia/gov/major brands
    """
    STRONG_DOMAINS = {
        "wikipedia.org", "amazon.com", "google.com",
        "facebook.com", "youtube.com", "microsoft.com",
        "apple.com", "nih.gov", "mayoclinic.org",
        "webmd.com", "healthline.com", "shopee.tw",
        "momoshop.com.tw", "pchome.com.tw",
    }

    competitor_domains: set[str] = set()
    for slot in slots:
        if slot.get("slot_type") != "organic":
            continue
        domain = slot.get("owner_domain", "")
        if domain and not slot.get("is_own_site"):
            competitor_domains.add(domain)

    has_strong = any(
        any(d.endswith(sd) or d == sd for sd in STRONG_DOMAINS)
        for d in competitor_domains
    )

    # Rough DA estimate based on count and strong presence
    count = len(competitor_domains)
    if count <= 2:
        avg_da = 15.0
    elif count <= 5:
        avg_da = 30.0
    elif count <= 8:
        avg_da = 45.0
    else:
        avg_da = 60.0

    if has_strong:
        avg_da = min(80.0, avg_da + 20)

    return count, avg_da, has_strong
