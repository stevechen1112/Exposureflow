"""Extract executable keyword candidates from Strategy Intake text."""

from __future__ import annotations

import re
from dataclasses import dataclass

from exposureflow_api.models.strategy import BusinessIntake
from exposureflow_api.strategy.keyword_utils import normalize_keyword

QUOTE_PATTERNS = (
    re.compile(r"「([^」]+)」"),
    re.compile(r'"([^"]+)"'),
    re.compile(r"'([^']+)'"),
)

STRATEGY_NOISE = (
    "自然搜尋曝光",
    "自然搜尋",
    "搜尋曝光",
    "成為區域第一",
    "成為第一",
    "區域第一",
    "提升",
    "提高",
    "增加",
    "能見度",
    "曝光",
    "排名",
    "等服務詞",
    "等關鍵字",
    "等關鍵詞",
    "目標",
    "策略",
)

SERVICE_HINTS = (
    "紗窗",
    "紗窗維修",
    "紗窗修理",
    "紗窗安裝",
    "紗窗清洗",
    "換紗窗",
    "修紗窗",
    "維修",
    "修理",
    "安裝",
    "清洗",
    "價格",
    "費用",
    "報價",
    "推薦",
    "保固",
)

MIN_REGION_SERVICE_LEN = 4
REGION_MARKERS = ("市", "縣", "區", "鄉", "鎮", "里", "部分")
QUESTION_MARKERS = ("嗎", "如何", "怎麼", "什麼", "多少", "?", "？")
COMPARISON_MARKERS = ("比較", "vs", "VS")

COMMERCIAL_HINTS = ("價格", "費用", "多少", "報價", "價錢", "cost", "price")
INFORMATIONAL_HINTS = ("如何", "是什麼", "怎麼", "方法", "步驟", "教學")

MAX_KEYWORD_LEN = 24
MIN_KEYWORD_LEN = 2


@dataclass(frozen=True)
class ExtractedKeywordCandidate:
    keyword: str
    node_type: str
    intent: str | None
    source: str
    source_text: str
    confidence: float


def _unique_strings(values: list | None) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in values or []:
        text = str(raw).strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
    return out


def _extract_quoted_phrases(text: str) -> list[str]:
    phrases: list[str] = []
    for pattern in QUOTE_PATTERNS:
        for match in pattern.findall(text):
            phrase = str(match).strip()
            if phrase:
                phrases.append(phrase)
    return phrases


def _strip_strategy_noise(text: str) -> str:
    cleaned = text.strip()
    for noise in STRATEGY_NOISE:
        cleaned = cleaned.replace(noise, " ")
    return " ".join(cleaned.split())


def _looks_like_sentence(text: str) -> bool:
    if len(text) > MAX_KEYWORD_LEN:
        return True
    sentence_markers = ("成為", "提升", "提高", "目標", "策略", "自然搜尋", "能見度", "不做", "排除")
    return any(marker in text for marker in sentence_markers)


def _infer_intent(keyword: str) -> str | None:
    lowered = keyword.lower()
    if any(hint in lowered for hint in COMMERCIAL_HINTS):
        return "commercial"
    if any(hint in lowered for hint in INFORMATIONAL_HINTS):
        return "informational"
    return None


def _infer_node_type(keyword: str) -> str:
    if any(marker in keyword for marker in QUESTION_MARKERS):
        return "faq"
    if any(marker in keyword for marker in COMPARISON_MARKERS):
        return "comparison"
    if any(hint in keyword for hint in COMMERCIAL_HINTS) or len(keyword) >= 10:
        return "long_tail"
    if len(keyword) <= 6:
        return "pillar"
    return "cluster"


def _service_terms(*texts: str | None) -> list[str]:
    terms: list[str] = []
    for text in texts:
        if not text:
            continue
        for hint in sorted(SERVICE_HINTS, key=len, reverse=True):
            if hint in text and hint not in terms:
                terms.append(hint)
                break
    return [term for term in terms if len(term) >= 2]


def _looks_like_region(region: str) -> bool:
    region = region.strip()
    if len(region) < 2:
        return False
    return any(marker in region for marker in REGION_MARKERS) or region.endswith(("台中", "台北", "高雄", "彰化"))


