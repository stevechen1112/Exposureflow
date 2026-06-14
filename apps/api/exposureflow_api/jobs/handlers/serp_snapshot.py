"""SERP snapshot job handler."""

from __future__ import annotations

from connectors.serp.fallback import SerpFallbackClient
from connectors.serp.slot_extractor import build_fetch_result
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.config import settings
from exposureflow_api.integrations.sync_helpers import finalize_job_run, get_site
from exposureflow_api.models import JobRun, SerpQuerySnapshot, SerpSlot


async def run_serp_snapshot(db: AsyncSession, run: JobRun) -> None:
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

    keyword = run.input_json.get("keyword")
    if not keyword:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="KEYWORD_MISSING",
            error_message="keyword required in job input",
        )
        return

    country = run.input_json.get("country", "tw")
    language = run.input_json.get("language", site.primary_locale)
    device = run.input_json.get("device", "desktop")

    try:
        client = SerpFallbackClient(
            serper_api_key=settings.serper_api_key,
            serpapi_api_key=settings.serpapi_api_key,
        )
        raw = client.fetch(keyword, country=country, language=language, device=device)
        result = build_fetch_result(
            raw,
            keyword=keyword,
            country=country,
            language=language,
            device=device,
            site_domain=site.domain,
        )

        snapshot = SerpQuerySnapshot(
            workspace_id=run.workspace_id,
            site_id=site_id,
            keyword=keyword,
            surface="google",
            country=country,
            language=language,
            device=device,
            raw_provider=result.raw_provider,
            raw_json=result.raw_json,
            captured_at=result.captured_at,
        )
        db.add(snapshot)
        await db.flush()

        for slot in result.slots:
            db.add(
                SerpSlot(
                    workspace_id=run.workspace_id,
                    snapshot_id=snapshot.id,
                    slot_type=slot.slot_type,
                    position=slot.position,
                    owner_domain=slot.owner_domain,
                    owner_brand=slot.owner_brand,
                    url=slot.url,
                    title=slot.title,
                    snippet=slot.snippet,
                    is_own_site=slot.is_own_site,
                    is_competitor=slot.is_competitor,
                    is_third_party=slot.is_third_party,
                )
            )
        await db.flush()

        provider_cost = 1 if result.raw_provider == "serper" else 2
        await finalize_job_run(
            run,
            success=True,
            output={
                "snapshot_id": str(snapshot.id),
                "slots_count": len(result.slots),
                "provider": result.raw_provider,
            },
            provider=result.raw_provider,
            cost_cents=provider_cost,
        )
    except Exception as exc:  # noqa: BLE001
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="SERP_SNAPSHOT_FAILED",
            error_message=str(exc),
        )
