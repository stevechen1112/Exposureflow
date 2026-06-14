"""WordPress publisher adapter — draft publish and page update."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class WordPressCredentials:
    site_url: str
    username: str
    application_password: str


@dataclass(frozen=True)
class PublishResult:
    success: bool
    post_id: int | None
    post_url: str | None
    status: str
    raw_response: dict[str, Any]


def parse_credentials(payload_json: str) -> WordPressCredentials:
    data = json.loads(payload_json)
    site_url = str(data["site_url"]).rstrip("/")
    return WordPressCredentials(
        site_url=site_url,
        username=str(data["username"]),
        application_password=str(data["application_password"]),
    )


def build_post_payload(
    *,
    title: str,
    content_markdown: str,
    status: str = "draft",
    meta_description: str | None = None,
    canonical_url: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "title": title,
        "content": content_markdown,
        "status": status,
    }
    meta: dict[str, str] = {}
    if meta_description:
        meta["description"] = meta_description
    if canonical_url:
        meta["canonical"] = canonical_url
    if meta:
        payload["meta"] = meta
    return payload


async def publish_draft(
    credentials: WordPressCredentials,
    payload: dict[str, Any],
    *,
    client: httpx.AsyncClient | None = None,
    post_id: int | None = None,
) -> PublishResult:
    base = credentials.site_url
    auth = (credentials.username, credentials.application_password)
    owns_client = client is None
    http = client or httpx.AsyncClient(timeout=30.0)
    try:
        if post_id is not None:
            url = f"{base}/wp-json/wp/v2/posts/{post_id}"
            response = await http.post(url, json=payload, auth=auth)
        else:
            url = f"{base}/wp-json/wp/v2/posts"
            response = await http.post(url, json=payload, auth=auth)
        data = response.json() if response.content else {}
        if response.status_code >= 400:
            return PublishResult(
                success=False,
                post_id=post_id,
                post_url=None,
                status="error",
                raw_response={"status_code": response.status_code, "body": data},
            )
        return PublishResult(
            success=True,
            post_id=int(data.get("id")) if data.get("id") is not None else post_id,
            post_url=data.get("link"),
            status=str(data.get("status") or payload.get("status") or "draft"),
            raw_response=data,
        )
    finally:
        if owns_client:
            await http.aclose()
