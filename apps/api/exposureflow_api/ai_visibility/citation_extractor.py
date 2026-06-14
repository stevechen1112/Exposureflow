"""Extract and classify cited URLs from AI probe answers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

from exposureflow_api.exposure.owner_classification import classify_url_owner

URL_PATTERN = re.compile(r"https?://[^\s\)\]>\",']+")

PROBE_SURFACES = frozenset(
    {"chatgpt_search", "perplexity", "bing_copilot", "google_ai_overview"}
)
PROBE_MODES = frozenset({"automated_provider", "assisted_manual", "manual_import"})


@dataclass(frozen=True)
class ExtractedCitation:
    cited_url: str
    cited_domain: str | None
    citation_context: str | None
    is_own_site: bool
    is_competitor: bool
    is_third_party_about_brand: bool


def _normalize_url(url: str) -> str:
    return url.rstrip(".,;)")


def extract_urls_from_text(text: str) -> list[str]:
    seen: set[str] = set()
    urls: list[str] = []
    for match in URL_PATTERN.findall(text):
        normalized = _normalize_url(match)
        if normalized not in seen:
            seen.add(normalized)
            urls.append(normalized)
    return urls


def merge_cited_urls(explicit_urls: list[str], answer_text: str) -> list[str]:
    seen: set[str] = set()
    merged: list[str] = []
    for url in explicit_urls + extract_urls_from_text(answer_text):
        normalized = _normalize_url(url.strip())
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        merged.append(normalized)
    return merged


def citation_context_for_url(answer_text: str, url: str, window: int = 80) -> str | None:
    idx = answer_text.find(url)
    if idx < 0:
        return None
    start = max(0, idx - window)
    end = min(len(answer_text), idx + len(url) + window)
    return answer_text[start:end].strip()


def extract_citations(
    *,
    answer_text: str,
    explicit_urls: list[str] | None,
    site_domain: str,
    competitor_domains: set[str],
    our_brand_names: set[str],
) -> list[ExtractedCitation]:
    urls = merge_cited_urls(explicit_urls or [], answer_text)
    citations: list[ExtractedCitation] = []
    for url in urls:
        owner = classify_url_owner(
            url,
            site_domain=site_domain,
            competitor_domains=competitor_domains,
        )
        context = citation_context_for_url(answer_text, url)
        mentions_brand = False
        if context and our_brand_names:
            lower = context.lower()
            mentions_brand = any(name.lower() in lower for name in our_brand_names if name)
        is_third_party = owner.is_third_party or (
            not owner.is_own and not owner.is_competitor and mentions_brand
        )
        host = urlparse(url).netloc.lower().removeprefix("www.") or None
        citations.append(
            ExtractedCitation(
                cited_url=url,
                cited_domain=host,
                citation_context=context,
                is_own_site=owner.is_own,
                is_competitor=owner.is_competitor,
                is_third_party_about_brand=is_third_party,
            )
        )
    return citations
