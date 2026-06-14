"""ForgeBase publisher adapter."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class ForgeBaseCredentials:
    api_base_url: str
    api_key: str
    site_slug: str


@dataclass(frozen=True)
class ForgeBasePublishResult:
    success: bool
    content_id: str | None
    url: str | None
    status: str
    raw_response: dict[str, Any]


def parse_forgebase_credentials(payload_json: str) -> ForgeBaseCredentials:
    data = json.loads(payload_json)
    return ForgeBaseCredentials(
        api_base_url=str(data["api_base_url"]).rstrip("/"),
        api_key=str(data["api_key"]),
        site_slug=str(data["site_slug"]),
    )


def build_forgebase_payload(
    *,
    title: str,
    body_markdown: str,
    status: str = "draft",
    meta: dict | None = None,
) -> dict[str, Any]:
    return {
        "title": title,
        "body_markdown": body_markdown,
        "status": status,
        "meta": meta or {},
    }


async def publish_forgebase_draft(
    credentials: ForgeBaseCredentials,
    payload: dict[str, Any],
    *,
    client: httpx.AsyncClient | None = None,
    content_id: str | None = None,
) -> ForgeBasePublishResult:
    auth = {"Authorization": f"Bearer {credentials.api_key}"}
    owns = client is None
    http = client or httpx.AsyncClient(timeout=30.0)
    try:
        if content_id:
            url = f"{credentials.api_base_url}/api/v1/sites/{credentials.site_slug}/content/{content_id}"
            response = await http.patch(url, json=payload, headers=auth)
        else:
            url = f"{credentials.api_base_url}/api/v1/sites/{credentials.site_slug}/content"
            response = await http.post(url, json=payload, headers=auth)
        data = response.json() if response.content else {}
        if response.status_code >= 400:
            return ForgeBasePublishResult(
                success=False,
                content_id=content_id,
                url=None,
                status="error",
                raw_response={"status_code": response.status_code, "body": data},
            )
        return ForgeBasePublishResult(
            success=True,
            content_id=str(data.get("id")) if data.get("id") is not None else content_id,
            url=data.get("url"),
            status=str(data.get("status") or payload.get("status") or "draft"),
            raw_response=data,
        )
    finally:
        if owns:
            await http.aclose()
