"""Post-publish analytics & learning loop.

Modeled after ContentFlow's analytics_agent.py + learning_agent.py.
Provides:
- Article performance grading (A/B/C/D/F)
- Cannibalization detection
- Refresh trigger checking
- Three-layer learning (L1 rules / L2 templates / L3 strategy)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any


# ── Performance grading ────────────────────────────────────────────────────

@dataclass
class ArticlePerformance:
    """Single article/post performance metrics."""
    article_id: str
    url: str
    title: str
    published_date: date | None = None

    # GSC metrics
    target_keyword: str = ""
    current_rank: float = 99.0
    rank_change_7d: float = 0.0  # positive = improved
    impressions_28d: int = 0
    clicks_28d: int = 0
    ctr: float = 0.0

    # AI analysis
    performance_grade: str = "C"  # A/B/C/D/F
    recommended_action: str = "maintain"
    action_reason: str = ""
    observation_signals: list[str] = field(default_factory=list)


@dataclass
class CannibalizationPair:
    """Two articles competing for the same keyword."""
    keyword: str
    article_ids: list[str] = field(default_factory=list)
    article_titles: list[str] = field(default_factory=list)
    article_urls: list[str] = field(default_factory=list)
    positions: list[float] = field(default_factory=list)
    suggestion: str = ""


@dataclass
class RefreshRecommendation:
    """Content refresh recommendation."""
    article_id: str
    article_title: str
    url: str
    trigger_reason: str
    priority: str  # high / medium / low
    current_rank: float | None = None
    previous_rank: float | None = None


# ── Performance grading logic ───────────────────────────────────────────────

def _compute_grade(rank: float, ctr: float, impressions: int) -> str:
    """Grade article performance A-F based on rank + CTR + impressions."""
    if impressions < 10:
        return "F"
    if rank <= 5 and ctr >= 0.08:
        return "A"
    if rank <= 10:
        return "B"
    if rank <= 20:
        return "C"
    if rank <= 50:
        return "D"
    return "F"


def _recommend_action(grade: str, rank_change: float, impressions: int) -> tuple[str, str]:
    """Recommend action based on grade and rank trend."""
    if grade == "A":
        return "maintain", "Top performer — monitor for competitor threats"
    if grade == "B":
        if rank_change < -3:  # dropping
            return "refresh", "Near top 3 but dropping — refresh to regain position"
        return "optimize", "Near top 3 — small optimizations could push to top"
    if grade == "C":
        if rank_change < -5:
            return "refresh", "Dropping from page 1-2 — needs content refresh"
        return "refresh", "Page 2 — highest ROI for content refresh"
    if grade == "D":
        if impressions > 100:
            return "rewrite", "Page 3+ with impressions — consider rewrite"
        return "analyze", "Page 3+ low impressions — diagnose issue"
    if grade == "F":
        if impressions == 0:
            return "investigate", "No impressions — check indexing/technical issues"
        return "deprioritize", "Very low performance — deprioritize or merge"
    return "maintain", ""


def grade_article_performance(
    *,
    keyword: str = "",
    rank: float = 99.0,
    rank_prev: float | None = None,
    impressions_28d: int = 0,
    clicks_28d: int = 0,
    ctr: float = 0.0,
) -> ArticlePerformance:
    """Grade a single article's performance."""
    rank_change = (rank_prev - rank) if rank_prev is not None else 0.0
    grade = _compute_grade(rank, ctr, impressions_28d)
    action, reason = _recommend_action(grade, rank_change, impressions_28d)

    signals: list[str] = []
    if rank <= 10:
        signals.append("page1_visible")
    if rank_change < -3:
        signals.append("ranking_declining")
    if ctr < 0.02 and impressions_28d > 50:
        signals.append("low_ctr_high_impressions")
    if impressions_28d > 500:
        signals.append("high_exposure_potential")

    return ArticlePerformance(
        article_id="",
        url="",
        title="",
        target_keyword=keyword,
        current_rank=rank,
        rank_change_7d=rank_change,
        impressions_28d=impressions_28d,
        clicks_28d=clicks_28d,
        ctr=ctr,
        performance_grade=grade,
        recommended_action=action,
        action_reason=reason,
        observation_signals=signals,
    )


