from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.auth.jwt import AuthContext
from exposureflow_api.auth.permissions import require_permission
from exposureflow_api.common.audit import record_audit
from exposureflow_api.common.errors import APIError, not_found
from exposureflow_api.database import get_db
from exposureflow_api.exposure.deps import get_site_in_workspace
from exposureflow_api.jobs.service import enqueue_job
from exposureflow_api.models.reporting import Report
from exposureflow_api.reporting.delivery_reports import DELIVERY_BUILDERS, REPORT_TYPE_BY_MODE
from exposureflow_api.reporting.exporters import export_report
from exposureflow_api.reporting.monthly_report import build_monthly_exposure_markdown
from exposureflow_api.reporting.schemas import (
    DeliveryReportCreate,
    MonthlyReportCreate,
    ReportExportRequest,
    ReportResponse,
)

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])

_CONTENT_TYPES = {
    "markdown": "text/markdown; charset=utf-8",
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


async def _persist_report(
    db: AsyncSession,
    *,
    workspace_id: UUID,
    user: AuthContext,
    site_id: UUID,
    report_type: str,
    delivery_mode: str | None,
    title: str,
    markdown: str,
    branding_json: dict,
    period_start,
    period_end,
) -> Report:
    row = Report(
        workspace_id=workspace_id,
        site_id=site_id,
        report_type=report_type,
        delivery_mode=delivery_mode,
        period_start=period_start,
        period_end=period_end,
        status="ready",
        title=title,
        content_markdown=markdown,
        branding_json=branding_json,
        created_by=user.user_id,
    )
    db.add(row)
    await db.flush()
    await record_audit(
        db,
        action="report.generate",
        target_type="report",
        target_id=str(row.id),
        workspace_id=workspace_id,
        actor_user_id=user.user_id,
        metadata={"site_id": str(site_id), "report_type": report_type, "delivery_mode": delivery_mode},
    )
    await db.commit()
    await db.refresh(row)
    return row


@router.get("", response_model=list[ReportResponse])
async def list_reports(
    site_id: UUID | None = None,
    report_type: str | None = None,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
) -> list[Report]:
    _user, _membership, workspace_id = ctx
    stmt = select(Report).where(Report.workspace_id == workspace_id)
    if site_id:
        await get_site_in_workspace(db, workspace_id, site_id)
        stmt = stmt.where(Report.site_id == site_id)
    if report_type:
        stmt = stmt.where(Report.report_type == report_type)
    result = await db.execute(stmt.order_by(Report.created_at.desc()))
    return list(result.scalars().all())


@router.post("/monthly-exposure", response_model=ReportResponse)
async def create_monthly_exposure_report(
    body: MonthlyReportCreate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("job:write")),
    db: AsyncSession = Depends(get_db),
) -> Report:
    user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, body.site_id)
    markdown = await build_monthly_exposure_markdown(
        db,
        workspace_id,
        body.site_id,
        period_start=body.period_start,
        period_end=body.period_end,
        branding=body.branding_json,
    )
    title = body.title or "Monthly Exposure Report"
    return await _persist_report(
        db,
        workspace_id=workspace_id,
        user=user,
        site_id=body.site_id,
        report_type="monthly_exposure",
        delivery_mode="monthly_retainer",
        title=title,
        markdown=markdown,
        branding_json=body.branding_json,
        period_start=body.period_start,
        period_end=body.period_end,
    )


@router.post("/generate", response_model=ReportResponse)
async def generate_delivery_report(
    body: DeliveryReportCreate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("job:write")),
    db: AsyncSession = Depends(get_db),
) -> Report:
    user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, body.site_id)
    builder = DELIVERY_BUILDERS.get(body.delivery_mode)
    if builder is None:
        raise APIError(code="INVALID_MODE", message="Unknown delivery_mode", status_code=400)
    kwargs: dict = {"branding": body.branding_json}
    if body.delivery_mode == "monthly_retainer":
        kwargs["period_start"] = body.period_start
        kwargs["period_end"] = body.period_end
    markdown = await builder(db, workspace_id, body.site_id, **kwargs)
    report_type = REPORT_TYPE_BY_MODE[body.delivery_mode]
    titles = {
        "audit": "SEO / Exposure Audit",
        "roadmap": "Exposure Roadmap",
        "monthly_retainer": "Monthly Exposure Report",
        "execution_tracker": "Execution Tracker",
    }
    title = body.title or titles[body.delivery_mode]
    return await _persist_report(
        db,
        workspace_id=workspace_id,
        user=user,
        site_id=body.site_id,
        report_type=report_type,
        delivery_mode=body.delivery_mode,
        title=title,
        markdown=markdown,
        branding_json=body.branding_json,
        period_start=body.period_start,
        period_end=body.period_end,
    )


@router.post("/monthly-exposure/async")
async def enqueue_monthly_report(
    body: MonthlyReportCreate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("job:write")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    _user, _membership, workspace_id = ctx
    await get_site_in_workspace(db, workspace_id, body.site_id)
    run = await enqueue_job(
        db,
        workspace_id=workspace_id,
        job_type="report.monthly.generate",
        site_id=body.site_id,
        input_json={
            "period_start": body.period_start.isoformat() if body.period_start else None,
            "period_end": body.period_end.isoformat() if body.period_end else None,
            "title": body.title,
            "branding_json": body.branding_json,
        },
    )
    await db.commit()
    return {"job_run_id": str(run.id), "status": run.status}


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: UUID,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
) -> Report:
    _user, _membership, workspace_id = ctx
    row = await db.get(Report, report_id)
    if row is None or row.workspace_id != workspace_id:
        raise not_found("Report")
    return row


@router.post("/{report_id}/export")
async def export_report_file(
    report_id: UUID,
    body: ReportExportRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
) -> Response:
    _user, _membership, workspace_id = ctx
    row = await db.get(Report, report_id)
    if row is None or row.workspace_id != workspace_id:
        raise not_found("Report")
    branding = row.branding_json or {}
    export_title = branding.get("organization_name") or row.title
    content = row.content_markdown or ""
    data = export_report(content, body.format, title=export_title)  # type: ignore[arg-type]
    ext = "md" if body.format == "markdown" else body.format
    return Response(
        content=data,
        media_type=_CONTENT_TYPES[body.format],
        headers={"Content-Disposition": f'attachment; filename="report-{report_id}.{ext}"'},
    )
