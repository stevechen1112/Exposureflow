"""Dispatch job runs to provider-specific handlers."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.jobs.handlers.bing_sync import run_bing_sync
from exposureflow_api.jobs.handlers.indexability_coverage_check import run_indexability_coverage_check
from exposureflow_api.jobs.handlers.indexability_published_noindex import run_indexability_published_noindex
from exposureflow_api.jobs.handlers.indexability_sitemap_health import run_indexability_sitemap_health
from exposureflow_api.jobs.handlers.integration_health import run_integration_health_check
from exposureflow_api.jobs.handlers.ga4_sync import run_ga4_sync
from exposureflow_api.jobs.handlers.gsc_sync import run_gsc_sync
from exposureflow_api.jobs.handlers.serp_snapshot import run_serp_snapshot
from exposureflow_api.jobs.handlers.tech_seo_crawl import run_tech_seo_crawl
from exposureflow_api.jobs.handlers.topic_graph_rebuild import run_topic_graph_rebuild
from exposureflow_api.jobs.handlers.decision_generate import run_decision_candidates_generate
from exposureflow_api.jobs.handlers.roadmap_build import run_roadmap_build
from exposureflow_api.jobs.handlers.content_generate import run_content_generate_grounded_draft
from exposureflow_api.jobs.handlers.content_scheduled_batch import run_content_scheduled_batch
from exposureflow_api.jobs.handlers.content_publish_gate import run_content_publish_gate
from exposureflow_api.jobs.handlers.wordpress_publish import run_wordpress_publish_draft
from exposureflow_api.jobs.handlers.knowledge_ingest import run_knowledge_source_ingest
from exposureflow_api.jobs.handlers.knowledge_embed import run_knowledge_fact_embed
from exposureflow_api.jobs.handlers.cold_start_research import run_cold_start_research
from exposureflow_api.jobs.handlers.execution_run import run_execution_job
from exposureflow_api.jobs.handlers.report_monthly_generate import run_report_monthly_generate
from exposureflow_api.integrations.sync_helpers import finalize_job_run
from exposureflow_api.models import JobRun

HANDLERS = {
    "gsc.sync": run_gsc_sync,
    "ga4.sync": run_ga4_sync,
    "serp.snapshot": run_serp_snapshot,
    "tech_seo.crawl": run_tech_seo_crawl,
    "bing.sync": run_bing_sync,
    "indexability.sitemap_health": run_indexability_sitemap_health,
    "indexability.published_noindex": run_indexability_published_noindex,
    "indexability.coverage_check": run_indexability_coverage_check,
    "integration.health_check": run_integration_health_check,
    "topic_graph.rebuild": run_topic_graph_rebuild,
    "decision.candidates.generate": run_decision_candidates_generate,
    "roadmap.build": run_roadmap_build,
    "content.generate.grounded_draft": run_content_generate_grounded_draft,
    "content.scheduled_batch": run_content_scheduled_batch,
    "content.publish_gate.check": run_content_publish_gate,
    "wordpress.publish_draft": run_wordpress_publish_draft,
    "knowledge.source.ingest": run_knowledge_source_ingest,
    "knowledge.fact.embed": run_knowledge_fact_embed,
    "strategy.cold_start_research": run_cold_start_research,
    "execution.job.run": run_execution_job,
    "report.monthly.generate": run_report_monthly_generate,
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
