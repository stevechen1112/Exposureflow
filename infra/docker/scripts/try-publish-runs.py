#!/usr/bin/env python3
import json
import urllib.request

BASE = "http://localhost:8000"
WS = "67a1694d-fab1-4694-b05c-37790ef8ef87"
RUNS = [
    "570c3fbd-b32c-4f2f-9f1a-228bde4e199a",
    "2355e8ef-82b1-4bc5-aea7-59b4efcc7268",
]


def post(path, body=None, token=None, workspace=None, method="POST"):
    data = json.dumps(body or {}).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if workspace:
        headers["X-Workspace-Id"] = workspace
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())


token = post("/api/v1/auth/dev-token", {"email": "owner@example.com", "name": "Owner", "role": "owner"})["access_token"]
for run_id in RUNS:
    try:
        gate = post(f"/api/v1/content/generation-runs/{run_id}/publish-gate", {}, token=token, workspace=WS)
        print(run_id, json.dumps(gate, ensure_ascii=False))
    except Exception as e:
        print(run_id, "ERROR", e)
    try:
        pub = post(f"/api/v1/content/generation-runs/{run_id}/publish", {}, token=token, workspace=WS)
        print(run_id, "PUBLISH", json.dumps(pub, ensure_ascii=False))
    except Exception as e:
        print(run_id, "PUBLISH_ERROR", e)
