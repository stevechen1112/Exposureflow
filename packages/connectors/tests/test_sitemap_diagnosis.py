"""Live sitemap diagnosis tests."""

import httpx

from connectors.indexability.sitemap_diagnosis import diagnose_live_sitemap

SITEMAP_LOCALHOST = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>http://localhost:3000/blog/test</loc></url>
  <url><loc>http://localhost:3000/about</loc></url>
</urlset>"""

SITEMAP_OK = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://ezfix.com.tw/blog/test</loc></url>
  <url><loc>https://ezfix.com.tw/about</loc></url>
</urlset>"""


def test_diagnose_live_sitemap_flags_localhost() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=SITEMAP_LOCALHOST)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    diagnosis = diagnose_live_sitemap(
        "https://ezfix.com.tw/sitemap.xml",
        "ezfix.com.tw",
        http_client=client,
    )
    assert diagnosis.fetch_ok is True
    assert diagnosis.root_cause == "localhost_urls"
    assert len(diagnosis.sample_bad_urls) >= 1
    assert "NEXT_PUBLIC_SITE_URL" in diagnosis.recommended_action


def test_diagnose_live_sitemap_ok_gsc_stale() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=SITEMAP_OK)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    diagnosis = diagnose_live_sitemap(
        "https://ezfix.com.tw/sitemap.xml",
        "ezfix.com.tw",
        http_client=client,
    )
    assert diagnosis.root_cause == "content_ok_gsc_stale"


def test_diagnose_live_sitemap_fetch_failed() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="not found")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    diagnosis = diagnose_live_sitemap(
        "https://ezfix.com.tw/sitemap.xml",
        "ezfix.com.tw",
        http_client=client,
    )
    assert diagnosis.fetch_ok is False
    assert diagnosis.root_cause == "fetch_failed"
