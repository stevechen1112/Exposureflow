"""Route execution jobs to the correct adapter."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.execution.adapters.outreach import run_outreach_adapter
from exposureflow_api.execution.adapters.refresh import run_refresh_adapter
from exposureflow_api.execution.adapters.schema_enhancement import run_schema_adapter
from exposureflow_api.execution.adapters.technical_fix import run_technical_fix_adapter
from exposureflow_api.models.execution_content import ExecutionJob

ADAPTERS = {
    "refresh_page": run_refresh_adapter,
    "refresh": run_refresh_adapter,
    "add_schema": run_schema_adapter,
    "schema_enhancement": run_schema_adapter,
    "add_faq": run_schema_adapter,
    "technical_fix": run_technical_fix_adapter,
    "fix_indexability": run_technical_fix_adapter,
    "fix_ai_crawler_access": run_technical_fix_adapter,
    "outreach_to_third_party": run_outreach_adapter,
    "create_linkable_asset": run_outreach_adapter,
}


async def dispatch_execution_job(db: AsyncSession, job: ExecutionJob) -> ExecutionJob:
    handler = ADAPTERS.get(job.job_type)
    if handler is None:
        job.status = "failed"
        job.error_message = f"No adapter for job_type={job.job_type}"
        job.completed_at = datetime.now(timezone.utc)
        await db.flush()
        return job

    job.status = "running"
    job.started_at = datetime.now(timezone.utc)
    result = handler(job.input_json or {})
    job.completed_at = datetime.now(timezone.utc)
    if result.success:
        job.status = "completed"
        job.output_json = result.output
        job.error_message = None
    else:
        job.status = "failed"
        job.error_message = result.error_message
        job.output_json = result.output
    await db.flush()
    return job
