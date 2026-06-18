"""Weekly index coverage check — OG-013 undiscovered published URLs."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from connectors.indexability.coverage import filter_urls_older_than
from connectors.indexability.verifier import url_present_in_sitemap
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.exposure.service import generate_opportunities_from_indexability
from exposureflow_api.indexability.queries import list_live_published_urls
from exposureflow_api.integrations.sync_helpers import (
    finalize_job_run,
    get_credential,
    get_site,
)
from exposureflow_api.models import IntegrationSyncState, JobRun


async def run_indexability_coverage_check(db: AsyncSession, run: JobRun) -> None:
    site_id = run.site_id
    if site_id is None:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="MISSING_SITE",
            error_message="site_id is required for indexability.coverage_check",
        )
        return

    site = await get_site(db, run.workspace_id, site_id)
    if site is None:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="SITE_NOT_FOUND",
            error_message="Site not found",
        )
        return

    credential = await get_credential(db, run.workspace_id, site_id, "gsc")
    if credential is None:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="CREDENTIAL_MISSING",
            error_message="GSC credential required for indexability.coverage_check",
        )
        return

    sync_result = await db.execute(
        select(IntegrationSyncState).where(
            IntegrationSyncState.workspace_id == run.workspace_id,
            IntegrationSyncState.site_id == site_id,
            IntegrationSyncState.provider == "gsc",
        )
    )
    sync_state = sync_result.scalar_one_or_none()
    max_sync_age_days = int(run.input_json.get("max_sync_age_days", 30))
    if sync_state is None or sync_state.last_success_at is None:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="GSC_SYNC_STALE",
            error_message="GSC sync has never succeeded for this site",
        )
        return

    sync_age = datetime.now(UTC) - sync_state.last_success_at
    if sync_age > timedelta(days=max_sync_age_days):
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="GSC_SYNC_STALE",
            error_message=f"GSC sync older than {max_sync_age_days} days",
        )
        return

    published = await list_live_published_urls(
        db,
        run.workspace_id,
        site_id,
        days_back=60,
    )
    min_age_days = int(run.input_json.get("min_age_days", 7))
    candidate_urls = filter_urls_older_than(
        [(record.url, record.published_at) for record in published],
        min_age_days=min_age_days,
    )

    site_base = f"https://{site.domain}".rstrip("/")
    contentflow_cred = await get_credential(db, run.workspace_id, site_id, "contentflow")
    if contentflow_cred is not None:
        from execution_adapters.contentflow import parse_contentflow_credentials

        from exposureflow_api.integrations.sync_helpers import decrypt_credential_payload

        cf = parse_contentflow_credentials(decrypt_credential_payload(contentflow_cred))
        site_base = cf.site_url.rstrip("/")

    missing_urls: list[str] = []
    for url in candidate_urls:
        in_sitemap = await asyncio.to_thread(
            url_present_in_sitemap,
            url,
            site_base_url=site_base,
        )
        if not in_sitemap:
            missing_urls.append(url)

    opportunities_created = 0
    if missing_urls:
        opportunities_created = await generate_opportunities_from_indexability(
            db,
            run.workspace_id,
            site_id,
            missing_urls,
        )

    await db.flush()
    await finalize_job_run(
        run,
        success=True,
        output={
            "published_urls_tracked": len(published),
            "candidate_urls": len(candidate_urls),
            "missing_from_sitemap": missing_urls,
            "opportunities_created": opportunities_created,
        },
        provider="indexability",
    )
