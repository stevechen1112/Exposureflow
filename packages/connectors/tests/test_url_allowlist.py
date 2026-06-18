"""URL allowlist tests for sitemap diagnosis."""

import pytest

from connectors.indexability.url_allowlist import UnsafeSitemapUrlError, assert_sitemap_url_allowed


def test_assert_sitemap_url_allowed_accepts_matching_domain() -> None:
    url = assert_sitemap_url_allowed("https://ezfix.com.tw/sitemap.xml", "ezfix.com.tw")
    assert url == "https://ezfix.com.tw/sitemap.xml"


def test_assert_sitemap_url_allowed_rejects_foreign_host() -> None:
    with pytest.raises(UnsafeSitemapUrlError):
        assert_sitemap_url_allowed("https://evil.example.com/sitemap.xml", "ezfix.com.tw")


def test_assert_sitemap_url_allowed_rejects_localhost() -> None:
    with pytest.raises(UnsafeSitemapUrlError):
        assert_sitemap_url_allowed("http://localhost:3000/sitemap.xml", "ezfix.com.tw")