# ── Cannibalization detection ──────────────────────────────────────────────

def detect_cannibalization(
    keyword_rankings: list[dict[str, Any]],
    *,
    position_threshold: float = 20.0,
) -> list[CannibalizationPair]:
    """Detect articles competing for the same keyword.

    Args:
        keyword_rankings: list of {keyword, article_id, title, url, position}
        position_threshold: only consider articles ranking <= this position

    Returns:
        List of CannibalizationPair for keywords with multiple ranking articles
    """
    by_keyword: dict[str, list[dict]] = {}
    for item in keyword_rankings:
        kw = item.get("keyword", "")
        pos = float(item.get("position", 99))
        if pos <= position_threshold:
            by_keyword.setdefault(kw, []).append(item)

    pairs: list[CannibalizationPair] = []
    for kw, items in by_keyword.items():
        if len(items) < 2:
            continue
        pairs.append(CannibalizationPair(
            keyword=kw,
            article_ids=[str(i.get("article_id", "")) for i in items],
            article_titles=[str(i.get("title", "")) for i in items],
            article_urls=[str(i.get("url", "")) for i in items],
            positions=[float(i.get("position", 99)) for i in items],
            suggestion=(
                f"Multiple pages ranking for '{kw}'. "
                f"Consider merging weaker pages into the strongest one "
                f"or differentiating their target keywords."
            ),
        ))
    return pairs


# ── Refresh trigger checking ───────────────────────────────────────────────

def check_refresh_triggers(
    performances: list[ArticlePerformance],
    *,
    rank_drop_threshold: float = 5.0,
    age_months_threshold: int = 6,
    today: date | None = None,
) -> list[RefreshRecommendation]:
    """Check which articles need content refresh.

    Triggers:
    1. Rank dropped >= rank_drop_threshold positions (high priority)
    2. Article age >= age_months_threshold + rank 10-30 (medium priority)
    3. Grade C with high impressions (medium priority)
    """
    today = today or date.today()
    recommendations: list[RefreshRecommendation] = []

    for perf in performances:
        # Trigger 1: Significant rank drop
        if perf.rank_change_7d <= -rank_drop_threshold:
            recommendations.append(RefreshRecommendation(
                article_id=perf.article_id,
                article_title=perf.title,
                url=perf.url,
                trigger_reason=f"Rank dropped {abs(perf.rank_change_7d):.1f} positions in 7 days",
                priority="high",
                current_rank=perf.current_rank,
            ))
            continue

        # Trigger 2: Aging content
        if perf.published_date:
            age_months = (today - perf.published_date).days / 30
            if age_months >= age_months_threshold and 10 <= perf.current_rank <= 30:
                recommendations.append(RefreshRecommendation(
                    article_id=perf.article_id,
                    article_title=perf.title,
                    url=perf.url,
                    trigger_reason=f"Content age {age_months:.0f} months, rank P{perf.current_rank:.0f}",
                    priority="medium",
                    current_rank=perf.current_rank,
                ))
                continue

        # Trigger 3: Grade C with high impressions
        if perf.performance_grade == "C" and perf.impressions_28d >= 200:
            recommendations.append(RefreshRecommendation(
                article_id=perf.article_id,
                article_title=perf.title,
                url=perf.url,
                trigger_reason=f"Grade C with {perf.impressions_28d} impressions — refresh could push to top 10",
                priority="medium",
                current_rank=perf.current_rank,
            ))

    return recommendations


# ── Three-layer learning ───────────────────────────────────────────────────

@dataclass
class PatternResult:
    """A discovered success pattern."""
    category: str
    pattern_text: str
    evidence_count: int
    metadata: dict = field(default_factory=dict)
    confidence_level: str = "unverified"  # unverified / verified / universal


