#!/usr/bin/env python3
"""Re-publish ezfix articles with markdown format via ContentFlow update API."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import quote

import httpx

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "apps" / "api"))
sys.path.insert(0, str(ROOT / "packages" / "execution-adapters" / "src"))

from exposureflow_api.execution.compiler.content_normalizer import (  # noqa: E402
    extract_excerpt,
    infer_category,
    normalize_article_markdown,
)
from execution_adapters.contentflow import build_publish_payload  # noqa: E402

SITE_URL = "https://ezfix.com.tw"
SECRET = "cf-henghui-2026-change-me"

ARTICLES = [
    {
        "slug": "紗窗破了怎麼辦",
        "title": "紗窗破了怎麼辦",
        "keyword": "紗窗破了怎麼辦",
        "handoff": ROOT / "docs" / "handoff" / "ezfix" / "紗窗破了怎麼辦.md",
    },
    {
        "slug": "換紗窗價格",
        "title": "換紗窗價格",
        "keyword": "換紗窗價格",
        "handoff": ROOT / "docs" / "handoff" / "ezfix" / "換紗窗價格.md",
    },
]


def main() -> None:
    headers = {
        "Authorization": f"Bearer {SECRET}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=30.0) as client:
        for item in ARTICLES:
            raw = item["handoff"].read_text(encoding="utf-8")
            normalized = normalize_article_markdown(
                raw,
                keyword=item["keyword"],
                title=item["title"],
            )
            payload = build_publish_payload(
                title=item["title"],
                slug=item["slug"],
                content_markdown=normalized,
                status="published",
                excerpt=extract_excerpt(normalized, keyword=item["keyword"]),
                category=infer_category(item["keyword"]),
                content_format="markdown",
            )
            encoded = quote(item["slug"], safe="")
            update_url = f"{SITE_URL}/api/contentflow/update/{encoded}"
            update_payload = {k: v for k, v in payload.items() if k != "slug"}
            resp = client.put(update_url, headers=headers, json=update_payload)
            if resp.status_code == 404:
                resp = client.post(f"{SITE_URL}/api/contentflow/publish", headers=headers, json=payload)
            print(item["slug"], resp.status_code, resp.text[:300])


if __name__ == "__main__":
    main()
