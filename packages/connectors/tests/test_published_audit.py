"""Published article audit tests."""

import httpx

from connectors.indexability.published_audit import audit_recent_published_urls


def test_audit_recent_published_urls_detects_noindex() -> None:
    article = "https://example.com/blog/live-post"

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        if request.url.path == "/blog/live-post":
            return httpx.Response(
                200,
                text='<html><head><meta name="robots" content="noindex"></head></html>',
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    issues = audit_recent_published_urls(
        "https://example.com",
        [article],
        http_client=client,
    )
    assert any(issue.issue_type == "noindex" for issue in issues)


def test_audit_recent_published_urls_detects_robots_blog_block() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /blog\n")
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    issues = audit_recent_published_urls(
        "https://example.com",
        ["https://example.com/blog/post"],
        http_client=client,
        max_articles_to_check=0,
    )
    assert any(issue.issue_type == "robots_blocked" for issue in issues)
