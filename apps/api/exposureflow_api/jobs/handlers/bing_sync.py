"""Bing Webmaster sync job handler."""

from __future__ import annotations

from datetime import date, timedelta

from connectors.bing_webmaster import BingApiKeyProvider, BingWebmasterClient
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.integrations.sync_helpers import (
    decrypt_credential_payload,
    finalize_job_run,
    get_credential,
    get_or_create_sync_state,
    get_site,
    mark_sync_failure,
    mark_sync_success,
    parse_last_sync_date,
    upsert_bing_rows,
)
from exposureflow_api.models import JobRun


async def run_bing_sync(db: AsyncSession, run: JobRun) -> None:
    site_id = run.site_id
    if site_id is None:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="MISSING_SITE",
            error_message="site_id is required for bing.sync",
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

    credential = await get_credential(db, run.workspace_id, site_id, "bing_webmaster")
    if credential is None:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="CREDENTIAL_MISSING",
            error_message="Bing Webmaster credential not configured",
        )
        return

    state = await get_or_create_sync_state(db, run.workspace_id, site_id, "bing_webmaster")
    api_key = decrypt_credential_payload(credential)
    site_url = run.input_json.get("site_url") or f"https://{site.domain}/"

    try:
        client = BingWebmasterClient(
            site_url=site_url,
            token_provider=BingApiKeyProvider(api_key),
        )
        last_date = parse_last_sync_date(state.cursor_json)
        end = date.today() - timedelta(days=2)
        start = last_date + timedelta(days=1) if last_date else end - timedelta(days=30)
        rows = client.fetch_query_stats(start, end) if start <= end else []
        count = await upsert_bing_rows(db, run.workspace_id, site_id, rows)
        latest = max((row.date for row in rows), default=last_date)
        if latest:
            mark_sync_success(state, last_date=latest)
        else:
            mark_sync_success(state)
        await finalize_job_run(
            run,
            success=True,
            output={"rows_upserted": count, "site_url": site_url},
            provider="bing_webmaster",
        )
    except Exception as exc:  # noqa: BLE001
        mark_sync_failure(state, str(exc))
        await finalize_job_run(
            run,
            success=False,
            output={},
            provider="bing_webmaster",
            error_code="BING_SYNC_FAILED",
            error_message=str(exc),
        )
