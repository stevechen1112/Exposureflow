import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from execution_adapters.wordpress import (
    WordPressCredentials,
    build_post_payload,
    parse_credentials,
    publish_draft,
)


def test_parse_credentials() -> None:
    payload = json.dumps(
        {
            "site_url": "https://example.com",
            "username": "admin",
            "application_password": "abcd 1234",
        }
    )
    creds = parse_credentials(payload)
    assert creds.site_url == "https://example.com"
    assert creds.username == "admin"


def test_build_post_payload_includes_meta() -> None:
    payload = build_post_payload(
        title="Test",
        content_markdown="Body",
        meta_description="Desc",
        canonical_url="https://example.com/page",
    )
    assert payload["title"] == "Test"
    assert payload["meta"]["description"] == "Desc"


@pytest.mark.asyncio
async def test_publish_draft_posts_to_wordpress() -> None:
    creds = WordPressCredentials(
        site_url="https://example.com",
        username="admin",
        application_password="secret",
    )
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.content = b"{}"
    mock_response.json.return_value = {
        "id": 42,
        "link": "https://example.com/?p=42",
        "status": "draft",
    }

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch("execution_adapters.wordpress.httpx.AsyncClient") as client_cls:
        client_cls.return_value.__aenter__.return_value = mock_client
        result = await publish_draft(
            creds,
            build_post_payload(title="T", content_markdown="Body"),
            client=mock_client,
        )

    assert result.success is True
    assert result.post_id == 42
    mock_client.post.assert_awaited_once()
