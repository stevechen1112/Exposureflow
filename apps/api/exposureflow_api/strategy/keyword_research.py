"""SERP-driven keyword research helpers for cold-start and enrichment."""

from __future__ import annotations

import re
from dataclasses import dataclass

from exposureflow_api.strategy.keyword_enrichment import enrichment_from_serp
from exposureflow_api.strategy.keyword_utils import normalize_keyword

MAX_KEYWORD_LEN = 48
MIN_KEYWORD_LEN = 2
QUESTION_MARKERS = ("嗎", "如何", "怎麼", "什麼", "多少", "哪", "?", "？")


@dataclass(frozen=True)
class ResearchCandidate:
    keyword: str
    node_type: str
    intent: str | None
    source: str
    confidence: float
    enrichment: dict


def infer_keyword_level(node_type: str) -> str:
    if node_type == "core":
        return "head"
    if node_type in ("long_tail", "faq"):
        return "long_tail"
    return "mid_tail"


def infer_node_type(keyword: str) -> str:
    if any(marker in keyword for marker in QUESTION_MARKERS):
        return "faq"
    if "比較" in keyword or "vs" in keyword.lower():
        return "comparison"
    if len(keyword) >= 10:
        return "long_tail"
    if len(keyword) <= 6:
        return "pillar"
    return "cluster"


def infer_intent(keyword: str) -> str | None:
    lowered = keyword.lower()
    if any(x in lowered for x in ("價格", "費用", "報價", "購買", "哪裡買")):
        return "transactional"
    if any(x in lowered for x in ("推薦", "比較", "品牌")):
        return "commercial"
    if any(x in keyword for x in QUESTION_MARKERS):
        return "informational"
    return None


def infer_funnel_stage(intent: str | None, node_type: str) -> str | None:
    if intent == "transactional" or node_type in ("comparison", "solution"):
        return "bofu"
    if intent == "commercial" or node_type == "cluster":
        return "mofu"
    if intent == "informational" or node_type in ("long_tail", "faq"):
        return "tofu"
    return None


def _looks_like_keyword(text: str) -> bool:
    cleaned = text.strip()
    if len(cleaned) < MIN_KEYWORD_LEN or len(cleaned) > MAX_KEYWORD_LEN:
        return False
    if cleaned.count("，") > 0 or cleaned.count("。") > 0:
        return False
    if re.search(r"[。！!；;]", cleaned):
        return False
    return True


def expand_candidates_from_serp(
    *,
    seed_keyword: str,
    slots: list,
    provider: str,
    include_paa: bool = True,
    include_related: bool = True,
    max_expansions: int = 12,
) -> list[ResearchCandidate]:
    """Build reviewable candidates from one SERP fetch."""
    enrichment = enrichment_from_serp(
        slots=slots,
        provider=provider,
        source="cold_start_serp",
        seed_keyword=seed_keyword,
    )
    out: list[ResearchCandidate] = []
    seen: set[str] = set()

    def add(keyword: str, source: str, confidence: float) -> None:
        key = normalize_keyword(keyword)
        if not key or key in seen or not _looks_like_keyword(keyword):
            return
        seen.add(key)
        node_type = infer_node_type(keyword)
        intent = infer_intent(keyword)
        out.append(
            ResearchCandidate(
                keyword=keyword.strip(),
                node_type=node_type,
                intent=intent,
                source=source,
                confidence=confidence,
                enrichment=enrichment,
            )
        )

    add(seed_keyword, "seed", 1.0)

    if include_paa:
        for question in enrichment.get("paa_questions") or []:
            if len(out) >= max_expansions + 1:
                break
            add(str(question), "paa", 0.85)

    if include_related:
        for related in enrichment.get("related_searches") or []:
            if len(out) >= max_expansions + 1:
                break
            add(str(related), "related_search", 0.8)

    return out[: max_expansions + 1]
