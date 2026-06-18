"""GSC sitemap health job handler."""

from __future__ import annotations

import json

from connectors.google_search_console import GSCClient, OAuthTokenProvider, ServiceAccountTokenProvider
from connectors.indexability.gsc_sitemap import audit_gsc_sitemap_health
from connectors.indexability.sitemap_diagnosis import diagnose_live_sitemap
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.exposure.service import (
    generate_opportunities_from_sitemap_health,
    resolve_open_sitemap_opportunities,
)
from exposureflow_api.indexability.technical_issues import (
    resolve_open_technical_issues,
    upsert_technical_issue,
)
from exposureflow_api.integrations.sync_helpers import (
    decrypt_credential_payload,
    finalize_job_run,
    get_credential,
    get_site,
)
from exposureflow_api.models import JobRun

_GSC_SITEMAP_ISSUE_TYPES = [
    "gsc_sitemap_unreachable",
    "gsc_sitemap_missing",
    "gsc_sitemap_api_error",
]


async def run_indexability_sitemap_health(db: AsyncSession, run: JobRun) -> None:
    from exposureflow_api.reliability.circuit_breaker import assert_provider_available

    assert_provider_available("gsc")

    site_id = run.site_id
    if site_id is None:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="MISSING_SITE",
            error_message="site_id is required for indexability.sitemap_health",
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
            error_message="GSC credential not configured",
        )
        return

    payload = decrypt_credential_payload(credential)
    site_url = run.input_json.get("site_url") or f"sc-domain:{site.domain}"

    try:
        if credential.credential_type == "oauth":
            token_data = json.loads(payload)
            token_provider = OAuthTokenProvider(token_data["access_token"])
        else:
            token_provider = ServiceAccountTokenProvider(payload)

        client = GSCClient(site_url=site_url, token_provider=token_provider)
        report = audit_gsc_sitemap_health(client)
        diagnoses: dict[str, dict] = {}

        if report.healthy:
            resolved_issues = await resolve_open_technical_issues(
                db,
                workspace_id=run.workspace_id,
                site_id=site_id,
                issue_types=_GSC_SITEMAP_ISSUE_TYPES,
            )
            resolved_opps = await resolve_open_sitemap_opportunities(
                db, run.workspace_id, site_id
            )
            output = report.to_dict()
            output["resolved_issues"] = resolved_issues
            output["resolved_opportunities"] = resolved_opps
            await db.flush()
            await finalize_job_run(
                run,
                success=True,
                output=output,
                provider="gsc",
            )
            return

        for issue in report.issues:
            evidence = dict(issue.evidence)
            recommended_action = issue.recommended_action

            if issue.issue_type == "gsc_sitemap_unreachable":
                broken = evidence.get("broken_sitemaps") or []
                for entry in broken:
                    sm_url = entry.get("url")
                    if not sm_url:
                        continue
                    diagnosis = diagnose_live_sitemap(sm_url, site.domain)
                    diagnoses[sm_url] = diagnosis.to_dict()
                    if diagnosis.recommended_action:
                        recommended_action = diagnosis.recommended_action
                    if diagnosis.root_cause:
                        evidence["live_diagnosis"] = diagnosis.to_dict()
                    break

            await upsert_technical_issue(
                db,
                workspace_id=run.workspace_id,
                site_id=site_id,
                issue_type=issue.issue_type,
                severity=issue.severity,
                description=issue.description,
                recommended_action=recommended_action,
                evidence=evidence,
                url=site_url,
                source="gsc_sitemap_health",
                match_url=False,
            )

        opportunities_created = await generate_opportunities_from_sitemap_health(
            db,
            run.workspace_id,
            site_id,
            report.issues,
            diagnoses,
        )

        from exposureflow_api.decision.service import generate_action_candidates

        candidates_created = await generate_action_candidates(db, run.workspace_id, site_id)

        await db.flush()
        output = report.to_dict()
        output["live_diagnoses"] = diagnoses
        output["opportunities_created"] = opportunities_created
        output["candidates_created"] = candidates_created
        await finalize_job_run(
            run,
            success=True,
            output=output,
            provider="gsc",
        )
    except Exception as exc:  # noqa: BLE001
        await finalize_job_run(
            run,
            success=False,
            output={},
            provider="gsc",
            error_code="SITEMAP_HEALTH_FAILED",
            error_message=str(exc),
        )
