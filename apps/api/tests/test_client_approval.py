"""Unit tests for client approval service."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from exposureflow_api.common.errors import APIError
from exposureflow_api.reporting.service import set_roadmap_client_approval


@pytest.mark.asyncio
async def test_set_roadmap_client_approval_not_found() -> None:
    db = AsyncMock()
    db.get = AsyncMock(return_value=None)
    with pytest.raises(APIError) as exc:
        await set_roadmap_client_approval(
            db, uuid4(), uuid4(), site_id=uuid4(), approval="approved", actor_user_id=uuid4()
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_set_roadmap_client_approval_success() -> None:
    db = AsyncMock()
    ws = uuid4()
    item_id = uuid4()
    item = SimpleNamespace(id=item_id, workspace_id=ws, site_id=uuid4(), client_approval_status="pending")
    db.get = AsyncMock(return_value=item)
    db.flush = AsyncMock()
    with patch("exposureflow_api.reporting.service.record_audit", new_callable=AsyncMock):
        updated = await set_roadmap_client_approval(
            db, ws, item_id, site_id=item.site_id, approval="approved", actor_user_id=uuid4()
        )
    assert updated.client_approval_status == "approved"


@pytest.mark.asyncio
async def test_set_roadmap_client_approval_site_mismatch() -> None:
    db = AsyncMock()
    ws = uuid4()
    item_id = uuid4()
    item = SimpleNamespace(id=item_id, workspace_id=ws, site_id=uuid4(), client_approval_status="pending")
    db.get = AsyncMock(return_value=item)
    with pytest.raises(APIError) as exc:
        await set_roadmap_client_approval(
            db, ws, item_id, site_id=uuid4(), approval="approved", actor_user_id=uuid4()
        )
    assert exc.value.status_code == 403
