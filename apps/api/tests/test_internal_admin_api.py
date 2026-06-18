"""Phase 13 internal admin and notifications integration tests."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from exposureflow_api.database import async_session_factory
from exposureflow_api.models import User, WorkspaceMembership


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


async def _grant_support_admin(email: str) -> None:
    async with async_session_factory() as session:
        user = (await session.execute(select(User).where(User.email == email))).scalar_one()
        membership = (
            await session.execute(
                select(WorkspaceMembership).where(WorkspaceMembership.user_id == user.id).limit(1)
            )
        ).scalar_one()
        membership.role = "support_admin"
        await session.commit()


@pytest.mark.asyncio
async def test_internal_admin_workspaces_as_support_admin(client: AsyncClient) -> None:
    token, _ws = await _auth(client, "admin-support@example.com", "Support Admin")
    await _grant_support_admin("admin-support@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.get("/api/v1/internal/workspaces", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_internal_admin_denied_for_analyst(client: AsyncClient) -> None:
    token, ws_id = await _auth(client, "admin-analyst@example.com", "Admin Analyst")
    async with async_session_factory() as session:
        user = (await session.execute(select(User).where(User.email == "admin-analyst@example.com"))).scalar_one()
        membership = (
            await session.execute(
                select(WorkspaceMembership).where(
                    WorkspaceMembership.workspace_id == ws_id,
                    WorkspaceMembership.user_id == user.id,
                )
            )
        ).scalar_one()
        membership.role = "analyst"
        await session.commit()

    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.get("/api/v1/internal/workspaces", headers=headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_notifications_and_support_ticket(client: AsyncClient) -> None:
    token, ws_id = await _auth(client, "notify@example.com", "Notify User")
    headers = {"Authorization": f"Bearer {token}", "X-Workspace-Id": ws_id}

    ticket = await client.post(
        "/api/v1/support/tickets",
        headers=headers,
        json={"subject": "Sync issue", "description": "GSC failed twice", "priority": "high"},
    )
    assert ticket.status_code == 200
    assert ticket.json()["subject"] == "Sync issue"

    notes = await client.get("/api/v1/notifications", headers=headers)
    assert notes.status_code == 200
    assert isinstance(notes.json(), list)


@pytest.mark.asyncio
async def test_public_status_page(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/status")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_cs_funnel_and_integration_health(client: AsyncClient) -> None:
    token, _ws = await _auth(client, "cs-admin@example.com", "CS Admin")
    await _grant_support_admin("cs-admin@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    funnel = await client.get("/api/v1/internal/cs/onboarding-funnel", headers=headers)
    assert funnel.status_code == 200
    body = funnel.json()
    assert "total_workspaces" in body

    health = await client.get("/api/v1/internal/integration-health", headers=headers)
    assert health.status_code == 200

    costs = await client.get("/api/v1/internal/provider-costs?days=30", headers=headers)
    assert costs.status_code == 200


@pytest.mark.asyncio
async def test_status_incident_admin_create(client: AsyncClient) -> None:
    token, _ws = await _auth(client, "status-admin@example.com", "Status Admin")
    await _grant_support_admin("status-admin@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    created = await client.post(
        "/api/v1/internal/status/incidents",
        headers=headers,
        json={
            "title": "API latency",
            "summary": "Elevated latency in TW region",
            "severity": "minor",
            "affected_components": ["api"],
            "is_public": True,
        },
    )
    assert created.status_code == 200
    assert created.json()["title"] == "API latency"

    public = await client.get("/api/v1/status")
    assert public.status_code == 200
    titles = [row["title"] for row in public.json()]
    assert "API latency" in titles


@pytest.mark.asyncio
async def test_ops_maintenance_run_and_latest(client: AsyncClient) -> None:
    token, _ws = await _auth(client, "ops-maint@example.com", "Ops Maint")
    await _grant_support_admin("ops-maint@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    empty = await client.get("/api/v1/internal/ops-maintenance/latest", headers=headers)
    assert empty.status_code == 200
    assert empty.json()["run"] is None

    run_resp = await client.post(
        "/api/v1/internal/ops-maintenance/run",
        headers=headers,
        json={"use_llm_summary": False},
    )
    assert run_resp.status_code == 200
    body = run_resp.json()
    assert body["run"]["status"] in {"pass", "warn", "critical"}
    assert body["run"]["summary_title"]
    assert isinstance(body["signals"], list)

    latest = await client.get("/api/v1/internal/ops-maintenance/latest", headers=headers)
    assert latest.status_code == 200
    assert latest.json()["run"]["id"] == body["run"]["id"]

    runs = await client.get("/api/v1/internal/ops-maintenance/runs", headers=headers)
    assert runs.status_code == 200
    assert len(runs.json()) >= 1
