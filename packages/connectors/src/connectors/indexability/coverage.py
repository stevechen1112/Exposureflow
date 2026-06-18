"""Detect published URLs not yet appearing in GSC page data (OG-013 proxy)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from urllib.parse import urlparse


def normalize_page_url(url: str) -> str:
    parsed = urlparse(url.strip())
    path = parsed.path.rstrip("/") or "/"
    return f"{parsed.scheme}://{parsed.netloc.lower()}{path}"


def filter_urls_older_than(
    published_records: list[tuple[str, datetime]],
    *,
    min_age_days: int = 7,
    now: datetime | None = None,
) -> list[str]:
    """Return URLs whose live publish timestamp is at least min_age_days ago."""
    reference = now or datetime.now(UTC)
    cutoff = reference - timedelta(days=min_age_days)
    urls: list[str] = []
    for url, published_at in published_records:
        pub_at = published_at
        if pub_at.tzinfo is None:
            pub_at = pub_at.replace(tzinfo=UTC)
        if pub_at <= cutoff:
            urls.append(url)
    return urls
