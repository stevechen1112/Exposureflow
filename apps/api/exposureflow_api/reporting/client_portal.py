"""Client portal read models — sanitized for client_viewer."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.decision.outcomes import list_action_outcomes
from exposureflow_api.exposure.dashboard import build_dashboard_metrics
from exposureflow_api.models import RoadmapItem
from exposureflow_api.models.client_deliverables import ClientMeetingNote
from exposureflow_api.models.reporting import Report


async def build_client_portal_dashboard(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
) -> dict:
    metrics = await build_dashboard_metrics(db, workspace_id, site_id)
    reports = await db.execute(
        select(Report)
        .where(
            Report.workspace_id == workspace_id,
            Report.site_id == site_id,
            Report.status == "ready",
        )
        .order_by(Report.created_at.desc())
        .limit(5)
    )
    pending = await db.execute(
        select(RoadmapItem).where(
            RoadmapItem.workspace_id == workspace_id,
            RoadmapItem.site_id == site_id,
            RoadmapItem.client_approval_status == "pending",
        ).limit(20)
    )
    outcomes = await list_action_outcomes(db, workspace_id, site_id)
    meetings = await db.execute(
        select(ClientMeetingNote)
        .where(
            ClientMeetingNote.workspace_id == workspace_id,
            ClientMeetingNote.site_id == site_id,
        )
        .order_by(ClientMeetingNote.meeting_date.desc())
        .limit(5)
    )

    return {
        "exposure_summary": {
            "total_impressions": metrics["total_impressions"],
            "impressions_delta_pct": metrics["impressions_delta_pct"],
            "open_opportunity_count": metrics["open_opportunity_count"],
        },
        "recent_reports": [
            {
                "id": str(r.id),
                "title": r.title,
                "report_type": r.report_type,
                "delivery_mode": r.delivery_mode,
                "created_at": r.created_at.isoformat(),
            }
            for r in reports.scalars().all()
        ],
        "pending_approvals": [
            {
                "id": str(i.id),
                "title": i.title,
                "week_number": i.week_number,
                "status": i.status,
                "client_approval_status": i.client_approval_status,
            }
            for i in pending.scalars().all()
        ],
        "completed_actions": outcomes[:10],
        "meeting_notes": [
            {
                "id": str(m.id),
                "title": m.title,
                "meeting_date": m.meeting_date.isoformat(),
                "summary": m.summary[:500],
            }
            for m in meetings.scalars().all()
        ],
    }
