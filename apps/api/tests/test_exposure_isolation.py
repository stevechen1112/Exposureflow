"""Exposure layer tenant isolation integration tests."""

from datetime import date
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.models import ExposureAsset, GscPerformanceRow


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
async def test_exposure_assets_not_visible_across_workspaces(
    client: AsyncClient, engine
) -> None:
    token_a, workspace_a, site_a = await _bootstrap_user(client, "expose-a@example.com", "Expose A")
    token_b, workspace_b, _site_b = await _bootstrap_user(client, "expose-b@example.com", "Expose B")

    from sqlalchemy.ext.asyncio import async_sessionmaker

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as db:
        db.add(
            GscPerformanceRow(
                workspace_id=UUID(workspace_a),
                site_id=UUID(site_a),
                date=date(2026, 6, 1),
                query="private keyword",
                page="https://expose-a.example.com/secret",
                country="twn",
                device="DESKTOP",
                impressions=100,
                clicks=5,
                ctr=0.05,
                position=12.0,
            )
        )
        db.add(
            ExposureAsset(
                workspace_id=UUID(workspace_a),
                site_id=UUID(site_a),
                asset_type="page",
                url="https://expose-a.example.com/secret",
                status="candidate",
                total_impressions=100,
                total_clicks=5,
                metadata_json={"source": "test"},
            )
        )
        await db.commit()

    own = await client.get(
        f"/api/v1/exposure/sites/{site_a}/assets",
        headers={"Authorization": f"Bearer {token_a}", "X-Workspace-Id": workspace_a},
    )
    assert own.status_code == 200
    assert len(own.json()) == 1

    cross = await client.get(
        f"/api/v1/exposure/sites/{site_a}/assets",
        headers={"Authorization": f"Bearer {token_b}", "X-Workspace-Id": workspace_b},
    )
    assert cross.status_code == 200
    assert cross.json() == []

    denied = await client.get(
        f"/api/v1/exposure/sites/{site_a}/assets",
        headers={"Authorization": f"Bearer {token_b}", "X-Workspace-Id": workspace_a},
    )
    assert denied.status_code == 403


@pytest.mark.asyncio
async def test_merge_rejects_foreign_workspace_duplicate(
    client: AsyncClient, engine
) -> None:
    token_a, workspace_a, site_a = await _bootstrap_user(client, "merge-a@example.com", "Merge A")
    token_b, workspace_b, site_b = await _bootstrap_user(client, "merge-b@example.com", "Merge B")

    from sqlalchemy.ext.asyncio import async_sessionmaker

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as db:
        victim_asset = ExposureAsset(
            workspace_id=UUID(workspace_b),
            site_id=UUID(site_b),
            asset_type="page",
            url="https://merge-b.example.com/victim",
            status="candidate",
            total_impressions=50,
            total_clicks=2,
            metadata_json={},
        )
        attacker_canonical = ExposureAsset(
            workspace_id=UUID(workspace_a),
            site_id=UUID(site_a),
            asset_type="page",
            url="https://merge-a.example.com/canonical",
            status="candidate",
            total_impressions=10,
            total_clicks=1,
            metadata_json={},
        )
        db.add_all([victim_asset, attacker_canonical])
        await db.commit()
        await db.refresh(victim_asset)
        await db.refresh(attacker_canonical)

    merge_resp = await client.post(
        f"/api/v1/exposure/sites/{site_a}/assets/merge",
        headers={"Authorization": f"Bearer {token_a}", "X-Workspace-Id": workspace_a},
        json={
            "canonical_asset_id": str(attacker_canonical.id),
            "duplicate_asset_ids": [str(victim_asset.id)],
        },
    )
    assert merge_resp.status_code == 404

    async with session_factory() as db:
        refreshed = await db.get(ExposureAsset, victim_asset.id)
        assert refreshed is not None
        assert refreshed.status == "candidate"
        assert refreshed.total_impressions == 50
