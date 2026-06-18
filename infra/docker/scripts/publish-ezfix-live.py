#!/usr/bin/env python3
"""Push already-synced ezfix drafts to published status on the managed site."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("EF_API_BASE", "https://app.kakusinn.com")
WS = os.environ.get("EF_WORKSPACE_ID", "67a1694d-fab1-4694-b05c-37790ef8ef87")
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

    for run_id in RUNS:
        result = request(
            "POST",
            f"/api/v1/content/generation-runs/{run_id}/publish",
            {"site_status": "published"},
            token=token,
        )
        print("live", run_id, json.dumps(result, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
