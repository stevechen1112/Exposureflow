from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.auth.permissions import require_permission
from exposureflow_api.common.audit import record_audit
from exposureflow_api.database import get_db
from exposureflow_api.models.product_ops import PlatformStatusIncident, SupportTicket
from exposureflow_api.notifications import service as notification_service
from exposureflow_api.notifications.schemas import (
    NotificationResponse,
    StatusIncidentResponse,
    SupportTicketCreate,
    SupportTicketResponse,
)

router = APIRouter(prefix="/api/v1", tags=["notifications"])


@router.get("/notifications", response_model=list[NotificationResponse])
async def list_workspace_notifications(
    status: str | None = None,
    ctx: tuple[object, object, UUID] = Depends(require_permission("workspace:read")),
    db: AsyncSession = Depends(get_db),
) -> list[NotificationResponse]:
    user, _membership, workspace_id = ctx
    rows = await notification_service.list_notifications(
        db, workspace_id=workspace_id, user_id=user.user_id, status=status
    )
    return rows


@router.post("/notifications/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: UUID,
    ctx: tuple[object, object, UUID] = Depends(require_permission("workspace:read")),
    db: AsyncSession = Depends(get_db),
) -> NotificationResponse:
    user, _membership, workspace_id = ctx
    row = await notification_service.mark_notification_read(db, notification_id, workspace_id, user.user_id)
    await db.commit()
    return row


@router.post("/notifications/read-all")
async def mark_all_notifications_read(
    ctx: tuple[object, object, UUID] = Depends(require_permission("workspace:read")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from datetime import UTC, datetime

    from exposureflow_api.models.product_ops import Notification

    user, _membership, workspace_id = ctx
    await db.execute(
        update(Notification)
        .where(
            Notification.workspace_id == workspace_id,
            Notification.status == "unread",
            (Notification.user_id == user.user_id) | (Notification.user_id.is_(None)),
        )
        .values(status="read", read_at=datetime.now(UTC))
    )
    await db.commit()
    return {"status": "ok"}


@router.post("/support/tickets", response_model=SupportTicketResponse)
async def create_support_ticket(
    body: SupportTicketCreate,
    ctx: tuple[object, object, UUID] = Depends(require_permission("workspace:read")),
    db: AsyncSession = Depends(get_db),
) -> SupportTicketResponse:
    user, _membership, workspace_id = ctx
    ticket = SupportTicket(
        workspace_id=workspace_id,
        created_by_user_id=user.user_id,
        subject=body.subject,
        description=body.description,
        priority=body.priority,
    )
    db.add(ticket)
    await db.flush()
    await record_audit(
        db,
        action="support.ticket_created",
        target_type="support_ticket",
        target_id=str(ticket.id),
        workspace_id=workspace_id,
        actor_user_id=user.user_id,
    )
    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.get("/support/tickets", response_model=list[SupportTicketResponse])
async def list_support_tickets(
    ctx: tuple[object, object, UUID] = Depends(require_permission("workspace:read")),
    db: AsyncSession = Depends(get_db),
) -> list[SupportTicketResponse]:
    _user, _membership, workspace_id = ctx
    result = await db.execute(
        select(SupportTicket)
        .where(SupportTicket.workspace_id == workspace_id)
        .order_by(SupportTicket.created_at.desc())
        .limit(100)
    )
    return list(result.scalars().all())


@router.get("/status", response_model=list[StatusIncidentResponse])
async def public_status_page(db: AsyncSession = Depends(get_db)) -> list[StatusIncidentResponse]:
    result = await db.execute(
        select(PlatformStatusIncident)
        .where(PlatformStatusIncident.is_public.is_(True))
        .order_by(PlatformStatusIncident.started_at.desc())
        .limit(20)
    )
    return list(result.scalars().all())
