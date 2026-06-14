"""Enterprise IP allowlist enforcement."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.common.errors import APIError
from exposureflow_api.models.security_compliance import WorkspaceSecuritySettings


async def get_security_settings(
    db: AsyncSession, workspace_id: UUID
) -> WorkspaceSecuritySettings | None:
    result = await db.execute(
        select(WorkspaceSecuritySettings).where(
            WorkspaceSecuritySettings.workspace_id == workspace_id
        )
    )
    return result.scalar_one_or_none()


async def ensure_ip_allowed(
    db: AsyncSession,
    workspace_id: UUID,
    client_ip: str | None,
) -> None:
    settings = await get_security_settings(db, workspace_id)
    if settings is None or not settings.ip_allowlist:
        return
    if client_ip is None:
        raise APIError(
            code="IP_ALLOWLIST_DENIED",
            message="Client IP required for this workspace.",
            status_code=403,
        )
    if client_ip not in settings.ip_allowlist:
        raise APIError(
            code="IP_ALLOWLIST_DENIED",
            message="Your IP is not allowed for this workspace.",
            status_code=403,
        )
