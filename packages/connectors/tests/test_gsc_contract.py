"""GSC client contract tests with mocked HTTP."""

from datetime import date

import httpx

from connectors.google_search_console import GSCClient, OAuthTokenProvider


class _StaticTokenProvider:
    def get_access_token(self) -> str:
        return "test-token"


def test_gsc_fetch_search_analytics_parses_rows() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert "searchAnalytics/query" in str(request.url)
        assert request.headers["Authorization"] == "Bearer test-token"
        body = {
            "rows": [
                {
                    "keys": ["2026-06-01", "seo tips", "https://example.com/a", "twn", "DESKTOP"],
                    "impressions": 100,
                    "clicks": 10,
                    "ctr": 0.1,
                    "position": 5.2,
                }
            ]
        }
        return httpx.Response(200, json=body)

    transport = httpx.MockTransport(handler)
    client = GSCClient(
        site_url="sc-domain:example.com",
        token_provider=_StaticTokenProvider(),
        http_client=httpx.Client(transport=transport),
    )
    rows = client.fetch_search_analytics(date(2026, 6, 1), date(2026, 6, 1))
    assert len(rows) == 1
    assert rows[0].query == "seo tips"
    assert rows[0].page == "https://example.com/a"
    assert rows[0].impressions == 100


def test_gsc_incremental_returns_empty_when_caught_up() -> None:
    transport = httpx.MockTransport(lambda _r: httpx.Response(200, json={"rows": []}))
    client = GSCClient(
        site_url="sc-domain:example.com",
        token_provider=OAuthTokenProvider("token"),
        http_client=httpx.Client(transport=transport),
    )
    rows = client.fetch_incremental(date.today())
    assert rows == []
