"""In-app and email notification delivery."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.config import settings
from exposureflow_api.models.product_ops import Notification

logger = logging.getLogger(__name__)


async def create_notification(
    db: AsyncSession,
    *,
    workspace_id: UUID,
    notification_type: str,
    title: str,
    body: str,
    severity: str = "info",
    user_id: UUID | None = None,
    link_url: str | None = None,
    metadata: dict | None = None,
    send_email: bool = True,
    dedupe_hours: int | None = 24,
) -> Notification | None:
    if dedupe_hours:
        since = datetime.now(UTC) - timedelta(hours=dedupe_hours)
        target_id = (metadata or {}).get("target_id")
        stmt = select(Notification).where(
            Notification.workspace_id == workspace_id,
            Notification.notification_type == notification_type,
            Notification.created_at >= since,
        )
        if target_id:
            stmt = stmt.where(Notification.metadata_json["target_id"].astext == str(target_id))
        existing = (await db.execute(stmt.limit(1))).scalar_one_or_none()
        if existing is not None:
            return existing

    row = Notification(
        workspace_id=workspace_id,
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        body=body,
        severity=severity,
        link_url=link_url,
        metadata_json=metadata or {},
    )
    db.add(row)
    await db.flush()
    if send_email:
        await _dispatch_email(row)
    return row


async def _dispatch_email(notification: Notification) -> None:
    if not settings.notification_email_enabled:
        notification.metadata_json = {
            **notification.metadata_json,
            "email_skipped": "notifications disabled",
        }
        return
    logger.info(
        "notification_email",
        extra={
            "workspace_id": str(notification.workspace_id),
            "type": notification.notification_type,
            "title": notification.title,
        },
    )
    notification.email_sent_at = datetime.now(UTC)
    notification.metadata_json = {**notification.metadata_json, "email_channel": "log"}


async def notify_sync_failure(
    db: AsyncSession,
    *,
    workspace_id: UUID,
    site_id: UUID,
    provider: str,
    error: str,
) -> Notification:
    return await create_notification(
        db,
        workspace_id=workspace_id,
        notification_type="sync_failure",
        title=f"{provider.upper()} 同步失敗",
        body=error[:500],
        severity="error",
        link_url=f"{settings.app_base_url}/app",
        metadata={"site_id": str(site_id), "provider": provider},
        dedupe_hours=6,
    )


async def notify_quota_warning(
    db: AsyncSession,
    *,
    workspace_id: UUID,
    metric: str,
    used: int,
    limit: int,
) -> Notification | None:
    if limit <= 0:
        return None
    ratio = used / limit
    if ratio < 0.8:
        return None
    severity = "warning" if ratio < 1 else "error"
    return await create_notification(
        db,
        workspace_id=workspace_id,
        notification_type="quota_warning",
        title="配額警示" if ratio < 1 else "配額已用盡",
        body=f"{metric} 已使用 {used}/{limit}（{int(ratio * 100)}%）",
        severity=severity,
        link_url=f"{settings.app_base_url}/app",
        metadata={"metric": metric, "used": used, "limit": limit},
    )


async def notify_report_ready(
    db: AsyncSession,
    *,
    workspace_id: UUID,
    report_id: UUID,
    title: str,
) -> Notification:
    return await create_notification(
        db,
        workspace_id=workspace_id,
        notification_type="report_ready",
        title="報表已就緒",
        body=title,
        severity="info",
        link_url=f"{settings.app_base_url}/app",
        metadata={"report_id": str(report_id)},
    )


async def notify_approval_required(
    db: AsyncSession,
    *,
    workspace_id: UUID,
    target_type: str,
    target_id: UUID,
    title: str,
) -> Notification:
    return await create_notification(
        db,
        workspace_id=workspace_id,
        notification_type="approval_required",
        title="待審核",
        body=title,
        severity="warning",
        metadata={"target_type": target_type, "target_id": str(target_id)},
        dedupe_hours=48,
    )


async def list_notifications(
    db: AsyncSession,
    *,
    workspace_id: UUID,
    user_id: UUID | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[Notification]:
    stmt = select(Notification).where(Notification.workspace_id == workspace_id)
    if user_id is not None:
        stmt = stmt.where((Notification.user_id == user_id) | (Notification.user_id.is_(None)))
    if status:
        stmt = stmt.where(Notification.status == status)
    stmt = stmt.order_by(Notification.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def mark_notification_read(
    db: AsyncSession, notification_id: UUID, workspace_id: UUID, user_id: UUID
) -> Notification:
    row = await db.get(Notification, notification_id)
    if row is None or row.workspace_id != workspace_id:
        from exposureflow_api.common.errors import not_found

        raise not_found("Notification")
    if row.user_id is not None and row.user_id != user_id:
        from exposureflow_api.common.errors import APIError

        raise APIError(code="PERMISSION_DENIED", message="Cannot mark another user's notification.", status_code=403)
    row.status = "read"
    row.read_at = datetime.now(UTC)
    await db.flush()
    return row