def _region_service_candidates(
    regions: list[str],
    services: list[str],
    *,
    source_text: str,
) -> list[ExtractedKeywordCandidate]:
    candidates: list[ExtractedKeywordCandidate] = []
    for region in regions:
        region = region.strip()
        if not region or not _looks_like_region(region):
            continue
        for service in services:
            if len(service) < 2:
                continue
            keyword = f"{region}{service}".strip()
            if len(keyword) < MIN_REGION_SERVICE_LEN or _looks_like_sentence(keyword):
                continue
            candidates.append(
                ExtractedKeywordCandidate(
                    keyword=keyword,
                    node_type="cluster",
                    intent=_infer_intent(keyword),
                    source="market_service",
                    source_text=source_text,
                    confidence=0.65,
                )
            )
    return candidates


def _candidate_from_phrase(
    phrase: str,
    *,
    source: str,
    source_text: str,
    confidence: float,
) -> ExtractedKeywordCandidate | None:
    keyword = phrase.strip()
    if len(keyword) < MIN_KEYWORD_LEN or len(keyword) > MAX_KEYWORD_LEN:
        return None
    if _looks_like_sentence(keyword):
        return None
    return ExtractedKeywordCandidate(
        keyword=keyword,
        node_type=_infer_node_type(keyword),
        intent=_infer_intent(keyword),
        source=source,
        source_text=source_text,
        confidence=confidence,
    )


def extract_keyword_candidates(intake: BusinessIntake) -> list[ExtractedKeywordCandidate]:
    """Turn intake strategy text into reviewable keyword candidates."""
    candidates: list[ExtractedKeywordCandidate] = []
    regions = _unique_strings(intake.sales_regions_json)
    services = _service_terms(intake.company_summary, " ".join(intake.strategic_goals_json or []))

    for goal in _unique_strings(intake.strategic_goals_json):
        for phrase in _extract_quoted_phrases(goal):
            item = _candidate_from_phrase(
                phrase,
                source="quoted_phrase",
                source_text=goal,
                confidence=0.95,
            )
            if item:
                candidates.append(item)

        cleaned = _strip_strategy_noise(goal)
        if cleaned and not _looks_like_sentence(cleaned):
            item = _candidate_from_phrase(
                cleaned,
                source="goal_phrase",
                source_text=goal,
                confidence=0.7,
            )
            if item:
                candidates.append(item)

    if intake.company_summary:
        for phrase in _extract_quoted_phrases(intake.company_summary):
            item = _candidate_from_phrase(
                phrase,
                source="company_summary",
                source_text=intake.company_summary,
                confidence=0.85,
            )
            if item:
                candidates.append(item)

    candidates.extend(
        _region_service_candidates(
            regions,
            services,
            source_text=" / ".join(regions),
        )
    )

    deduped: dict[str, ExtractedKeywordCandidate] = {}
    for item in candidates:
        key = normalize_keyword(item.keyword)
        if not key:
            continue
        existing = deduped.get(key)
        if existing is None or item.confidence > existing.confidence:
            deduped[key] = item
    return list(deduped.values())


def assign_parent_ids(candidates: list[ExtractedKeywordCandidate]) -> list[dict]:
    """Return candidate payloads with optional parent_keyword hints for hierarchy."""
    pillars = [c for c in candidates if c.node_type == "pillar"]
    rows: list[dict] = []
    for candidate in sorted(candidates, key=lambda c: (-c.confidence, c.keyword)):
        parent_keyword: str | None = None
        if candidate.node_type in ("cluster", "long_tail"):
            for pillar in pillars:
                if pillar.keyword in candidate.keyword or candidate.keyword in pillar.keyword:
                    parent_keyword = pillar.keyword
                    break
        rows.append(
            {
                "keyword": candidate.keyword,
                "node_type": candidate.node_type,
                "intent": candidate.intent,
                "business_fit_status": "needs_review",
                "reason": candidate.source,
                "source_text": candidate.source_text,
                "confidence": candidate.confidence,
                "parent_keyword": parent_keyword,
            }
        )
    return rows
