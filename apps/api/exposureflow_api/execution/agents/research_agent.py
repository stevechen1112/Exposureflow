"""Research Agent: SERP analysis + competitor depth + keyword extraction.

Modeled after ContentFlow's research_agent.py.
For each target keyword, performs:
1. SERP fetch (via existing connectors/serp)
2. Competitor content depth analysis (H2 structure, word count, FAQ presence)
3. PAA question extraction
4. Related search extraction
5. Builds structured SerpIntelligence for downstream agents
"""

from __future__ import annotations

import asyncio
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

import httpx
from loguru import logger

from exposureflow_api.config import settings

SKIP_DOMAINS = {
    "youtube.com", "youtu.be", "facebook.com", "instagram.com",
    "twitter.com", "x.com", "wikipedia.org", "google.com",
    "line.me", "amazon.com", "shopee.tw",
}


@dataclass
class CompetitorDepth:
    """Lightweight competitor page analysis."""
    url: str
    h2_headings: list[str] = field(default_factory=list)
    estimated_word_count: int = 0
    has_faq: bool = False
    has_table: bool = False
    has_schema: bool = False


@dataclass
class ContentPatternSignals:
    """Aggregated content patterns from competitor analysis."""
    avg_word_count: int = 0
    faq_presence_rate: float = 0.0
    table_presence_rate: float = 0.0
    avg_h2_count: float = 0.0


@dataclass
class SerpIntelligence:
    """Structured SERP intelligence for downstream agents."""
    query: str
    top_results: list[dict[str, Any]] = field(default_factory=list)
    paa_questions: list[str] = field(default_factory=list)
    related_searches: list[str] = field(default_factory=list)
    competitor_depth: list[CompetitorDepth] = field(default_factory=list)
    content_patterns: ContentPatternSignals = field(default_factory=ContentPatternSignals)
    heading_patterns: list[str] = field(default_factory=list)
    top_intent: str = "informational"
    difficulty_hint: str = "medium"
    paa_count: int = 0
    related_search_count: int = 0


@dataclass
class ResearchReport:
    """Complete research output for one keyword."""
    keyword: str
    serp_intelligence: SerpIntelligence
    extracted_keywords: list[str] = field(default_factory=list)
    recommended_angle: str = ""
    content_gaps: list[str] = field(default_factory=list)


async def _fetch_competitor_depth(url: str) -> CompetitorDepth | None:
    """Lightweight crawl of a single competitor URL."""
    try:
        domain = urlparse(url).netloc.lstrip("www.")
        if any(domain.endswith(skip) for skip in SKIP_DOMAINS):
            return None

        async with httpx.AsyncClient(
            timeout=8.0,
            headers={"User-Agent": "Mozilla/5.0 (compatible; ExposureFlowBot/1.0)"},
            follow_redirects=True,
        ) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return None
            html = resp.text

        # Extract H2 headings
        h2_pattern = re.compile(r"<h2[^>]*>(.*?)</h2>", re.IGNORECASE | re.DOTALL)
        h2_raw = h2_pattern.findall(html)
        h2_headings = [re.sub(r"<[^>]+>", "", h).strip() for h in h2_raw if h.strip()][:10]

        # Estimate word count
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text)
        cjk_count = len(re.findall(r"[\u4e00-\u9fff]", text))
        eng_words = len(re.findall(r"[a-zA-Z]+", text))
        estimated_word_count = cjk_count + eng_words // 2

        # FAQ presence
        has_faq = bool(
            re.search(r"(常見問題|FAQ|Q&A|q&a|<details)", html, re.IGNORECASE)
            or any("常見問題" in h or "FAQ" in h.upper() for h in h2_headings)
        )

        # Table presence
        has_table = bool(re.search(r"<table", html, re.IGNORECASE))

        # Schema presence
        has_schema = bool(re.search(r'application/ld\+json', html, re.IGNORECASE))

        return CompetitorDepth(
            url=url,
            h2_headings=h2_headings,
            estimated_word_count=estimated_word_count,
            has_faq=has_faq,
            has_table=has_table,
            has_schema=has_schema,
        )
    except Exception:
        return None


async def _fetch_competitor_depths(urls: list[str], max_competitors: int = 3) -> list[CompetitorDepth]:
    """Parallel fetch competitor depths."""
    tasks = [_fetch_competitor_depth(url) for url in urls[:max_competitors + 2]]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    depths = []
    for r in results:
        if isinstance(r, CompetitorDepth):
            depths.append(r)
            if len(depths) >= max_competitors:
                break
    return depths


