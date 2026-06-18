"""Index coverage discovery gap tests."""

from datetime import UTC, datetime, timedelta

from connectors.indexability.coverage import filter_urls_older_than, normalize_page_url


def test_normalize_page_url_strips_trailing_slash() -> None:
    assert normalize_page_url("https://Example.com/blog/post/") == "https://example.com/blog/post"


def test_filter_urls_older_than_requires_min_age() -> None:
    now = datetime(2026, 6, 17, tzinfo=UTC)
    recent = now - timedelta(days=2)
    old = now - timedelta(days=10)
    urls = filter_urls_older_than(
        [
            ("https://example.com/blog/recent", recent),
            ("https://example.com/blog/old", old),
        ],
        min_age_days=7,
        now=now,
    )
    assert urls == ["https://example.com/blog/old"]
