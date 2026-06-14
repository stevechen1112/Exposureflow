"""Workspace data export for GDPR / offboarding."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.models import (
    AuditLog,
    ExposureOpportunity,
    IntegrationCredential,
    Report,
    Site,
    Workspace,
    WorkspaceMembership,
)
from exposureflow_api.models.security_compliance import DataExportRequest


async def build_workspace_export(db: AsyncSession, workspace_id: UUID) -> dict:
    ws = await db.get(Workspace, workspace_id)
    if ws is None:
        raise ValueError("Workspace not found")

    sites = await db.execute(select(Site).where(Site.workspace_id == workspace_id))
    members = await db.execute(
        select(WorkspaceMembership).where(WorkspaceMembership.workspace_id == workspace_id)
    )
    opportunities = await db.execute(
        select(ExposureOpportunity).where(ExposureOpportunity.workspace_id == workspace_id).limit(5000)
    )
    reports = await db.execute(select(Report).where(Report.workspace_id == workspace_id))
    audits = await db.execute(
        select(AuditLog).where(AuditLog.workspace_id == workspace_id).order_by(AuditLog.created_at.desc()).limit(1000)
    )
    credentials = await db.execute(
        select(IntegrationCredential).where(IntegrationCredential.workspace_id == workspace_id)
    )

    return {
        "exported_at": datetime.now(UTC).isoformat(),
        "workspace": {
            "id": str(ws.id),
            "name": ws.name,
            "workspace_type": ws.workspace_type,
            "client_name": ws.client_name,
            "status": ws.status,
        },
        "sites": [
            {
                "id": str(s.id),
                "domain": s.domain,
                "site_name": s.site_name,
                "status": s.status,
            }
            for s in sites.scalars().all()
        ],
        "memberships": [
            {"user_id": str(m.user_id), "role": m.role, "status": m.status}
            for m in members.scalars().all()
        ],
        "opportunities_count": len(list(opportunities.scalars().all())),
        "reports": [
            {"id": str(r.id), "title": r.title, "status": r.status, "report_type": r.report_type}
            for r in reports.scalars().all()
        ],
        "audit_log_count": len(list(audits.scalars().all())),
        "integrations": [
            {
                "id": str(c.id),
                "provider": c.provider,
                "credential_name": c.credential_name,
                "status": c.status,
                "key_version": c.key_version,
            }
            for c in credentials.scalars().all()
        ],
    }


async def create_export_request(
    db: AsyncSession,
    *,
    workspace_id: UUID,
    requested_by: UUID,
) -> DataExportRequest:
    request = DataExportRequest(
        workspace_id=workspace_id,
        requested_by=requested_by,
        status="processing",
    )
    db.add(request)
    await db.flush()
    try:
        payload = await build_workspace_export(db, workspace_id)
        request.export_json = payload
        request.status = "ready"
        request.completed_at = datetime.now(UTC)
    except Exception as exc:  # noqa: BLE001
        request.status = "failed"
        request.error_message = str(exc)[:500]
        request.completed_at = datetime.now(UTC)
    await db.flush()
    return request
