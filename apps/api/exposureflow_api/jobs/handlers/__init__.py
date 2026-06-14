"""Dispatch job runs to provider-specific handlers."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.jobs.handlers.bing_sync import run_bing_sync
from exposureflow_api.jobs.handlers.integration_health import run_integration_health_check
from exposureflow_api.jobs.handlers.ga4_sync import run_ga4_sync
from exposureflow_api.jobs.handlers.gsc_sync import run_gsc_sync
from exposureflow_api.jobs.handlers.serp_snapshot import run_serp_snapshot
from exposureflow_api.jobs.handlers.tech_seo_crawl import run_tech_seo_crawl
from exposureflow_api.jobs.handlers.topic_graph_rebuild import run_topic_graph_rebuild
from exposureflow_api.integrations.sync_helpers import finalize_job_run
from exposureflow_api.models import JobRun

HANDLERS = {
    "gsc.sync": run_gsc_sync,
    "ga4.sync": run_ga4_sync,
    "serp.snapshot": run_serp_snapshot,
    "tech_seo.crawl": run_tech_seo_crawl,
    "bing.sync": run_bing_sync,
    "integration.health_check": run_integration_health_check,
    "topic_graph.rebuild": run_topic_graph_rebuild,
}


async def dispatch_job_run(db: AsyncSession, run: JobRun) -> None:
    handler = HANDLERS.get(run.job_type)
    if handler is None:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="UNKNOWN_JOB_TYPE",
            error_message=f"No handler for job_type={run.job_type}",
        )
        return
    await handler(db, run)
