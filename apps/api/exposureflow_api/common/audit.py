from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.models import AuditLog


async def record_audit(
    db: AsyncSession,
    *,
    action: str,
    target_type: str,
    target_id: str | None = None,
    workspace_id: UUID | None = None,
    account_id: UUID | None = None,
    actor_user_id: UUID | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    entry = AuditLog(
        workspace_id=workspace_id,
        account_id=account_id,
        actor_user_id=actor_user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata_json=metadata or {},
    )
    db.add(entry)
    await db.flush()
    return entry
