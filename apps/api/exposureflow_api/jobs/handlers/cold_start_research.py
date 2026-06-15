"""Cold-start keyword research — SERP expansion into needs_review pyramid nodes."""

from __future__ import annotations

from uuid import UUID

from connectors.serp.fallback import SerpFallbackClient
from connectors.serp.slot_extractor import build_fetch_result
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.config import settings
from exposureflow_api.exposure.owner_classification import load_competitor_domains
from exposureflow_api.integrations.sync_helpers import finalize_job_run, get_site
from exposureflow_api.models import JobRun
from exposureflow_api.models.strategy import KeywordPyramidNode
from exposureflow_api.strategy.constraint_engine import evaluate_constraint_match, parse_constraint_rules
from exposureflow_api.strategy.keyword_enrichment import merge_enrichment
from exposureflow_api.strategy.keyword_research import (
    expand_candidates_from_serp,
    infer_funnel_stage,
    infer_keyword_level,
)
from exposureflow_api.strategy.keyword_utils import normalize_keyword


async def run_cold_start_research(db: AsyncSession, run: JobRun) -> None:
    site_id = run.site_id
    if site_id is None:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="MISSING_SITE_ID",
            error_message="site_id is required",
        )
        return

    payload = run.input_json or {}
    seed_keywords = payload.get("seed_keywords") or []
    market = payload.get("market") or "TW"
    language = payload.get("language") or "zh-TW"
    include_paa = bool(payload.get("include_paa", True))
    include_related = bool(payload.get("include_related", True))
    max_expansions = int(payload.get("max_expansions") or 12)
    max_seeds = int(payload.get("max_seeds") or 5)

    if not seed_keywords:
        await finalize_job_run(
            run,
            success=False,
            output={},
            error_code="MISSING_SEED_KEYWORDS",
            error_message="seed_keywords required for cold-start research",
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

    country = str(market).lower()
    if country in ("tw", "taiwan"):
        country = "tw"

    existing = await db.execute(
        select(KeywordPyramidNode.keyword).where(
            KeywordPyramidNode.workspace_id == run.workspace_id,
            KeywordPyramidNode.site_id == site_id,
        )
    )
    existing_keys = {normalize_keyword(row[0]) for row in existing.all() if row[0]}

    constraint_rules = parse_constraint_rules(payload.get("constraints") or [])
    created = 0
    serp_fetched = 0
    skipped = 0
    errors: list[str] = []

    try:
        client = SerpFallbackClient(
            serper_api_key=settings.serper_api_key,
            serpapi_api_key=settings.serpapi_api_key,
        )
        competitors = await load_competitor_domains(db, run.workspace_id, site_id)

        for seed in seed_keywords[:max_seeds]:
            seed_text = str(seed).strip()
            if not seed_text:
                continue
            try:
                raw = client.fetch(
                    seed_text,
                    country=country,
                    language=language,
                    device="desktop",
                )
                result = build_fetch_result(
                    raw,
                    keyword=seed_text,
                    country=country,
                    language=language,
                    device="desktop",
                    site_domain=site.domain,
                    competitor_domains=competitors,
                )
                serp_fetched += 1
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{seed_text}: {exc}")
                continue

            candidates = expand_candidates_from_serp(
                seed_keyword=seed_text,
                slots=result.slots,
                provider=result.raw_provider,
                include_paa=include_paa,
                include_related=include_related,
                max_expansions=max_expansions,
            )

            for candidate in candidates:
                key = normalize_keyword(candidate.keyword)
                if not key or key in existing_keys:
                    skipped += 1
                    continue
                if evaluate_constraint_match(candidate.keyword, constraint_rules):
                    skipped += 1
                    continue

                intent = candidate.intent
                funnel = infer_funnel_stage(intent, candidate.node_type)
                db.add(
                    KeywordPyramidNode(
                        workspace_id=run.workspace_id,
                        site_id=UUID(str(site_id)),
                        keyword=candidate.keyword,
                        node_type=candidate.node_type,
                        intent=intent,
                        target_market=market,
                        language=language,
                        keyword_level=infer_keyword_level(candidate.node_type),
                        funnel_stage=funnel,
                        business_fit_status="needs_review",
                        priority=4,
                        created_by="system",
                        evidence_json=merge_enrichment(
                            {
                                "source": "cold_start_research",
                                "job_run_id": str(run.id),
                                "research_source": candidate.source,
                                "confidence": candidate.confidence,
                            },
                            candidate.enrichment,
                        ),
                    )
                )
                existing_keys.add(key)
                created += 1

        await finalize_job_run(
            run,
            success=True,
            output={
                "keywords_created": created,
                "keywords_skipped": skipped,
                "serp_fetched": serp_fetched,
                "status": "needs_review",
                "errors": errors[:5],
            },
            provider="serper" if serp_fetched else None,
            cost_cents=serp_fetched,
        )
    except Exception as exc:  # noqa: BLE001
        await finalize_job_run(
            run,
            success=False,
            output={"keywords_created": created, "serp_fetched": serp_fetched},
            error_code="COLD_START_FAILED",
            error_message=str(exc),
        )
