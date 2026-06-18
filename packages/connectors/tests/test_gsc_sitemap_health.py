"""GSC sitemap health audit tests."""

import httpx

from connectors.google_search_console import GSCClient
from connectors.indexability.gsc_sitemap import audit_gsc_sitemap_health


class _StaticTokenProvider:
    def get_access_token(self) -> str:
        return "test-token"


def test_audit_gsc_sitemap_health_flags_missing_submission() -> None:
    transport = httpx.MockTransport(
        lambda _r: httpx.Response(200, json={"sitemap": []}),
    )
    client = GSCClient(
        site_url="sc-domain:example.com",
        token_provider=_StaticTokenProvider(),
        http_client=httpx.Client(transport=transport),
    )
    report = audit_gsc_sitemap_health(client)
    assert report.healthy is False
    assert report.issues[0].issue_type == "gsc_sitemap_missing"


def test_audit_gsc_sitemap_health_flags_unreachable_sitemap() -> None:
    body = {
        "sitemap": [
            {
                "path": "https://example.com/sitemap.xml",
                "errors": 2,
                "warnings": 0,
                "isPending": False,
            }
        ]
    }
    transport = httpx.MockTransport(lambda _r: httpx.Response(200, json=body))
    client = GSCClient(
        site_url="sc-domain:example.com",
        token_provider=_StaticTokenProvider(),
        http_client=httpx.Client(transport=transport),
    )
    report = audit_gsc_sitemap_health(client)
    assert report.healthy is False
    assert report.issues[0].issue_type == "gsc_sitemap_unreachable"


def test_gsc_list_sitemaps_parses_response() -> None:
    body = {"sitemap": [{"path": "https://example.com/sitemap.xml", "errors": 0}]}
    transport = httpx.MockTransport(lambda _r: httpx.Response(200, json=body))
    client = GSCClient(
        site_url="sc-domain:example.com",
        token_provider=_StaticTokenProvider(),
        http_client=httpx.Client(transport=transport),
    )
    sitemaps = client.list_sitemaps()
    assert len(sitemaps) == 1
    assert sitemaps[0]["path"] == "https://example.com/sitemap.xml"
