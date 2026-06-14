"""Strategy layer tenant isolation integration tests."""

import pytest
from httpx import AsyncClient


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
async def test_keyword_pyramid_not_visible_across_workspaces(
    client: AsyncClient, engine
) -> None:
    token_a, workspace_a, site_a = await _bootstrap_user(client, "strat-a@example.com", "Strat A")
    token_b, workspace_b, _site_b = await _bootstrap_user(client, "strat-b@example.com", "Strat B")

    create_resp = await client.post(
        "/api/v1/strategy/keyword-pyramid",
        headers={"Authorization": f"Bearer {token_a}", "X-Workspace-Id": workspace_a},
        json={
            "site_id": site_a,
            "keyword": "private keyword",
            "node_type": "pillar",
            "business_fit_status": "in_scope",
        },
    )
    assert create_resp.status_code == 200
    node_id = create_resp.json()["id"]

    own = await client.get(
        f"/api/v1/strategy/keyword-pyramid?site_id={site_a}",
        headers={"Authorization": f"Bearer {token_a}", "X-Workspace-Id": workspace_a},
    )
    assert own.status_code == 200
    assert len(own.json()) == 1

    cross = await client.get(
        f"/api/v1/strategy/keyword-pyramid?site_id={site_a}",
        headers={"Authorization": f"Bearer {token_b}", "X-Workspace-Id": workspace_b},
    )
    assert cross.status_code == 200
    assert cross.json() == []

    denied = await client.get(
        f"/api/v1/strategy/keyword-pyramid?site_id={site_a}",
        headers={"Authorization": f"Bearer {token_b}", "X-Workspace-Id": workspace_a},
    )
    assert denied.status_code == 403

    patch_denied = await client.patch(
        f"/api/v1/strategy/keyword-pyramid/{node_id}",
        headers={"Authorization": f"Bearer {token_b}", "X-Workspace-Id": workspace_b},
        json={"business_fit_status": "blocked"},
    )
    assert patch_denied.status_code == 404


@pytest.mark.asyncio
async def test_knowledge_facts_isolated_by_workspace(client: AsyncClient, engine) -> None:
    token_a, workspace_a, site_a = await _bootstrap_user(client, "know-a@example.com", "Know A")
    token_b, workspace_b, site_b = await _bootstrap_user(client, "know-b@example.com", "Know B")

    source_resp = await client.post(
        "/api/v1/knowledge/sources",
        headers={"Authorization": f"Bearer {token_a}", "X-Workspace-Id": workspace_a},
        json={
            "site_id": site_a,
            "source_type": "manual",
            "title": "Product catalog",
        },
    )
    assert source_resp.status_code == 200
    source_id = source_resp.json()["id"]

    fact_resp = await client.post(
        "/api/v1/knowledge/facts",
        headers={"Authorization": f"Bearer {token_a}", "X-Workspace-Id": workspace_a},
        json={
            "site_id": site_a,
            "knowledge_source_id": source_id,
            "fact_type": "product_spec",
            "subject": "Pump X100",
            "fact_text": "Flow rate 500 L/min",
        },
    )
    assert fact_resp.status_code == 200

    cross = await client.get(
        f"/api/v1/knowledge/facts?site_id={site_a}",
        headers={"Authorization": f"Bearer {token_b}", "X-Workspace-Id": workspace_b},
    )
    assert cross.status_code == 200
    assert cross.json() == []

    own_b = await client.get(
        f"/api/v1/knowledge/facts?site_id={site_b}",
        headers={"Authorization": f"Bearer {token_b}", "X-Workspace-Id": workspace_b},
    )
    assert own_b.status_code == 200
    assert own_b.json() == []


@pytest.mark.asyncio
async def test_business_fit_evaluate_endpoint(client: AsyncClient) -> None:
    token, workspace_id, site_id = await _bootstrap_user(
        client, "fit-a@example.com", "Fit A"
    )

    await client.post(
        "/api/v1/strategy/keyword-pyramid",
        headers={"Authorization": f"Bearer {token}", "X-Workspace-Id": workspace_id},
        json={
            "site_id": site_id,
            "keyword": "blocked term",
            "node_type": "cluster",
            "business_fit_status": "blocked",
        },
    )

    eval_resp = await client.post(
        "/api/v1/strategy/business-fit/evaluate",
        headers={"Authorization": f"Bearer {token}", "X-Workspace-Id": workspace_id},
        json={"site_id": site_id, "keyword": "blocked term"},
    )
    assert eval_resp.status_code == 200
    body = eval_resp.json()
    assert body["business_fit_score"] == 0.0
    assert body["blocked"] is True
