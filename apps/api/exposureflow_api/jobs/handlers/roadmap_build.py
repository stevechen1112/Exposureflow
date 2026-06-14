"""Build exposure roadmap from approved decisions."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.decision import service as decision_service
from exposureflow_api.integrations.sync_helpers import finalize_job_run
from exposureflow_api.models import JobRun


async def run_roadmap_build(db: AsyncSession, run: JobRun) -> None:
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
    horizon_weeks = int((run.input_json or {}).get("horizon_weeks") or 8)
    title = (run.input_json or {}).get("title")
    if horizon_weeks not in {4, 8, 16}:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="INVALID_HORIZON",
            error_message="horizon_weeks must be 4, 8, or 16",
        )
        return
    roadmap = await decision_service.build_site_roadmap(
        db,
        run.workspace_id,
        UUID(str(site_id)),
        horizon_weeks=horizon_weeks,
        title=title,
    )
    await finalize_job_run(
        run,
        success=True,
        output={"roadmap_id": str(roadmap.id), "horizon_weeks": horizon_weeks},
    )
