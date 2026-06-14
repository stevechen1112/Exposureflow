"""GA4 sync job handler."""

from __future__ import annotations

import json
from datetime import date, timedelta

from connectors.google_analytics import GA4Client, Ga4ServiceAccountTokenProvider
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
    upsert_ga4_rows,
)
from exposureflow_api.models import JobRun


class _OAuthTokenProvider:
    def __init__(self, access_token: str) -> None:
        self._access_token = access_token

    def get_access_token(self) -> str:
        return self._access_token


async def run_ga4_sync(db: AsyncSession, run: JobRun) -> None:
    site_id = run.site_id
    if site_id is None:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="MISSING_SITE",
            error_message="site_id is required for ga4.sync",
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

    credential = await get_credential(db, run.workspace_id, site_id, "ga4")
    if credential is None:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="CREDENTIAL_MISSING",
            error_message="GA4 credential not configured",
        )
        return

    property_id = run.input_json.get("property_id")
    if not property_id:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="PROPERTY_MISSING",
            error_message="property_id required in job input",
        )
        return

    state = await get_or_create_sync_state(db, run.workspace_id, site_id, "ga4")
    payload = decrypt_credential_payload(credential)

    try:
        if credential.credential_type == "oauth":
            token_data = json.loads(payload)
            token_provider = _OAuthTokenProvider(token_data["access_token"])
        else:
            token_provider = Ga4ServiceAccountTokenProvider(payload)

        client = GA4Client(property_id=str(property_id), token_provider=token_provider)
        last_date = parse_last_sync_date(state.cursor_json)
        end = date.today() - timedelta(days=1)
        start = last_date + timedelta(days=1) if last_date else end - timedelta(days=30)
        if start > end:
            rows = []
        else:
            rows = client.fetch_page_metrics(start, end)
        count = await upsert_ga4_rows(db, run.workspace_id, site_id, rows)
        latest = max((row.date for row in rows), default=last_date)
        if latest:
            mark_sync_success(state, last_date=latest)
        else:
            mark_sync_success(state)
        await finalize_job_run(
            run,
            success=True,
            output={"rows_upserted": count, "property_id": property_id, "auxiliary": True},
            provider="ga4",
        )
    except Exception as exc:  # noqa: BLE001
        mark_sync_failure(state, str(exc))
        await finalize_job_run(
            run,
            success=False,
            output={},
            provider="ga4",
            error_code="GA4_SYNC_FAILED",
            error_message=str(exc),
        )
