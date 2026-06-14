"""Generate monthly exposure report via background job."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.integrations.sync_helpers import finalize_job_run
from exposureflow_api.models import JobRun
from exposureflow_api.models.reporting import Report
from exposureflow_api.reporting.monthly_report import build_monthly_exposure_markdown


async def run_report_monthly_generate(db: AsyncSession, run: JobRun) -> None:
    site_id = run.site_id
    if site_id is None:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="MISSING_SITE_ID",
            error_message="site_id is required",
        )
        return
    inp = run.input_json or {}
    period_start = date.fromisoformat(inp["period_start"]) if inp.get("period_start") else None
    period_end = date.fromisoformat(inp["period_end"]) if inp.get("period_end") else None
    branding = inp.get("branding_json") or {}
    markdown = await build_monthly_exposure_markdown(
        db,
        run.workspace_id,
        UUID(str(site_id)),
        period_start=period_start,
        period_end=period_end,
        branding=branding,
    )
    title = inp.get("title") or "Monthly Exposure Report"
    row = Report(
        workspace_id=run.workspace_id,
        site_id=UUID(str(site_id)),
        report_type="monthly_exposure",
        delivery_mode="monthly_retainer",
        period_start=period_start,
        period_end=period_end,
        status="ready",
        title=title,
        content_markdown=markdown,
        branding_json=branding,
    )
    db.add(row)
    await db.flush()
    await finalize_job_run(
        run,
        success=True,
        output={"report_id": str(row.id), "title": title},
    )
