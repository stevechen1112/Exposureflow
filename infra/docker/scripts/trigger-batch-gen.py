#!/usr/bin/env python3
"""Trigger batch content generation on prod via internal API."""
import json
import urllib.request

BASE = "http://localhost:8000"
WS = "67a1694d-fab1-4694-b05c-37790ef8ef87"
SITE = "02cb80a6-75ef-4a0a-b2b3-8911d650579e"


def post(path, body, token=None, workspace=None):
    data = json.dumps(body).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if workspace:
        headers["X-Workspace-Id"] = workspace
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=600) as resp:
        return json.loads(resp.read().decode())


token_resp = post("/api/v1/auth/dev-token", {"email": "owner@example.com", "name": "Owner", "role": "owner"})
token = token_resp["access_token"]
print("token ok")

result = post(
    "/api/v1/content/schedule/batch-generate",
    {"site_id": SITE, "count": 1, "priority_filter": "P1"},
    token=token,
    workspace=WS,
)
print(json.dumps(result, ensure_ascii=False, indent=2))
