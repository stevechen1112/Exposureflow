#!/usr/bin/env python3
"""One-shot: store ezfix contentflow credential and publish draft runs."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("EF_API_BASE", "https://app.kakusinn.com")
WS = os.environ.get("EF_WORKSPACE_ID", "67a1694d-fab1-4694-b05c-37790ef8ef87")
SITE = os.environ.get("EF_SITE_ID", "02cb80a6-75ef-4a0a-b2b3-8911d650579e")
SECRET = os.environ.get("CONTENTFLOW_SECRET", "cf-henghui-2026-change-me")
RUNS = [
    "570c3fbd-b32c-4f2f-9f1a-228bde4e199a",
    "2355e8ef-82b1-4bc5-aea7-59b4efcc7268",
]


def request(method: str, path: str, body: dict | None = None, token: str | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    headers["X-Workspace-Id"] = WS
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()
        raise RuntimeError(f"{method} {path} -> {exc.code}: {detail}") from exc


def main() -> int:
    token_resp = request(
        "POST",
        "/api/v1/auth/dev-token",
        {"email": "owner@example.com", "name": "Owner", "role": "owner"},
    )
    token = token_resp["access_token"]

    cred_payload = json.dumps(
        {
            "site_url": "https://ezfix.com.tw",
            "secret": SECRET,
            "blog_path": "/blog",
        },
        ensure_ascii=False,
    )

    existing = request("GET", "/api/v1/integrations/credentials", token=token)
    has_cf = any(
        row.get("provider") == "contentflow" and row.get("site_id") == SITE
        for row in existing
    )
    if not has_cf:
        created = request(
            "POST",
            "/api/v1/integrations/credentials",
            {
                "provider": "contentflow",
                "credential_type": "api_key",
                "payload": cred_payload,
                "site_id": SITE,
                "credential_name": "default",
            },
            token=token,
        )
        print("credential_created", created.get("id"))
    else:
        print("credential_exists")

    for run_id in RUNS:
        result = request(
            "POST",
            f"/api/v1/content/generation-runs/{run_id}/publish",
            {},
            token=token,
        )
        print("published", run_id, json.dumps(result, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
