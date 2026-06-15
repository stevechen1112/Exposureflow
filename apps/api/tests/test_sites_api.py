import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_site_crud_and_isolation(client: AsyncClient) -> None:
    owner = await client.post(
        "/api/v1/auth/dev-token",
        json={"email": "site-crud@example.com", "name": "Site CRUD"},
    )
    token = owner.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    client_ws = await client.post(
        "/api/v1/workspaces",
        headers=headers,
        json={
            "name": "Client Workspace Test",
            "workspace_type": "client",
            "client_name": "恆惠修理紗窗",
            "default_locale": "zh-TW",
        },
    )
    assert client_ws.status_code == 200
    workspace_id = client_ws.json()["id"]
    ws_headers = {**headers, "X-Workspace-Id": workspace_id}

    create = await client.post(
        "/api/v1/sites",
        headers=ws_headers,
        json={
            "domain": "https://EzFix.com.tw/path",
            "site_name": "恆惠修理紗窗",
            "target_countries": ["TW"],
            "target_languages": ["zh-TW"],
            "industry": "本地居家維修",
            "business_model": "到府服務",
        },
    )
    assert create.status_code == 200
    site = create.json()
    assert site["domain"] == "ezfix.com.tw"
    site_id = site["id"]

    get_one = await client.get(f"/api/v1/sites/{site_id}", headers=ws_headers)
    assert get_one.status_code == 200
    assert get_one.json()["site_name"] == "恆惠修理紗窗"

    patch = await client.patch(
        f"/api/v1/sites/{site_id}",
        headers=ws_headers,
        json={"site_name": "恆惠修理紗窗（台中）", "business_model": "到府服務、LINE 詢價"},
    )
    assert patch.status_code == 200
    assert patch.json()["site_name"] == "恆惠修理紗窗（台中）"

    other = await client.post(
        "/api/v1/auth/dev-token",
        json={"email": "site-other@example.com", "name": "Other"},
    )
    other_token = other.json()["access_token"]
    cross = await client.get(
        f"/api/v1/sites/{site_id}",
        headers={"Authorization": f"Bearer {other_token}", "X-Workspace-Id": workspace_id},
    )
    assert cross.status_code == 403
