"""Phase 14 launch readiness and business metrics tests."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from exposureflow_api.database import async_session_factory
from exposureflow_api.models import User, WorkspaceMembership


async def _auth_support(client: AsyncClient, email: str, name: str) -> str:
    token_resp = await client.post("/api/v1/auth/dev-token", json={"email": email, "name": name})
    assert token_resp.status_code == 200
    token = token_resp.json()["access_token"]
    async with async_session_factory() as session:
        user = (await session.execute(select(User).where(User.email == email))).scalar_one()
        membership = (
            await session.execute(select(WorkspaceMembership).where(WorkspaceMembership.user_id == user.id).limit(1))
        ).scalar_one()
        membership.role = "support_admin"
        await session.commit()
    return token


@pytest.mark.asyncio
async def test_public_launch_readiness(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/launch/readiness")
    assert resp.status_code == 200
    body = resp.json()
    assert "overall" in body
    assert "checks" in body
    assert body["total"] > 0


@pytest.mark.asyncio
async def test_internal_launch_checklist(client: AsyncClient) -> None:
    token = await _auth_support(client, "launch-support@example.com", "Launch Support")
    resp = await client.get(
        "/api/v1/internal/launch/checklist",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["overall"] in {"ready", "not_ready"}
    ids = [c["id"] for c in body["checks"]]
    assert "ops.backup_runbook" in ids


@pytest.mark.asyncio
async def test_business_metrics(client: AsyncClient) -> None:
    token = await _auth_support(client, "metrics-support@example.com", "Metrics Support")
    resp = await client.get(
        "/api/v1/internal/business-metrics?days=30",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "product_activation_rate" in body
    assert "gross_margin_by_plan" in body
    assert "funnel" in body
