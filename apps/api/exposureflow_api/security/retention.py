"""Retention policy enforcement."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.models import AuditLog
from exposureflow_api.models.security_compliance import SecurityEvent
from exposureflow_api.security.settings import get_or_create_security_settings


async def apply_retention_policy(db: AsyncSession, workspace_id: UUID) -> dict[str, int]:
    settings = await get_or_create_security_settings(db, workspace_id)
    cutoff = datetime.now(UTC) - timedelta(days=settings.retention_days)

    audit_result = await db.execute(
        delete(AuditLog).where(
            AuditLog.workspace_id == workspace_id,
            AuditLog.created_at < cutoff,
        )
    )
    event_result = await db.execute(
        delete(SecurityEvent).where(
            SecurityEvent.workspace_id == workspace_id,
            SecurityEvent.created_at < cutoff,
        )
    )
    return {
        "audit_logs_deleted": audit_result.rowcount or 0,
        "security_events_deleted": event_result.rowcount or 0,
        "retention_days": settings.retention_days,
    }
