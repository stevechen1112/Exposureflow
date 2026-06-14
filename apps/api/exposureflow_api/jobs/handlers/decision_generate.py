"""Generate action candidates from open opportunities."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.decision import service as decision_service
from exposureflow_api.integrations.sync_helpers import finalize_job_run
from exposureflow_api.models import JobRun


async def run_decision_candidates_generate(db: AsyncSession, run: JobRun) -> None:
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
    count = await decision_service.generate_action_candidates(
        db, run.workspace_id, UUID(str(site_id))
    )
    await finalize_job_run(
        run,
        success=True,
        output={"candidates_created": count},
    )
