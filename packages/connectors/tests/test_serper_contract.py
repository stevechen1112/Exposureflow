"""Serper provider contract test."""

import httpx

from connectors.serp.providers.serper import SerperProvider


def test_serper_fetch_posts_expected_payload() -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        captured["headers"] = dict(request.headers)
        captured["body"] = json.loads(request.content.decode())
        return httpx.Response(
            200,
            json={"organic": [{"title": "T", "link": "https://example.com", "position": 1}]},
        )

    transport = httpx.MockTransport(handler)
    provider = SerperProvider("serper-key", http_client=httpx.Client(transport=transport))
    result = provider.fetch("exposure seo", country="tw", language="zh-TW", device="desktop")
    assert captured["headers"]["x-api-key"] == "serper-key"
    assert captured["body"]["q"] == "exposure seo"
    assert result["_provider"] == "serper"
    assert len(result["organic"]) == 1
