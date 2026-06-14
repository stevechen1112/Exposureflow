"""Decision plane tenant isolation integration tests."""

from uuid import UUID

import pytest
from httpx import AsyncClient

from exposureflow_api.models import ActionCandidate


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
async def test_action_candidates_not_visible_across_workspaces(
    client: AsyncClient, engine
) -> None:
    token_a, workspace_a, site_a = await _bootstrap_user(client, "dec-a@example.com", "DEC A")
    token_b, workspace_b, _site_b = await _bootstrap_user(client, "dec-b@example.com", "DEC B")

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from exposureflow_api.models import ExposureOpportunity

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as db:
        opp = ExposureOpportunity(
            workspace_id=UUID(workspace_a),
            site_id=UUID(site_a),
            opportunity_type="refresh_page",
            reason="isolation test",
            priority="medium",
        )
        db.add(opp)
        await db.flush()
        db.add(
            ActionCandidate(
                workspace_id=UUID(workspace_a),
                site_id=UUID(site_a),
                opportunity_id=opp.id,
                action_type="refresh_page",
                expected_exposure_impact=50,
                risk_level="medium",
            )
        )
        await db.commit()

    own = await client.get(
        "/api/v1/decisions/candidates",
        params={"site_id": site_a},
        headers={"Authorization": f"Bearer {token_a}", "X-Workspace-Id": workspace_a},
    )
    assert own.status_code == 200
    assert len(own.json()) == 1

    cross = await client.get(
        "/api/v1/decisions/candidates",
        params={"site_id": site_a},
        headers={"Authorization": f"Bearer {token_b}", "X-Workspace-Id": workspace_b},
    )
    assert cross.status_code == 200
    assert cross.json() == []
