"""Strategy intake versioning and impact tests."""

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


def _intake_payload(site_id: str, *, suffix: str = "A") -> dict:
    return {
        "site_id": site_id,
        "company_summary": f"台中紗窗維修 Company {suffix}",
        "sales_regions_json": ["台中"],
        "strategic_goals_json": [
            f"提升「修理紗窗 {suffix}」「換紗窗價格 {suffix}」等服務詞能見度"
        ],
        "constraints_json": [f"不做 B2B {suffix}"],
        "change_summary": f"initial {suffix}",
    }


@pytest.mark.asyncio
async def test_intake_approve_applies_keyword_and_archives_old_version(
    client: AsyncClient, engine
) -> None:
    token, workspace_id, site_id = await _bootstrap_user(
        client, "intake-v1@example.com", "Intake V1"
    )
    headers = {"Authorization": f"Bearer {token}", "X-Workspace-Id": workspace_id}

    create_resp = await client.post(
        "/api/v1/strategy/intakes",
        headers=headers,
        json=_intake_payload(site_id, suffix="v1"),
    )
    assert create_resp.status_code == 200
    v1 = create_resp.json()
    assert v1["version_number"] == 1
    assert v1["status"] == "draft"

    approve_v1 = await client.post(
        f"/api/v1/strategy/intakes/{v1['id']}/approve",
        headers=headers,
        json={},
    )
    assert approve_v1.status_code == 200
    body = approve_v1.json()
    assert body["intake"]["status"] == "approved"
    assert body["intake"]["is_current"] is True
    assert body["impact"]["keywords_created"] >= 1

    pyramid = await client.get(
        f"/api/v1/strategy/keyword-pyramid?site_id={site_id}",
        headers=headers,
    )
    assert pyramid.status_code == 200
    pyramid_rows = pyramid.json()
    assert len(pyramid_rows) >= 1
    keywords = {row["keyword"] for row in pyramid_rows}
    assert any("修理紗窗" in keyword for keyword in keywords)
    assert not any("goal" in keyword.lower() for keyword in keywords)

    fork_resp = await client.post(
        f"/api/v1/strategy/intakes/{v1['id']}/fork",
        headers=headers,
        json={},
    )
    assert fork_resp.status_code == 200
    v2_draft = fork_resp.json()
    assert v2_draft["version_number"] == 2
    assert v2_draft["status"] == "draft"
    assert v2_draft["parent_intake_id"] == v1["id"]

    patch_resp = await client.patch(
        f"/api/v1/strategy/intakes/{v2_draft['id']}",
        headers=headers,
        json={
            "constraints_json": ["不做 B2B v1", "不做 B2B 批發"],
            "change_summary": "新增 B2B 限制",
        },
    )
    assert patch_resp.status_code == 200

    preview_resp = await client.get(
        f"/api/v1/strategy/intakes/{v2_draft['id']}/impact-preview",
        headers=headers,
    )
    assert preview_resp.status_code == 200
    preview = preview_resp.json()
    assert preview["constraint_rules_to_upsert"]
    assert preview["keywords_to_add"]
    assert not any(item.get("action") == "create_blocked" for item in preview["keywords_to_block"])

    approve_v2 = await client.post(
        f"/api/v1/strategy/intakes/{v2_draft['id']}/approve",
        headers=headers,
        json={},
    )
    assert approve_v2.status_code == 200
    approve_body = approve_v2.json()
    assert approve_body["intake"]["version_number"] == 2
    assert approve_body["intake"]["is_current"] is True

    versions = await client.get(
        f"/api/v1/strategy/intakes?site_id={site_id}",
        headers=headers,
    )
    assert versions.status_code == 200
    rows = versions.json()
    archived = [row for row in rows if row["id"] == v1["id"]][0]
    assert archived["status"] == "archived"
    assert archived["is_current"] is False


@pytest.mark.asyncio
async def test_approved_intake_cannot_be_edited(client: AsyncClient) -> None:
    token, workspace_id, site_id = await _bootstrap_user(
        client, "intake-lock@example.com", "Intake Lock"
    )
    headers = {"Authorization": f"Bearer {token}", "X-Workspace-Id": workspace_id}

    create_resp = await client.post(
        "/api/v1/strategy/intakes",
        headers=headers,
        json=_intake_payload(site_id),
    )
    intake_id = create_resp.json()["id"]
    await client.post(
        f"/api/v1/strategy/intakes/{intake_id}/approve",
        headers=headers,
        json={},
    )

    patch_resp = await client.patch(
        f"/api/v1/strategy/intakes/{intake_id}",
        headers=headers,
        json={"company_summary": "changed"},
    )
    assert patch_resp.status_code == 400
