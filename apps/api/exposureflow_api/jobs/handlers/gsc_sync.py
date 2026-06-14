"""GSC sync job handler."""

from __future__ import annotations

import json

from connectors.google_search_console import GSCClient, OAuthTokenProvider, ServiceAccountTokenProvider
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
    upsert_gsc_rows,
)
from exposureflow_api.models import JobRun


async def run_gsc_sync(db: AsyncSession, run: JobRun) -> None:
    from exposureflow_api.reliability.circuit_breaker import assert_provider_available

    assert_provider_available("gsc")

    site_id = run.site_id
    if site_id is None:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="MISSING_SITE",
            error_message="site_id is required for gsc.sync",
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

    state = await get_or_create_sync_state(db, run.workspace_id, site_id, "gsc")
    payload = decrypt_credential_payload(credential)
    site_url = run.input_json.get("site_url") or f"sc-domain:{site.domain}"

    try:
        if credential.credential_type == "oauth":
            token_data = json.loads(payload)
            token_provider = OAuthTokenProvider(token_data["access_token"])
        else:
            token_provider = ServiceAccountTokenProvider(payload)

        client = GSCClient(site_url=site_url, token_provider=token_provider)
        last_date = parse_last_sync_date(state.cursor_json)
        rows = client.fetch_incremental(last_date)
        count = await upsert_gsc_rows(db, run.workspace_id, site_id, rows)
        latest = max((row.date for row in rows), default=last_date)
        if latest:
            mark_sync_success(state, last_date=latest)
        else:
            mark_sync_success(state)
        await finalize_job_run(
            run,
            success=True,
            output={"rows_upserted": count, "site_url": site_url},
            provider="gsc",
        )
    except Exception as exc:  # noqa: BLE001
        mark_sync_failure(state, str(exc))
        await finalize_job_run(
            run,
            success=False,
            output={},
            provider="gsc",
            error_code="GSC_SYNC_FAILED",
            error_message=str(exc),
        )
