"""Workspace security settings helpers."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.models.security_compliance import WorkspaceSecuritySettings


async def get_or_create_security_settings(
    db: AsyncSession, workspace_id: UUID
) -> WorkspaceSecuritySettings:
    result = await db.execute(
        select(WorkspaceSecuritySettings).where(
            WorkspaceSecuritySettings.workspace_id == workspace_id
        )
    )
    row = result.scalar_one_or_none()
    if row is not None:
        return row
    row = WorkspaceSecuritySettings(workspace_id=workspace_id)
    db.add(row)
    await db.flush()
    return row
