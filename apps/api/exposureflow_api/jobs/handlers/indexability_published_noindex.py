"""Daily published-article noindex / robots audit job handler."""

from __future__ import annotations

import asyncio

from connectors.indexability.published_audit import audit_recent_published_urls
from execution_adapters.contentflow import parse_contentflow_credentials
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.indexability.queries import list_live_published_urls
from exposureflow_api.indexability.technical_issues import upsert_technical_issue
from exposureflow_api.integrations.sync_helpers import (
    decrypt_credential_payload,
    finalize_job_run,
    get_credential,
    get_site,
)
from exposureflow_api.models import JobRun


async def run_indexability_published_noindex(db: AsyncSession, run: JobRun) -> None:
    site_id = run.site_id
    if site_id is None:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="MISSING_SITE",
            error_message="site_id is required for indexability.published_noindex",
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

    records = await list_live_published_urls(
        db,
        run.workspace_id,
        site_id,
        days_back=7,
    )
    if not records:
        await finalize_job_run(
            run,
            success=True,
            output={"articles_checked": 0, "issues_found": 0},
            provider="indexability",
        )
        return

    site_base = f"https://{site.domain}".rstrip("/")
    contentflow_cred = await get_credential(db, run.workspace_id, site_id, "contentflow")
    if contentflow_cred is not None:
        cf = parse_contentflow_credentials(decrypt_credential_payload(contentflow_cred))
        site_base = cf.site_url.rstrip("/")

    issues = await asyncio.to_thread(
        audit_recent_published_urls,
        site_base,
        [record.url for record in records],
    )

    for issue in issues:
        await upsert_technical_issue(
            db,
            workspace_id=run.workspace_id,
            site_id=site_id,
            issue_type=issue.issue_type,
            severity=issue.severity,
            description=issue.description,
            recommended_action=issue.recommended_action,
            evidence={"url": issue.url},
            url=issue.url,
            source="published_noindex_check",
        )

    await db.flush()
    await finalize_job_run(
        run,
        success=True,
        output={
            "articles_checked": min(len(records), 10),
            "issues_found": len(issues),
            "issue_types": sorted({issue.issue_type for issue in issues}),
        },
        provider="indexability",
    )
