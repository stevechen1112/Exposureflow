"""Security event recording and suspicious activity detection."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.models.security_compliance import SecurityEvent

SUSPICIOUS_THRESHOLDS: dict[str, int] = {
    "auth.permission_denied": 10,
    "auth.ip_blocked": 5,
    "auth.2fa_failed": 5,
}


async def record_security_event(
    db: AsyncSession,
    *,
    event_type: str,
    severity: str = "info",
    workspace_id: UUID | None = None,
    account_id: UUID | None = None,
    actor_user_id: UUID | None = None,
    ip_address: str | None = None,
    metadata: dict | None = None,
) -> SecurityEvent:
    event = SecurityEvent(
        workspace_id=workspace_id,
        account_id=account_id,
        event_type=event_type,
        severity=severity,
        actor_user_id=actor_user_id,
        ip_address=ip_address,
        metadata_json=metadata or {},
    )
    db.add(event)
    await db.flush()
    return event


async def detect_suspicious_activity(
    db: AsyncSession,
    *,
    event_type: str,
    workspace_id: UUID | None = None,
    actor_user_id: UUID | None = None,
    window_minutes: int = 15,
) -> bool:
    threshold = SUSPICIOUS_THRESHOLDS.get(event_type)
    if threshold is None:
        return False
    since = datetime.now(UTC) - timedelta(minutes=window_minutes)
    query = select(func.count()).select_from(SecurityEvent).where(
        SecurityEvent.event_type == event_type,
        SecurityEvent.created_at >= since,
    )
    if workspace_id:
        query = query.where(SecurityEvent.workspace_id == workspace_id)
    if actor_user_id:
        query = query.where(SecurityEvent.actor_user_id == actor_user_id)
    count = int((await db.execute(query)).scalar_one())
    return count >= threshold
