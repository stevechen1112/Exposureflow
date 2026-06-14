"""Ingestion layer tenant isolation integration tests."""

from datetime import date
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.models import GscPerformanceRow


async def _bootstrap_user(client: AsyncClient, email: str, name: str) -> tuple[str, str, str]:
    token_resp = await client.post(
        "/api/v1/auth/dev-token",
        json={"email": email, "name": name},
    )
    assert token_resp.status_code == 200
    token = token_resp.json()["access_token"]
    ws_resp = await client.get("/api/v1/workspaces", headers={"Authorization": f"Bearer {token}"})
    workspace_id = ws_resp.json()[0]["id"]
    site_resp = await client.post(
        "/api/v1/sites",
        headers={"Authorization": f"Bearer {token}", "X-Workspace-Id": workspace_id},
        json={"domain": f"{email.split('@')[0]}.example.com", "site_name": name},
    )
    assert site_resp.status_code == 200
    site_id = site_resp.json()["id"]
    return token, workspace_id, site_id


@pytest.mark.asyncio
async def test_gsc_performance_not_visible_across_workspaces(
    client: AsyncClient, engine
) -> None:
    token_a, workspace_a, site_a = await _bootstrap_user(client, "ingest-a@example.com", "Ingest A")
    token_b, workspace_b, _site_b = await _bootstrap_user(client, "ingest-b@example.com", "Ingest B")

    from sqlalchemy.ext.asyncio import async_sessionmaker

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as db:
        db.add(
            GscPerformanceRow(
                workspace_id=UUID(workspace_a),
                site_id=UUID(site_a),
                date=date(2026, 6, 1),
                query="secret query",
                page="https://ingest-a.example.com/page",
                country="twn",
                device="DESKTOP",
                impressions=999,
                clicks=50,
                ctr=0.05,
                position=3.0,
            )
        )
        await db.commit()

    own = await client.get(
        "/api/v1/integrations/gsc/performance",
        params={"site_id": site_a},
        headers={"Authorization": f"Bearer {token_a}", "X-Workspace-Id": workspace_a},
    )
    assert own.status_code == 200
    assert len(own.json()) == 1
    assert own.json()[0]["query"] == "secret query"

    cross_workspace = await client.get(
        "/api/v1/integrations/gsc/performance",
        params={"site_id": site_a},
        headers={"Authorization": f"Bearer {token_b}", "X-Workspace-Id": workspace_b},
    )
    assert cross_workspace.status_code == 200
    assert cross_workspace.json() == []

    denied_header = await client.get(
        "/api/v1/integrations/gsc/performance",
        params={"site_id": site_a},
        headers={"Authorization": f"Bearer {token_b}", "X-Workspace-Id": workspace_a},
    )
    assert denied_header.status_code == 403


@pytest.mark.asyncio
async def test_integration_sync_trigger_requires_workspace_access(client: AsyncClient) -> None:
    token_a, workspace_a, site_a = await _bootstrap_user(client, "sync-a@example.com", "Sync A")
    token_b, workspace_b, _ = await _bootstrap_user(client, "sync-b@example.com", "Sync B")

    allowed = await client.post(
        "/api/v1/integrations/gsc/sync",
        headers={"Authorization": f"Bearer {token_a}", "X-Workspace-Id": workspace_a},
        json={"site_id": site_a, "input_json": {}},
    )
    assert allowed.status_code == 200
    assert "job_run_id" in allowed.json()

    denied = await client.post(
        "/api/v1/integrations/gsc/sync",
        headers={"Authorization": f"Bearer {token_b}", "X-Workspace-Id": workspace_a},
        json={"site_id": site_a, "input_json": {}},
    )
    assert denied.status_code == 403
