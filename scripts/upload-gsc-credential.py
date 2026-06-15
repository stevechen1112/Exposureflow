"""One-off: upload GSC service account credential to ExposureFlow API."""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://app.kakusinn.com"
WORKSPACE_ID = "67a1694d-fab1-4694-b05c-37790ef8ef87"
SITE_ID = "02cb80a6-75ef-4a0a-b2b3-8911d650579e"
KEY_PATH = Path(__file__).resolve().parent.parent / "exposureflow-gsc-3c99151c5773.json"


def post(url: str, body: dict, headers: dict | None = None) -> dict:
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def get(url: str, headers: dict) -> list | dict:
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def main() -> int:
    sa = KEY_PATH.read_text(encoding="utf-8")
    token = post(f"{BASE}/api/v1/auth/dev-token", {"email": "owner@example.com", "name": "Owner", "role": "owner"})[
        "access_token"
    ]
    hdrs = {"Authorization": f"Bearer {token}", "X-Workspace-Id": WORKSPACE_ID}

    creds = get(f"{BASE}/api/v1/integrations/credentials?site_id={SITE_ID}", hdrs)
    gsc_cred = next((c for c in creds if c.get("provider") == "gsc"), None)
    if gsc_cred:
        print("CREDENTIAL_EXISTS", gsc_cred.get("id"), gsc_cred.get("status"))
    else:
        try:
            cred = post(
                f"{BASE}/api/v1/integrations/credentials",
                {
                    "provider": "gsc",
                    "credential_type": "service_account",
                    "site_id": SITE_ID,
                    "credential_name": "default",
                    "payload": sa,
                },
                hdrs,
            )
            print("CREDENTIAL_OK", cred.get("id"), cred.get("status"))
        except urllib.error.HTTPError as exc:
            print("CREDENTIAL_ERR", exc.code, exc.read().decode())
            return 1

    sync = post(
        f"{BASE}/api/v1/integrations/gsc/sync",
        {"site_id": SITE_ID, "input_json": {"site_url": "sc-domain:ezfix.com.tw"}},
        hdrs,
    )
    print("SYNC_QUEUED", sync.get("job_run_id"), sync.get("status"))

    import time

    time.sleep(8)
    states = get(f"{BASE}/api/v1/integrations/sync-states?site_id={SITE_ID}", hdrs)
    gsc = next((s for s in states if s.get("provider") == "gsc"), states[0] if states else {})
    print("SYNC_STATE", json.dumps(gsc, ensure_ascii=False))

    summary = get(f"{BASE}/api/v1/integrations/gsc/summary?site_id={SITE_ID}", hdrs)
    print("GSC_SUMMARY", json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
