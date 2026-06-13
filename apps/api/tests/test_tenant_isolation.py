import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_tenant_isolation_between_workspaces(client: AsyncClient) -> None:
    owner_a = await client.post(
        "/api/v1/auth/dev-token",
        json={"email": "owner-a@example.com", "name": "Owner A"},
    )
    assert owner_a.status_code == 200
    token_a = owner_a.json()["access_token"]

    owner_b = await client.post(
        "/api/v1/auth/dev-token",
        json={"email": "owner-b@example.com", "name": "Owner B"},
    )
    assert owner_b.status_code == 200
    token_b = owner_b.json()["access_token"]

    ws_a = await client.get("/api/v1/workspaces", headers={"Authorization": f"Bearer {token_a}"})
    ws_b = await client.get("/api/v1/workspaces", headers={"Authorization": f"Bearer {token_b}"})
    workspace_a_id = ws_a.json()[0]["id"]
    workspace_b_id = ws_b.json()[0]["id"]

    create_site_a = await client.post(
        "/api/v1/sites",
        headers={
            "Authorization": f"Bearer {token_a}",
            "X-Workspace-Id": workspace_a_id,
        },
        json={
            "domain": "client-a.example.com",
            "site_name": "Client A",
            "target_countries": ["TW"],
            "target_languages": ["zh-TW"],
        },
    )
    assert create_site_a.status_code == 200

    cross_read = await client.get(
        "/api/v1/sites",
        headers={
            "Authorization": f"Bearer {token_b}",
            "X-Workspace-Id": workspace_a_id,
        },
    )
    assert cross_read.status_code == 403

    own_read = await client.get(
        "/api/v1/sites",
        headers={
            "Authorization": f"Bearer {token_b}",
            "X-Workspace-Id": workspace_b_id,
        },
    )
    assert own_read.status_code == 200
    assert own_read.json() == []


@pytest.mark.asyncio
async def test_client_viewer_cannot_create_site(client: AsyncClient) -> None:
    owner = await client.post(
        "/api/v1/auth/dev-token",
        json={"email": "agency@example.com", "name": "Agency"},
    )
    token = owner.json()["access_token"]
    workspace_id = (
        await client.get("/api/v1/workspaces", headers={"Authorization": f"Bearer {token}"})
    ).json()[0]["id"]

    invite = await client.post(
        "/api/v1/invitations",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Workspace-Id": workspace_id,
        },
        json={"email": "client@example.com", "role": "client_viewer"},
    )
    assert invite.status_code == 200
    invite_token = invite.json()["invite_token"]

    viewer = await client.post(
        "/api/v1/auth/dev-token",
        json={"email": "client@example.com", "name": "Client"},
    )
    viewer_token = viewer.json()["access_token"]

    accept = await client.post(
        "/api/v1/invitations/accept",
        headers={"Authorization": f"Bearer {viewer_token}"},
        json={"token": invite_token},
    )
    assert accept.status_code == 200

    denied = await client.post(
        "/api/v1/sites",
        headers={
            "Authorization": f"Bearer {viewer_token}",
            "X-Workspace-Id": workspace_id,
        },
        json={"domain": "blocked.example.com", "site_name": "Blocked"},
    )
    assert denied.status_code == 403