def _build_serp_intelligence(
    query: str,
    organic_results: list[dict[str, Any]],
    paa_questions: list[str],
    related_searches: list[str],
    competitor_depth: list[CompetitorDepth],
) -> SerpIntelligence:
    """Build structured SerpIntelligence from raw SERP data."""
    # Infer top intent
    top_intent = "informational"
    titles_combined = " ".join(r.get("title", "") for r in organic_results[:5]).lower()
    if any(w in titles_combined for w in ("購買", "price", "buy", "推薦", "最好", "比較", "評價", "價格", "費用")):
        top_intent = "commercial"
    elif any(w in titles_combined for w in ("官網", "登入", "登录", "shop")):
        top_intent = "navigational"

    # Content patterns from competitor depth
    patterns = ContentPatternSignals()
    if competitor_depth:
        word_counts = [d.estimated_word_count for d in competitor_depth if d.estimated_word_count > 0]
        patterns.avg_word_count = int(sum(word_counts) / len(word_counts)) if word_counts else 0
        patterns.faq_presence_rate = sum(1 for d in competitor_depth if d.has_faq) / len(competitor_depth)
        patterns.table_presence_rate = sum(1 for d in competitor_depth if d.has_table) / len(competitor_depth)
        h2_counts = [len(d.h2_headings) for d in competitor_depth]
        patterns.avg_h2_count = sum(h2_counts) / len(h2_counts) if h2_counts else 0.0

    # Heading patterns
    all_h2s: list[str] = []
    for d in competitor_depth:
        all_h2s.extend(d.h2_headings)
    counter = Counter(h.strip() for h in all_h2s if h.strip())
    heading_patterns = [h for h, _ in counter.most_common(8)]

    # Difficulty hint
    difficulty_hint = "medium"
    if competitor_depth:
        avg_wc = patterns.avg_word_count
        n_comp = len(organic_results)
        if avg_wc > 3000 or n_comp >= 9:
            difficulty_hint = "high"
        elif avg_wc < 800 or n_comp <= 4:
            difficulty_hint = "low"

    return SerpIntelligence(
        query=query,
        top_results=organic_results[:10],
        paa_questions=paa_questions,
        related_searches=related_searches,
        competitor_depth=competitor_depth,
        content_patterns=patterns,
        heading_patterns=heading_patterns,
        top_intent=top_intent,
        difficulty_hint=difficulty_hint,
        paa_count=len(paa_questions),
        related_search_count=len(related_searches),
    )


def _extract_keywords_from_serp(
    serp: SerpIntelligence,
    top_n: int = 30,
) -> list[str]:
    """Extract high-frequency semantic keywords from SERP results.

    Uses simple bigram/trigram extraction for Chinese text.
    """
    STOPWORDS_ZH = {
        "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都",
        "一", "一個", "上", "也", "很", "到", "說", "要", "去", "你", "會",
        "著", "沒有", "看", "好", "自己", "這", "那", "什麼", "對", "中",
        "以", "時", "可以", "可", "但", "如果", "因為", "所以", "而且",
        "來", "個", "為", "與", "或", "及", "等", "被", "從", "而",
        "最", "更", "讓", "把", "能", "其", "他", "她", "它",
        "這個", "那個", "如何", "怎麼", "哪些", "為什麼",
        "透過", "進行", "使用", "需要", "包括", "提供", "相關",
    }

    text_corpus = " ".join(
        f"{r.get('title', '')} {r.get('snippet', '')}"
        for r in serp.top_results
    )
    paa_text = " ".join(serp.paa_questions)
    full_text = f"{text_corpus} {paa_text}"

    # Simple bigram + trigram for Chinese
    text = re.sub(r"<[^>]+>", "", full_text)
    text = re.sub(r"[^\u4e00-\u9fff\w\s]", " ", text)

    tokens: list[str] = []
    for i in range(len(text) - 1):
        chunk = text[i:i+2].strip()
        if len(chunk) == 2:
            tokens.append(chunk)
    for i in range(len(text) - 2):
        chunk = text[i:i+3].strip()
        if len(chunk) == 3:
            tokens.append(chunk)

    filtered = [w for w in tokens if w not in STOPWORDS_ZH and len(w) >= 2]
    counter = Counter(filtered)
    return [word for word, _ in counter.most_common(top_n)]


