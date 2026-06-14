"""Technical SEO crawl job handler."""

from __future__ import annotations

from datetime import UTC, datetime

from connectors.tech_seo.analyzer import TechnicalSeoAnalyzer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.integrations.sync_helpers import finalize_job_run, get_site
from exposureflow_api.models import JobRun, TechnicalIssue


async def run_tech_seo_crawl(db: AsyncSession, run: JobRun) -> None:
    site_id = run.site_id
    if site_id is None:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="MISSING_SITE",
            error_message="site_id is required",
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

    seed_urls = run.input_json.get("seed_urls", [])

    try:
        analyzer = TechnicalSeoAnalyzer(site.domain)
        findings = analyzer.analyze(seed_urls=seed_urls)
        now = datetime.now(UTC)
        upserted = 0
        for finding in findings:
            existing = await db.execute(
                select(TechnicalIssue).where(
                    TechnicalIssue.workspace_id == run.workspace_id,
                    TechnicalIssue.site_id == site_id,
                    TechnicalIssue.issue_type == finding.issue_type,
                    TechnicalIssue.url == finding.url,
                    TechnicalIssue.status == "open",
                )
            )
            issue = existing.scalar_one_or_none()
            if issue is None:
                db.add(
                    TechnicalIssue(
                        workspace_id=run.workspace_id,
                        site_id=site_id,
                        url=finding.url,
                        issue_type=finding.issue_type,
                        severity=finding.severity,
                        status="open",
                        source="crawler",
                        description=finding.description,
                        recommended_action=finding.recommended_action,
                        evidence_json=finding.evidence,
                        first_seen_at=now,
                        last_seen_at=now,
                    )
                )
            else:
                issue.last_seen_at = now
                issue.evidence_json = finding.evidence
            upserted += 1
        await db.flush()
        await finalize_job_run(
            run,
            success=True,
            output={"issues_processed": upserted},
            provider="tech_seo",
        )
    except Exception as exc:  # noqa: BLE001
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="TECH_SEO_FAILED",
            error_message=str(exc),
        )
