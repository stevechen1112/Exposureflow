"""Workspace and account data deletion."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.common.audit import record_audit
from exposureflow_api.models import IntegrationCredential, Site, Workspace, WorkspaceMembership
from exposureflow_api.models.security_compliance import WorkspaceSecuritySettings
from exposureflow_api.security.settings import get_or_create_security_settings


async def request_workspace_deletion(
    db: AsyncSession,
    *,
    workspace_id: UUID,
    actor_user_id: UUID,
) -> WorkspaceSecuritySettings:
    settings = await get_or_create_security_settings(db, workspace_id)
    settings.deletion_status = "pending_deletion"
    settings.deletion_requested_at = datetime.now(UTC)

    ws = await db.get(Workspace, workspace_id)
    if ws:
        ws.status = "pending_deletion"

    await db.execute(
        update(IntegrationCredential)
        .where(IntegrationCredential.workspace_id == workspace_id)
        .values(status="revoked")
    )
    await db.execute(
        update(WorkspaceMembership)
        .where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.user_id != actor_user_id,
        )
        .values(status="revoked")
    )
    await db.execute(
        update(Site).where(Site.workspace_id == workspace_id).values(status="deleted")
    )

    await record_audit(
        db,
        action="workspace.deletion_requested",
        target_type="workspace",
        target_id=str(workspace_id),
        workspace_id=workspace_id,
        actor_user_id=actor_user_id,
    )
    await db.flush()
    return settings


async def purge_workspace_data(
    db: AsyncSession,
    *,
    workspace_id: UUID,
    actor_user_id: UUID,
) -> None:
    """Hard purge after retention — removes integration secrets."""
    from exposureflow_api.common.errors import APIError
    from exposureflow_api.security.settings import get_or_create_security_settings

    settings = await get_or_create_security_settings(db, workspace_id)
    if settings.deletion_status != "pending_deletion":
        raise APIError(
            code="DELETION_NOT_REQUESTED",
            message="Request workspace deletion before purge.",
            status_code=400,
        )

    await db.execute(
        update(IntegrationCredential)
        .where(IntegrationCredential.workspace_id == workspace_id)
        .values(encrypted_payload="", status="purged")
    )
    settings = await get_or_create_security_settings(db, workspace_id)
    settings.deletion_status = "purged"
    ws = await db.get(Workspace, workspace_id)
    if ws:
        ws.status = "deleted"
    await record_audit(
        db,
        action="workspace.data_purged",
        target_type="workspace",
        target_id=str(workspace_id),
        workspace_id=workspace_id,
        actor_user_id=actor_user_id,
    )
    await db.flush()