def _identify_content_gaps(
    serp: SerpIntelligence,
    own_coverage: list[str] | None = None,
) -> list[str]:
    """Identify content gaps compared to competitors."""
    gaps: list[str] = []

    # PAA questions not covered
    if serp.paa_questions:
        gaps.append(f"PAA questions to cover: {len(serp.paa_questions)} questions available")

    # Heading patterns not in own content
    if serp.heading_patterns and own_coverage:
        missing = [h for h in serp.heading_patterns[:5] if h not in own_coverage]
        if missing:
            gaps.append(f"Missing H2 topics: {', '.join(missing)}")

    # Format gaps
    if serp.content_patterns.faq_presence_rate > 0.5:
        gaps.append("Competitors use FAQ format — consider adding FAQ section")
    if serp.content_patterns.table_presence_rate > 0.3:
        gaps.append("Competitors use tables — consider adding comparison table")

    # Word count gap
    if serp.content_patterns.avg_word_count > 2000:
        gaps.append(f"Competitor avg word count: {serp.content_patterns.avg_word_count} — ensure depth")

    return gaps


async def run_research_agent(
    keyword: str,
    *,
    serp_slots: list[dict[str, Any]] | None = None,
    serp_raw_json: dict[str, Any] | None = None,
    own_coverage: list[str] | None = None,
) -> ResearchReport:
    """Run the Research Agent for a single keyword.

    Args:
        keyword: target keyword to research
        serp_slots: pre-fetched SERP slots (from serp_query_snapshots)
        serp_raw_json: raw SERP provider response
        own_coverage: list of topics already covered by own site

    Returns:
        ResearchReport with full SERP intelligence
    """
    # Extract organic results from slots
    organic_results: list[dict[str, Any]] = []
    paa_questions: list[str] = []
    related_searches: list[str] = []

    if serp_slots:
        for slot in serp_slots:
            if slot.get("slot_type") == "organic":
                organic_results.append({
                    "title": slot.get("title", ""),
                    "snippet": slot.get("snippet", ""),
                    "url": slot.get("url", ""),
                    "domain": slot.get("owner_domain", ""),
                    "position": slot.get("position"),
                })
            elif slot.get("slot_type") == "paa":
                q = slot.get("title", "")
                if q:
                    paa_questions.append(q)

    if serp_raw_json:
        # Extract PAA from raw JSON
        paa_key = "peopleAlsoAsk" if "peopleAlsoAsk" in serp_raw_json else "related_questions"
        for item in serp_raw_json.get(paa_key, []):
            q = item.get("question") or item.get("title", "")
            if q and q not in paa_questions:
                paa_questions.append(q)

        # Extract related searches
        rs_key = "relatedSearches" if "relatedSearches" in serp_raw_json else "related_searches"
        for item in serp_raw_json.get(rs_key, []):
            q = item.get("query", "")
            if q:
                related_searches.append(q)

    # Fetch competitor depths
    competitor_urls = [r.get("url", "") for r in organic_results if r.get("url")]
    competitor_depth = await _fetch_competitor_depths(competitor_urls)

    # Build intelligence
    serp_intel = _build_serp_intelligence(
        keyword, organic_results, paa_questions, related_searches, competitor_depth
    )

    # Extract keywords
    extracted_kw = _extract_keywords_from_serp(serp_intel)

    # Identify gaps
    gaps = _identify_content_gaps(serp_intel, own_coverage)

    # Recommend angle
    angle = _recommend_angle(serp_intel)

    return ResearchReport(
        keyword=keyword,
        serp_intelligence=serp_intel,
        extracted_keywords=extracted_kw,
        recommended_angle=angle,
        content_gaps=gaps,
    )


def _recommend_angle(serp: SerpIntelligence) -> str:
    """Recommend a content angle based on SERP intelligence."""
    if serp.difficulty_hint == "low" and serp.top_intent == "informational":
        return "comprehensive_guide"
    if serp.top_intent == "commercial":
        return "comparison_with_recommendations"
    if serp.paa_count >= 5:
        return "faq_driven_with_deep_answers"
    if serp.content_patterns.avg_word_count > 2500:
        return "in_depth_with_original_insights"
    return "standard_educational"
