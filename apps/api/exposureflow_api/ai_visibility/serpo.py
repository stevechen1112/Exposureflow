"""SERPO (Search Engine Results Page Optimization) monitor."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class SerpoSnapshot:
    brand_query: str
    keyword: str | None
    surface: str
    first_page_positive_count: int
    first_page_neutral_count: int
    first_page_negative_count: int
    first_page_wrong_info_count: int
    recommended_actions_json: list[str]
    captured_at: datetime


def aggregate_serpo_from_mentions(
    *,
    brand_query: str,
    keyword: str | None,
    surface: str,
    mentions: list,
) -> SerpoSnapshot:
    positive = neutral = negative = wrong = 0
    for mention in mentions:
        sentiment = getattr(mention, "sentiment", None) or "unknown"
        if sentiment == "positive":
            positive += 1
        elif sentiment == "neutral":
            neutral += 1
        elif sentiment == "negative":
            negative += 1
        elif sentiment == "wrong_info":
            wrong += 1

    actions: list[str] = []
    if wrong > 0:
        actions.append("entity_fix: correct wrong brand info on indexed sources")
    if negative > positive:
        actions.append("third_party_citation: improve positive brand coverage")
    if positive == 0 and neutral == 0 and negative == 0 and wrong == 0:
        actions.append("monitor: insufficient SERPO signal")

    return SerpoSnapshot(
        brand_query=brand_query,
        keyword=keyword,
        surface=surface,
        first_page_positive_count=positive,
        first_page_neutral_count=neutral,
        first_page_negative_count=negative,
        first_page_wrong_info_count=wrong,
        recommended_actions_json=actions,
        captured_at=datetime.now(timezone.utc),
    )
