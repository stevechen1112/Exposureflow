import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from execution_adapters.contentflow import (
    ContentFlowCredentials,
    build_publish_payload,
    extract_blog_slug,
    markdown_to_blog_content,
    parse_contentflow_credentials,
    prepare_contentflow_body,
    publish_draft,
    resolve_blog_slug_from_brief,
    slugify_keyword,
    update_post,
)


def test_parse_contentflow_credentials() -> None:
    payload = json.dumps(
        {
            "site_url": "https://ezfix.com.tw",
            "secret": "test-secret",
            "blog_path": "/blog",
        }
    )
    creds = parse_contentflow_credentials(payload)
    assert creds.site_url == "https://ezfix.com.tw"
    assert creds.secret == "test-secret"
    assert creds.blog_path == "/blog"


def test_slugify_keyword_keeps_cjk_tokens() -> None:
    assert slugify_keyword("紗窗破了怎麼辦") == "紗窗破了怎麼辦"
    assert slugify_keyword("換紗窗 價格") == "換紗窗-價格"


def test_extract_blog_slug_from_target_url() -> None:
    slug = extract_blog_slug("https://ezfix.com.tw/blog/huan-sha-chuang")
    assert slug == "huan-sha-chuang"


def test_extract_blog_slug_rejects_nested_paths() -> None:
    assert extract_blog_slug("https://ezfix.com.tw/blog/category/post") is None


def test_resolve_blog_slug_prefers_current_url_for_refresh() -> None:
    slug = resolve_blog_slug_from_brief(
        {
            "opportunity_type": "refresh_page",
            "target_url": "https://ezfix.com.tw/services/pricing",
            "current_url": "https://ezfix.com.tw/blog/existing-post",
        }
    )
    assert slug == "existing-post"


def test_resolve_blog_slug_prefers_target_url_for_create() -> None:
    slug = resolve_blog_slug_from_brief(
        {
            "opportunity_type": "create_page",
            "target_url": "https://ezfix.com.tw/blog/new-post",
            "current_url": "https://ezfix.com.tw/",
        }
    )
    assert slug == "new-post"


def test_markdown_to_blog_content_strips_headers() -> None:
    text = markdown_to_blog_content("## 標題\n\n段落內容")
    assert "##" not in text
    assert "標題" in text
    assert "段落內容" in text


def test_build_publish_payload_keeps_markdown_by_default() -> None:
    payload = build_publish_payload(
        title="測試",
        slug="test-slug",
        content_markdown="## 內文\n\n段落",
        meta_description="描述",
        category="維修建議",
    )
    assert payload["slug"] == "test-slug"
    assert payload["meta_description"] == "描述"
    assert payload["content_format"] == "markdown"
    assert payload["content"] == "## 內文\n\n段落"
    assert payload["category"] == "維修建議"


def test_prepare_contentflow_body_plain_mode() -> None:
    body, fmt = prepare_contentflow_body("## 標題\n\n段落", content_format="plain")
    assert fmt == "plain"
    assert "##" not in body
    assert "段落" in body


@pytest.mark.asyncio
async def test_publish_draft_posts_to_contentflow_api() -> None:
    creds = ContentFlowCredentials(site_url="https://ezfix.com.tw", secret="secret")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"{}"
    mock_response.json.return_value = {
        "success": True,
        "postId": "post-1",
        "url": "/blog/test-slug",
    }

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    result = await publish_draft(
        creds,
        build_publish_payload(title="T", slug="test-slug", content_markdown="Body"),
        client=mock_client,
    )

    assert result.success is True
    assert result.post_id == "post-1"
    assert result.post_url == "https://ezfix.com.tw/blog/test-slug"
    mock_client.post.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_post_puts_to_contentflow_api() -> None:
    creds = ContentFlowCredentials(site_url="https://ezfix.com.tw", secret="secret")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"{}"
    mock_response.json.return_value = {
        "success": True,
        "postId": "post-1",
        "url": "/blog/existing-slug",
    }

    mock_client = AsyncMock()
    mock_client.put = AsyncMock(return_value=mock_response)

    result = await update_post(
        creds,
        "existing-slug",
        {"title": "Updated", "content": "Body", "status": "draft"},
        client=mock_client,
    )

    assert result.success is True
    assert result.action == "update"
    mock_client.put.assert_awaited_once()
    assert mock_client.put.await_args.args[0].endswith("/api/contentflow/update/existing-slug")


@pytest.mark.asyncio
async def test_update_post_encodes_cjk_slug() -> None:
    creds = ContentFlowCredentials(site_url="https://ezfix.com.tw", secret="secret")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"{}"
    mock_response.json.return_value = {"success": True, "postId": "4", "url": "/blog/x"}

    mock_client = AsyncMock()
    mock_client.put = AsyncMock(return_value=mock_response)

    await update_post(creds, "紗窗破了怎麼辦", {"content": "Body"}, client=mock_client)

    called_url = mock_client.put.await_args.args[0]
    assert called_url.endswith("/api/contentflow/update/%E7%B4%97%E7%AA%97%E7%A0%B4%E4%BA%86%E6%80%8E%E9%BA%BC%E8%BE%A6")
