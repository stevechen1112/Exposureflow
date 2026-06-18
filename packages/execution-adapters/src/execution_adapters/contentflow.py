"""ContentFlow managed-site publisher — POST publish / PUT update."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote, urlparse

import httpx

_HEADER_RE = re.compile(r"^#{1,6}\s+")


@dataclass(frozen=True)
class ContentFlowCredentials:
    site_url: str
    secret: str
    blog_path: str = "/blog"


@dataclass(frozen=True)
class ContentFlowPublishResult:
    success: bool
    post_id: str | None
    post_url: str | None
    status: str
    action: str
    raw_response: dict[str, Any]


def parse_contentflow_credentials(payload_json: str) -> ContentFlowCredentials:
    data = json.loads(payload_json)
    blog_path = str(data.get("blog_path") or "/blog").strip() or "/blog"
    if not blog_path.startswith("/"):
        blog_path = f"/{blog_path}"
    return ContentFlowCredentials(
        site_url=str(data["site_url"]).rstrip("/"),
        secret=str(data["secret"]),
        blog_path=blog_path.rstrip("/") or "/blog",
    )


def slugify_keyword(keyword: str) -> str:
    lowered = keyword.lower().strip()
    slug = re.sub(r"[\s\u3000]+", "-", lowered)
    slug = re.sub(r"[^\u4e00-\u9fa5a-z0-9\-_]", "", slug, flags=re.IGNORECASE)
    slug = re.sub(r"-+", "-", slug).strip("-")[:80]
    return slug or "article"


def extract_blog_slug(url: str | None, *, blog_path: str = "/blog") -> str | None:
    if not url:
        return None
    path = urlparse(url).path.rstrip("/")
    prefix = (blog_path or "/blog").rstrip("/")
    marker = f"{prefix}/"
    if marker not in path and not path.startswith(marker):
        return None
    slug = path.split(marker, 1)[-1].strip("/")
    if not slug or "/" in slug:
        return None
    return slug


def resolve_blog_slug_from_brief(
    brief_json: dict[str, Any],
    *,
    blog_path: str = "/blog",
) -> str | None:
    """Pick blog slug from brief URLs; refresh_page prefers current_url."""
    opportunity_type = str(brief_json.get("opportunity_type") or "")
    if opportunity_type == "refresh_page":
        url_candidates = (
            brief_json.get("current_url"),
            brief_json.get("target_url"),
        )
    else:
        url_candidates = (
            brief_json.get("target_url"),
            brief_json.get("current_url"),
        )
    for url in url_candidates:
        slug = extract_blog_slug(url, blog_path=blog_path)
        if slug:
            return slug
    return None


def markdown_to_blog_content(markdown: str) -> str:
    """Legacy plain-text transform for sites without markdown rendering."""
    lines: list[str] = []
    for line in markdown.splitlines():
        normalized = _HEADER_RE.sub("", line).strip()
        if normalized:
            lines.append(normalized)
    return "\n\n".join(lines)


def prepare_contentflow_body(content_markdown: str, *, content_format: str = "markdown") -> tuple[str, str]:
    if content_format == "markdown":
        return content_markdown.strip(), "markdown"
    return markdown_to_blog_content(content_markdown), "plain"


def build_publish_payload(
    *,
    title: str,
    slug: str,
    content_markdown: str,
    status: str = "draft",
    excerpt: str | None = None,
    meta_title: str | None = None,
    meta_description: str | None = None,
    json_ld: str | None = None,
    hero_image_url: str | None = None,
    category: str | None = None,
    content_format: str = "markdown",
) -> dict[str, Any]:
    body, resolved_format = prepare_contentflow_body(
        content_markdown, content_format=content_format
    )
    payload: dict[str, Any] = {
        "title": title,
        "slug": slug,
        "content": body,
        "content_format": resolved_format,
        "status": status,
    }
    if excerpt:
        payload["excerpt"] = excerpt
    if meta_title:
        payload["meta_title"] = meta_title
    if meta_description:
        payload["meta_description"] = meta_description
    if json_ld:
        payload["json_ld"] = json_ld
    if hero_image_url:
        payload["hero_image_url"] = hero_image_url
    if category:
        payload["category"] = category
    return payload


def resolve_post_url(credentials: ContentFlowCredentials, slug: str, relative_url: str | None) -> str:
    if relative_url and relative_url.startswith("http"):
        return relative_url
    path = relative_url or f"{credentials.blog_path}/{slug}"
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{credentials.site_url}{path}"


async def publish_draft(
    credentials: ContentFlowCredentials,
    payload: dict[str, Any],
    *,
    client: httpx.AsyncClient | None = None,
) -> ContentFlowPublishResult:
    owns_client = client is None
    http = client or httpx.AsyncClient(timeout=30.0)
    url = f"{credentials.site_url}/api/contentflow/publish"
    headers = {
        "Authorization": f"Bearer {credentials.secret}",
        "Content-Type": "application/json",
    }
    try:
        response = await http.post(url, json=payload, headers=headers)
        data = response.json() if response.content else {}
        if response.status_code >= 400:
            return ContentFlowPublishResult(
                success=False,
                post_id=None,
                post_url=None,
                status="error",
                action="publish",
                raw_response={"status_code": response.status_code, "body": data},
            )
        slug = str(payload.get("slug") or "")
        return ContentFlowPublishResult(
            success=bool(data.get("success", True)),
            post_id=str(data.get("postId")) if data.get("postId") is not None else None,
            post_url=resolve_post_url(credentials, slug, data.get("url")),
            status=str(payload.get("status") or "draft"),
            action="publish",
            raw_response=data,
        )
    finally:
        if owns_client:
            await http.aclose()


async def update_post(
    credentials: ContentFlowCredentials,
    slug: str,
    payload: dict[str, Any],
    *,
    client: httpx.AsyncClient | None = None,
) -> ContentFlowPublishResult:
    owns_client = client is None
    http = client or httpx.AsyncClient(timeout=30.0)
    encoded_slug = quote(slug, safe="")
    url = f"{credentials.site_url}/api/contentflow/update/{encoded_slug}"
    headers = {
        "Authorization": f"Bearer {credentials.secret}",
        "Content-Type": "application/json",
    }
    try:
        response = await http.put(url, json=payload, headers=headers)
        data = response.json() if response.content else {}
        if response.status_code >= 400:
            return ContentFlowPublishResult(
                success=False,
                post_id=None,
                post_url=None,
                status="error",
                action="update",
                raw_response={"status_code": response.status_code, "body": data},
            )
        return ContentFlowPublishResult(
            success=bool(data.get("success", True)),
            post_id=str(data.get("postId")) if data.get("postId") is not None else None,
            post_url=resolve_post_url(credentials, slug, data.get("url")),
            status=str(payload.get("status") or "draft"),
            action="update",
            raw_response=data,
        )
    finally:
        if owns_client:
            await http.aclose()
