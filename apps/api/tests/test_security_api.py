"""Security API integration tests."""

import pytest
from httpx import AsyncClient


async def _auth(client: AsyncClient, email: str, name: str) -> tuple[str, str]:
    token_resp = await client.post(
        "/api/v1/auth/dev-token",
        json={"email": email, "name": name},
    )
    assert token_resp.status_code == 200
    token = token_resp.json()["access_token"]
    ws_id = (
        await client.get("/api/v1/workspaces", headers={"Authorization": f"Bearer {token}"})
    ).json()[0]["id"]
    return token, ws_id


@pytest.mark.asyncio
async def test_data_export(client: AsyncClient) -> None:
    token, ws_id = await _auth(client, "export@example.com", "Export User")
    headers = {"Authorization": f"Bearer {token}", "X-Workspace-Id": ws_id}

    resp = await client.post("/api/v1/security/data-export", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ready"
    assert body["export_json"] is not None
    assert "workspace" in body["export_json"]


@pytest.mark.asyncio
async def test_security_settings_and_audit_logs(client: AsyncClient) -> None:
    token, ws_id = await _auth(client, "sec-settings@example.com", "Sec Settings")
    headers = {"Authorization": f"Bearer {token}", "X-Workspace-Id": ws_id}

    update = await client.put(
        "/api/v1/security/settings",
        headers=headers,
        json={"retention_days": 180, "ip_allowlist": ["127.0.0.1"]},
    )
    assert update.status_code == 200
    assert update.json()["retention_days"] == 180

    logs = await client.get("/api/v1/security/audit-logs", headers=headers)
    assert logs.status_code == 200
    actions = [row["action"] for row in logs.json()]
    assert "security.settings_updated" in actions


@pytest.mark.asyncio
async def test_ops_metrics(client: AsyncClient) -> None:
    token, ws_id = await _auth(client, "ops@example.com", "Ops User")
    headers = {"Authorization": f"Bearer {token}", "X-Workspace-Id": ws_id}

    metrics = await client.get("/api/v1/ops/metrics", headers=headers)
    assert metrics.status_code == 200
    assert "http_requests_total" in metrics.json()

    slo = await client.get("/api/v1/ops/slo", headers=headers)
    assert slo.status_code == 200
    assert "targets" in slo.json()


@pytest.mark.asyncio
async def test_security_cross_workspace_denied(client: AsyncClient) -> None:
    _token_a, ws_a = await _auth(client, "sec-a@example.com", "Sec A")
    token_b, _ws_b = await _auth(client, "sec-b@example.com", "Sec B")

    cross = await client.get(
        "/api/v1/security/audit-logs",
        headers={"Authorization": f"Bearer {token_b}", "X-Workspace-Id": ws_a},
    )
    assert cross.status_code == 403
