"""URL policy tests."""

from connectors.tech_seo.url_policy import filter_seed_urls, is_crawl_url_allowed


def test_blocks_private_ip_seed_urls() -> None:
    assert is_crawl_url_allowed("http://169.254.169.254/", "example.com") is False
    assert is_crawl_url_allowed("http://127.0.0.1/admin", "example.com") is False


def test_allows_same_site_urls() -> None:
    assert is_crawl_url_allowed("https://www.example.com/page", "example.com") is True


def test_filter_drops_off_domain_urls() -> None:
    seeds = filter_seed_urls(
        ["https://evil.com/x", "https://example.com/ok"],
        "example.com",
    )
    assert seeds == ["https://example.com/ok"]
