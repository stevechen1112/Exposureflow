"""Post-publish indexability verifier tests."""

import httpx

from connectors.indexability.verifier import url_present_in_sitemap, verify_published_url


def test_verify_published_url_immediate_ok_without_sitemap() -> None:
    article = "https://example.com/blog/test-article"

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/blog/test-article":
            return httpx.Response(200, text="<html><head></head><body>ok</body></html>")
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    result = verify_published_url(article, site_base_url="https://example.com", http_client=client)
    assert result.ok is True
    assert result.url_reachable is True
    assert result.sitemap_checked is False
    assert result.in_sitemap is None
    assert result.has_noindex is False


def test_verify_published_url_with_sitemap_check() -> None:
    article = "https://example.com/blog/test-article"
    sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://example.com/blog/test-article</loc></url>
    </urlset>"""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/blog/test-article":
            return httpx.Response(200, text="<html><head></head><body>ok</body></html>")
        if request.url.path == "/sitemap.xml":
            return httpx.Response(200, text=sitemap_xml)
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    result = verify_published_url(
        article,
        site_base_url="https://example.com",
        http_client=client,
        check_sitemap=True,
    )
    assert result.in_sitemap is True
    assert result.sitemap_checked is True


def test_verify_published_url_detects_noindex_without_sitemap_penalty() -> None:
    article = "https://example.com/blog/blocked"

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/blog/blocked":
            return httpx.Response(
                200,
                text='<html><head><meta name="robots" content="noindex,nofollow"></head></html>',
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    result = verify_published_url(article, site_base_url="https://example.com", http_client=client)
    assert result.ok is False
    assert result.has_noindex is True
    assert result.sitemap_checked is False


def test_url_present_in_sitemap_exact_match_only() -> None:
    sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://example.com/blog/ab</loc></url>
    </urlset>"""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/sitemap.xml":
            return httpx.Response(200, text=sitemap_xml)
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    assert url_present_in_sitemap(
        "https://example.com/blog/a",
        site_base_url="https://example.com",
        http_client=client,
    ) is False
