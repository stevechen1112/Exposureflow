"""Billing API and quota integration tests."""

import pytest
from httpx import AsyncClient

from exposureflow_api.billing.quota import check_quota
from exposureflow_api.billing.service import ensure_starter_subscription, seed_plans
from exposureflow_api.common.errors import APIError
from exposureflow_api.database import async_session_factory
from exposureflow_api.execution.capacity import record_usage_event
from exposureflow_api.models.tenant import Account, Organization, Workspace


async def _auth_headers(client: AsyncClient, email: str, name: str) -> tuple[str, str]:
    token_resp = await client.post(
        "/api/v1/auth/dev-token",
        json={"email": email, "name": name},
    )
    assert token_resp.status_code == 200
    token = token_resp.json()["access_token"]
    ws_resp = await client.get(
        "/api/v1/workspaces",
        headers={"Authorization": f"Bearer {token}"},
    )
    workspace_id = ws_resp.json()[0]["id"]
    return token, workspace_id


@pytest.mark.asyncio
async def test_billing_plans_and_subscription(client: AsyncClient) -> None:
    token, workspace_id = await _auth_headers(client, "billing@example.com", "Billing User")
    headers = {"Authorization": f"Bearer {token}", "X-Workspace-Id": workspace_id}

    plans = await client.get("/api/v1/billing/plans")
    assert plans.status_code == 200
    assert len(plans.json()) >= 4

    sub = await client.get("/api/v1/billing/subscription", headers=headers)
    assert sub.status_code == 200
    body = sub.json()
    assert body["plan"]["plan_code"] == "starter"
    assert body["status"] in {"trialing", "active"}


@pytest.mark.asyncio
async def test_checkout_dev_mode(client: AsyncClient) -> None:
    token, workspace_id = await _auth_headers(client, "checkout@example.com", "Checkout User")
    headers = {"Authorization": f"Bearer {token}", "X-Workspace-Id": workspace_id}

    resp = await client.post(
        "/api/v1/billing/checkout",
        headers=headers,
        json={"plan_code": "professional", "billing_interval": "month"},
    )
    assert resp.status_code == 200
    assert resp.json()["mode"] == "dev"
    assert "checkout_url" in resp.json()


@pytest.mark.asyncio
async def test_agency_dashboard_requires_auth(client: AsyncClient) -> None:
    token, workspace_id = await _auth_headers(client, "agency@example.com", "Agency Owner")
    headers = {"Authorization": f"Bearer {token}", "X-Workspace-Id": workspace_id}

    resp = await client.get("/api/v1/agency/dashboard", headers=headers)
    assert resp.status_code == 200
    assert "client_workspaces" in resp.json()


@pytest.mark.asyncio
async def test_quota_exceeded_raises(client: AsyncClient, engine) -> None:
    async with async_session_factory() as db:
        await seed_plans(db)
        account = Account(name="Quota Account", account_type="direct")
        db.add(account)
        await db.flush()
        org = Organization(account_id=account.id, name="Org")
        db.add(org)
        await db.flush()
        ws = Workspace(
            account_id=account.id,
            organization_id=org.id,
            name="Quota WS",
            workspace_type="client",
        )
        db.add(ws)
        await db.flush()
        subscription = await ensure_starter_subscription(db, account.id)
        subscription.custom_limits_json = {"serp_snapshots_per_month": 2}
        await db.flush()
        for i in range(2):
            await record_usage_event(
                db,
                workspace_id=ws.id,
                metric="serp_snapshots",
                idempotency_key=f"serp-{i}-{ws.id}",
            )
        await db.commit()

        async with async_session_factory() as session:
            with pytest.raises(APIError) as exc:
                await check_quota(session, ws.id, "serp_snapshots")
            assert exc.value.code == "QUOTA_EXCEEDED"


@pytest.mark.asyncio
async def test_site_limit_enforced(client: AsyncClient) -> None:
    token, workspace_id = await _auth_headers(client, "site-limit@example.com", "Site Limit")
    headers = {"Authorization": f"Bearer {token}", "X-Workspace-Id": workspace_id}

    first = await client.post(
        "/api/v1/sites",
        headers=headers,
        json={
            "domain": "first.example.com",
            "site_name": "First",
            "target_countries": ["TW"],
            "target_languages": ["zh-TW"],
        },
    )
    assert first.status_code == 200

    second = await client.post(
        "/api/v1/sites",
        headers=headers,
        json={
            "domain": "second.example.com",
            "site_name": "Second",
            "target_countries": ["TW"],
            "target_languages": ["zh-TW"],
        },
    )
    assert second.status_code == 429


@pytest.mark.asyncio
async def test_billing_cross_workspace_forbidden(client: AsyncClient) -> None:
    token_a, ws_a = await _auth_headers(client, "bill-a@example.com", "Bill A")
    token_b, _ws_b = await _auth_headers(client, "bill-b@example.com", "Bill B")

    cross = await client.get(
        "/api/v1/billing/subscription",
        headers={"Authorization": f"Bearer {token_b}", "X-Workspace-Id": ws_a},
    )
    assert cross.status_code == 403
