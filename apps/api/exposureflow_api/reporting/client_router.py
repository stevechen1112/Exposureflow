from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.auth.jwt import AuthContext
from exposureflow_api.auth.permissions import require_permission
from exposureflow_api.common.audit import record_audit
from exposureflow_api.common.errors import not_found
from exposureflow_api.database import get_db
from exposureflow_api.exposure.deps import get_site_in_workspace
from exposureflow_api.models.client_deliverables import ClientMeetingNote, DeliveryAnnotation
from exposureflow_api.reporting.client_portal import build_client_portal_dashboard
from exposureflow_api.reporting.schemas import (
    ClientApprovalRequest,
    ClientMeetingNoteCreate,
    ClientMeetingNoteResponse,
    DeliveryAnnotationCreate,
    DeliveryAnnotationResponse,
)
from exposureflow_api.reporting.service import set_roadmap_client_approval

router = APIRouter(prefix="/api/v1/client-portal", tags=["client-portal"])


@router.get("/dashboard")
async def client_dashboard(
    site_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    return await build_client_portal_dashboard(db, workspace_id, site_id)


@router.post("/roadmap-items/{item_id}/approve")
async def client_approve_roadmap_item(
    item_id: UUID,
    body: ClientApprovalRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("client:approve")),
    db: AsyncSession = Depends(get_db),
):
    user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, body.site_id)
    item = await set_roadmap_client_approval(
        db,
        workspace_id,
        item_id,
        site_id=body.site_id,
        approval="approved",
        actor_user_id=user.user_id,
        note=body.note,
    )
    await db.commit()
    await db.refresh(item)
    return {"id": str(item.id), "client_approval_status": item.client_approval_status}


@router.post("/roadmap-items/{item_id}/reject")
async def client_reject_roadmap_item(
    item_id: UUID,
    body: ClientApprovalRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("client:approve")),
    db: AsyncSession = Depends(get_db),
):
    user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, body.site_id)
    item = await set_roadmap_client_approval(
        db,
        workspace_id,
        item_id,
        site_id=body.site_id,
        approval="rejected",
        actor_user_id=user.user_id,
        note=body.note,
    )
    await db.commit()
    await db.refresh(item)
    return {"id": str(item.id), "client_approval_status": item.client_approval_status}


@router.get("/meeting-notes", response_model=list[ClientMeetingNoteResponse])
async def list_meeting_notes(
    site_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
) -> list[ClientMeetingNote]:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, site_id)
    result = await db.execute(
        select(ClientMeetingNote)
        .where(
            ClientMeetingNote.workspace_id == workspace_id,
            ClientMeetingNote.site_id == site_id,
        )
        .order_by(ClientMeetingNote.meeting_date.desc())
    )
    return list(result.scalars().all())


@router.post("/meeting-notes", response_model=ClientMeetingNoteResponse)
async def create_meeting_note(
    body: ClientMeetingNoteCreate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("job:write")),
    db: AsyncSession = Depends(get_db),
) -> ClientMeetingNote:
    user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, body.site_id)
    row = ClientMeetingNote(
        workspace_id=workspace_id,
        site_id=body.site_id,
        meeting_date=body.meeting_date,
        title=body.title,
        summary=body.summary,
        action_items_json=body.action_items_json,
        created_by=user.user_id,
    )
    db.add(row)
    await db.flush()
    await record_audit(
        db,
        action="client.meeting_note.create",
        target_type="client_meeting_note",
        target_id=str(row.id),
        workspace_id=workspace_id,
        actor_user_id=user.user_id,
    )
    await db.commit()
    await db.refresh(row)
    return row


@router.post("/annotations", response_model=DeliveryAnnotationResponse)
async def create_annotation(
    body: DeliveryAnnotationCreate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("client:approve")),
    db: AsyncSession = Depends(get_db),
) -> DeliveryAnnotation:
    user, _membership, workspace_id = ctx
    if body.report_id:
        from exposureflow_api.models.reporting import Report

        report = await db.get(Report, body.report_id)
        if report is None or report.workspace_id != workspace_id:
            raise not_found("Report")
    if body.roadmap_item_id:
        from exposureflow_api.models import RoadmapItem

        item = await db.get(RoadmapItem, body.roadmap_item_id)
        if item is None or item.workspace_id != workspace_id:
            raise not_found("Roadmap item")
    row = DeliveryAnnotation(
        workspace_id=workspace_id,
        report_id=body.report_id,
        roadmap_item_id=body.roadmap_item_id,
        author_user_id=user.user_id,
        annotation_type=body.annotation_type,
        body=body.body,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row