@dataclass
class LearningReport:
    """L1 pattern learning report."""
    analyzed_articles: int
    patterns: list[PatternResult] = field(default_factory=list)
    low_performers: list[dict] = field(default_factory=list)


def analyze_success_patterns(
    performances: list[ArticlePerformance],
    *,
    article_metadata: dict[str, dict] | None = None,
) -> LearningReport:
    """Analyze what patterns correlate with high performance.

    L1 learning: extract rules from observed performance patterns.
    """
    meta = article_metadata or {}
    patterns: list[PatternResult] = []
    low_performers: list[dict] = []

    # Separate high and low performers
    high = [p for p in performances if p.performance_grade in ("A", "B")]
    low = [p for p in performances if p.performance_grade in ("D", "F")]

    for p in low:
        low_performers.append({
            "article_id": p.article_id,
            "title": p.title,
            "grade": p.performance_grade,
            "rank": p.current_rank,
            "impressions": p.impressions_28d,
        })

    # Pattern 1: FAQ presence vs rank
    if meta:
        faq_high = sum(1 for p in high if meta.get(p.article_id, {}).get("has_faq"))
        faq_low = sum(1 for p in low if meta.get(p.article_id, {}).get("has_faq"))
        if len(high) >= 3 and faq_high / max(len(high), 1) > faq_low / max(len(low), 1) + 0.2:
            patterns.append(PatternResult(
                category="faq_impact",
                pattern_text="Articles with FAQ sections tend to rank higher",
                evidence_count=faq_high,
                metadata={"faq_high_ratio": faq_high / max(len(high), 1)},
            ))

    # Pattern 2: Word count vs rank
    if meta:
        wc_high = [meta.get(p.article_id, {}).get("word_count", 0) for p in high]
        wc_low = [meta.get(p.article_id, {}).get("word_count", 0) for p in low]
        avg_high = sum(wc_high) / max(len(wc_high), 1)
        avg_low = sum(wc_low) / max(len(wc_low), 1)
        if avg_high > avg_low * 1.3 and len(high) >= 3:
            patterns.append(PatternResult(
                category="word_count_pattern",
                pattern_text=f"Longer articles (avg {avg_high:.0f} words) outperform shorter ones (avg {avg_low:.0f})",
                evidence_count=len(high),
                metadata={"avg_high_words": avg_high, "avg_low_words": avg_low},
            ))

    # Pattern 3: CTR vs impressions correlation
    high_ctr_articles = [p for p in performances if p.ctr >= 0.05 and p.impressions_28d >= 100]
    if len(high_ctr_articles) >= 3:
        patterns.append(PatternResult(
            category="ctr_threshold",
            pattern_text=f"CTR >= 5% with >= 100 impressions correlates with top rankings",
            evidence_count=len(high_ctr_articles),
        ))

    return LearningReport(
        analyzed_articles=len(performances),
        patterns=patterns,
        low_performers=low_performers,
    )


# ── Ranking tier classification ───────────────────────────────────────────

def classify_ranking_tiers(
    keyword_positions: list[dict[str, Any]],
) -> dict[str, list[dict]]:
    """Classify keywords into ranking tiers for action planning.

    Returns:
        Dict with keys: top3, top10, top20, top50, beyond50, unranked
    """
    tiers: dict[str, list[dict]] = {
        "top3": [], "top10": [], "top20": [], "top50": [], "beyond50": [], "unranked": [],
    }
    for item in keyword_positions:
        pos = float(item.get("position", 99))
        if pos <= 3:
            tiers["top3"].append(item)
        elif pos <= 10:
            tiers["top10"].append(item)
        elif pos <= 20:
            tiers["top20"].append(item)
        elif pos <= 50:
            tiers["top50"].append(item)
        elif pos < 99:
            tiers["beyond50"].append(item)
        else:
            tiers["unranked"].append(item)
    return tiers
