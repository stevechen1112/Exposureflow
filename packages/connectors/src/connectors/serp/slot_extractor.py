"""Extract normalized SERP slots from provider raw JSON."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

from connectors.types import SerpFetchResult, SerpSlotData

FORUM_DOMAINS = {
    "reddit.com",
    "quora.com",
    "dcard.tw",
    "ptt.cc",
    "mobile01.com",
    "stackexchange.com",
    "stackoverflow.com",
}


def _domain(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(url)
    host = parsed.netloc.lower().removeprefix("www.")
    return host or None


def _classify_owner(
    url: str | None,
    site_domain: str,
    competitor_domains: set[str],
) -> tuple[bool, bool, bool]:
    domain = _domain(url)
    if domain is None:
        return False, False, False
    site = site_domain.lower().removeprefix("www.")
    if domain == site or domain.endswith(f".{site}"):
        return True, False, False
    if domain in competitor_domains or any(domain.endswith(f".{c}") for c in competitor_domains):
        return False, True, False
    if domain in FORUM_DOMAINS:
        return False, False, True
    return False, False, False


def extract_slots(
    raw_json: dict[str, Any],
    *,
    site_domain: str,
    competitor_domains: set[str] | None = None,
) -> list[SerpSlotData]:
    competitors = competitor_domains or set()
    slots: list[SerpSlotData] = []

    organic_key = "organic" if "organic" in raw_json else "organic_results"
    for idx, item in enumerate(raw_json.get(organic_key, []), start=1):
        url = item.get("link") or item.get("url")
        own, comp, third = _classify_owner(url, site_domain, competitors)
        slots.append(
            SerpSlotData(
                slot_type="organic",
                position=item.get("position") or idx,
                owner_domain=_domain(url),
                owner_brand=item.get("source"),
                url=url,
                title=item.get("title"),
                snippet=item.get("snippet") or item.get("description"),
                is_own_site=own,
                is_competitor=comp,
                is_third_party=third,
            )
        )

    answer_box = raw_json.get("answerBox") or raw_json.get("answer_box")
    if answer_box:
        url = answer_box.get("link") or answer_box.get("url")
        own, comp, third = _classify_owner(url, site_domain, competitors)
        slots.append(
            SerpSlotData(
                slot_type="featured_snippet",
                position=0,
                owner_domain=_domain(url),
                url=url,
                title=answer_box.get("title"),
                snippet=answer_box.get("snippet") or answer_box.get("answer"),
                is_own_site=own,
                is_competitor=comp,
                is_third_party=third,
            )
        )

    paa_key = "peopleAlsoAsk" if "peopleAlsoAsk" in raw_json else "related_questions"
    for item in raw_json.get(paa_key, []):
        slots.append(
            SerpSlotData(
                slot_type="paa",
                position=None,
                title=item.get("question") or item.get("title"),
                snippet=item.get("snippet"),
            )
        )

    for item in raw_json.get("relatedSearches", raw_json.get("related_searches", [])):
        slots.append(
            SerpSlotData(
                slot_type="related_search",
                position=None,
                title=item.get("query") if isinstance(item, dict) else str(item),
            )
        )

    for idx, item in enumerate(raw_json.get("images", raw_json.get("images_results", [])), start=1):
        url = item.get("link") or item.get("original")
        own, comp, third = _classify_owner(url, site_domain, competitors)
        slots.append(
            SerpSlotData(
                slot_type="image",
                position=idx,
                url=url,
                title=item.get("title"),
                is_own_site=own,
                is_competitor=comp,
                is_third_party=third,
            )
        )

    for idx, item in enumerate(raw_json.get("videos", raw_json.get("video_results", [])), start=1):
        url = item.get("link")
        own, comp, third = _classify_owner(url, site_domain, competitors)
        slots.append(
            SerpSlotData(
                slot_type="video",
                position=idx,
                url=url,
                title=item.get("title"),
                snippet=item.get("snippet"),
                is_own_site=own,
                is_competitor=comp,
                is_third_party=third,
            )
        )

    for idx, item in enumerate(raw_json.get("shopping_results", []), start=1):
        url = item.get("link")
        own, comp, third = _classify_owner(url, site_domain, competitors)
        slots.append(
            SerpSlotData(
                slot_type="product",
                position=idx,
                url=url,
                title=item.get("title"),
                is_own_site=own,
                is_competitor=comp,
                is_third_party=third,
            )
        )

    if raw_json.get("ai_overview") or raw_json.get("aiOverview"):
        slots.append(SerpSlotData(slot_type="ai_overview", position=0, title="AI Overview present"))

    return slots


def build_fetch_result(
    raw_json: dict[str, Any],
    *,
    keyword: str,
    country: str,
    language: str,
    device: str,
    site_domain: str,
    competitor_domains: set[str] | None = None,
) -> SerpFetchResult:
    captured_raw = raw_json.get("_captured_at")
    captured_at = (
        datetime.fromisoformat(captured_raw) if captured_raw else datetime.now(UTC)
    )
    provider = raw_json.get("_provider", "unknown")
    slots = extract_slots(raw_json, site_domain=site_domain, competitor_domains=competitor_domains)
    return SerpFetchResult(
        keyword=keyword,
        country=country,
        language=language,
        device=device,
        raw_provider=provider,
        raw_json=raw_json,
        captured_at=captured_at,
        slots=slots,
    )
