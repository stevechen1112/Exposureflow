"""Shared workspace listing for consultant and agency views."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.models import Workspace
from exposureflow_api.tenants.service import list_user_workspaces


async def list_client_workspaces_for_account(
    db: AsyncSession,
    *,
    account_id: UUID,
    user_id: UUID,
    include_all_account_clients: bool,
) -> list[Workspace]:
    """Client workspaces visible in cross-client consultant/agency views."""
    if include_all_account_clients:
        result = await db.execute(
            select(Workspace).where(
                Workspace.account_id == account_id,
                Workspace.status == "active",
                Workspace.workspace_type != "agency_internal",
            )
        )
        workspaces = list(result.scalars().all())
    else:
        rows = await list_user_workspaces(db, user_id)
        workspaces = [
            ws
            for ws, _role in rows
            if ws.account_id == account_id
            and ws.status == "active"
            and ws.workspace_type != "agency_internal"
        ]
    workspaces.sort(key=lambda w: (w.client_name or w.name).lower())
    return workspaces
