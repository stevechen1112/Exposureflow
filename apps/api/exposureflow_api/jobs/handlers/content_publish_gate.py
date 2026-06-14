"""Run publish gate for a content generation run."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.content import service as content_service
from exposureflow_api.integrations.sync_helpers import finalize_job_run
from exposureflow_api.models import JobRun


async def run_content_publish_gate(db: AsyncSession, run: JobRun) -> None:
    run_id = (run.input_json or {}).get("generation_run_id")
    if not run_id:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="MISSING_GENERATION_RUN_ID",
            error_message="generation_run_id is required",
        )
        return
    try:
        gate = await content_service.check_publish_gate(db, run.workspace_id, UUID(str(run_id)))
        await finalize_job_run(
            run,
            success=True,
            output={"gate_id": str(gate.id), "status": gate.status},
        )
    except Exception as exc:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="PUBLISH_GATE_FAILED",
            error_message=str(exc),
        )
