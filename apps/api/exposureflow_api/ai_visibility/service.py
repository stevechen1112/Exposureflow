"""AI visibility orchestration: probe runs, citations, brand, SERPO, opportunities."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.ai_visibility.brand_monitor import (
    classify_competitor_mentions,
    collect_brand_names,
    compute_visibility_metrics,
    detect_mentioned_brands,
)
from exposureflow_api.ai_visibility.citation_extractor import extract_citations
from exposureflow_api.ai_visibility.entity_checker import check_entity_consistency
from exposureflow_api.ai_visibility.import_probe import parse_csv_import, parse_json_import
from exposureflow_api.ai_visibility.opportunities import detect_ai_citation_ready, detect_entity_fix
from exposureflow_api.ai_visibility.serpo import aggregate_serpo_from_mentions
from exposureflow_api.common.errors import not_found
from exposureflow_api.exposure.owner_classification import load_competitor_domains
from exposureflow_api.exposure.scorer import ScoreInput, score_opportunity
from exposureflow_api.exposure.service import _build_opportunity
from exposureflow_api.models import (
    AIProbeRun,
    AIProbeSet,
    AICitation,
    BrandEntity,
    BrandMention,
    Competitor,
    ExposureAsset,
    ExposureOpportunity,
    SerpoRecord,
    Site,
)


async def _load_site(db: AsyncSession, workspace_id: UUID, site_id: UUID) -> Site:
    site = await db.get(Site, site_id)
    if site is None or site.workspace_id != workspace_id:
        raise not_found("Site")
    return site


async def _load_brand_entity(
    db: AsyncSession, workspace_id: UUID, site_id: UUID
) -> BrandEntity | None:
    result = await db.execute(
        select(BrandEntity)
        .where(
            BrandEntity.workspace_id == workspace_id,
            BrandEntity.site_id == site_id,
        )
        .order_by(BrandEntity.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def validate_probe_set(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
    probe_set_id: UUID | None,
) -> AIProbeSet | None:
    if probe_set_id is None:
        return None
    probe_set = await db.get(AIProbeSet, probe_set_id)
    if (
        probe_set is None
        or probe_set.workspace_id != workspace_id
        or probe_set.site_id != site_id
    ):
        raise not_found("AI probe set")
    return probe_set


async def _competitor_name_map(
    db: AsyncSession, workspace_id: UUID, site_id: UUID
) -> dict[str, str]:
    result = await db.execute(
        select(Competitor).where(
            Competitor.workspace_id == workspace_id,
            Competitor.site_id == site_id,
            Competitor.active.is_(True),
        )
    )
    mapping: dict[str, str] = {}
    for row in result.scalars().all():
        mapping[row.name.lower()] = row.domain
        for alias in row.aliases_json or []:
            if isinstance(alias, str) and alias.strip():
                mapping[alias.strip().lower()] = row.domain
    return mapping


async def record_probe_run(
    db: AsyncSession,
    *,
    workspace_id: UUID,
    site_id: UUID,
    probe_set_id: UUID | None,
    probe_mode: str,
    surface: str,
    prompt: str,
    answer_text: str,
    cited_urls: list[str] | None,
    mentioned_brands: list[str] | None,
    competitor_mentions: list[str] | None,
    sentiment: str | None,
    run_at: datetime | None,
    provider: str | None = None,
    model: str | None = None,
    raw_response_json: dict | None = None,
) -> AIProbeRun:
    site = await _load_site(db, workspace_id, site_id)
    entity = await _load_brand_entity(db, workspace_id, site_id)
    competitor_domains = await load_competitor_domains(db, workspace_id, site_id)
    competitor_names = await _competitor_name_map(db, workspace_id, site_id)

    our_names = collect_brand_names(
        entity.canonical_name if entity else None,
        entity.aliases_json if entity else [],
        site.site_name,
    )
    known_brands = set(our_names) | set(competitor_names.keys())
    detected_brands = detect_mentioned_brands(answer_text, mentioned_brands, known_brands)
    competitor_hits = classify_competitor_mentions(detected_brands, our_names, competitor_names)
    if competitor_mentions:
        for name in competitor_mentions:
            domain = competitor_names.get(name.lower(), "")
            competitor_hits.append({"name": name, "domain": domain or "unknown"})

    citations = extract_citations(
        answer_text=answer_text,
        explicit_urls=cited_urls,
        site_domain=site.domain,
        competitor_domains=competitor_domains,
        our_brand_names=our_names,
    )
    our_url_cited = any(c.is_own_site for c in citations)
    external_url_cited = any(
        (c.is_competitor or c.is_third_party_about_brand) and not c.is_own_site
        for c in citations
    )
    our_brand_mentioned = any(
        name.lower() in answer_text.lower() for name in our_names if name
    )

    captured_at = run_at or datetime.now(UTC)
    run = AIProbeRun(
        workspace_id=workspace_id,
        site_id=site_id,
        probe_set_id=probe_set_id,
        probe_mode=probe_mode,
        provider=provider,
        model=model,
        surface=surface,
        prompt=prompt,
        answer_text=answer_text,
        cited_urls_json=[c.cited_url for c in citations],
        mentioned_brands_json=detected_brands,
        sentiment=sentiment,
        our_brand_mentioned=our_brand_mentioned,
        our_url_cited=our_url_cited,
        external_url_cited=external_url_cited,
        competitor_mentions_json=competitor_hits,
        raw_response_json=raw_response_json or {},
        run_at=captured_at,
    )
    db.add(run)
    await db.flush()

    for citation in citations:
        db.add(
            AICitation(
                workspace_id=workspace_id,
                site_id=site_id,
                ai_probe_run_id=run.id,
                surface=surface,
                prompt=prompt,
                cited_url=citation.cited_url,
                cited_domain=citation.cited_domain,
                citation_context=citation.citation_context,
                is_own_site=citation.is_own_site,
                is_third_party_about_brand=citation.is_third_party_about_brand,
                is_competitor=citation.is_competitor,
                captured_at=captured_at,
            )
        )

    db.add(
        BrandMention(
            workspace_id=workspace_id,
            site_id=site_id,
            ai_probe_run_id=run.id,
            source_url=f"ai://{surface}",
            source_domain=surface,
            source_type="ai_answer",
            mention_text=answer_text[:2000],
            linked=our_url_cited,
            sentiment=sentiment,
            relevance_score=80.0 if our_brand_mentioned else 40.0,
            captured_at=captured_at,
        )
    )
    await db.flush()
    return run


async def import_probe_runs(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
    probe_set_id: UUID | None,
    *,
    format: str,
    csv_content: str | None,
    rows: list[dict] | None,
) -> list[AIProbeRun]:
    await validate_probe_set(db, workspace_id, site_id, probe_set_id)
    if format == "csv":
        if not csv_content:
            raise ValueError("csv_content is required for CSV import")
        parsed = parse_csv_import(csv_content)
    else:
        if not rows:
            raise ValueError("rows is required for JSON import")
        parsed = parse_json_import(rows)

    created: list[AIProbeRun] = []
    for row in parsed:
        run = await record_probe_run(
            db,
            workspace_id=workspace_id,
            site_id=site_id,
            probe_set_id=probe_set_id,
            probe_mode="manual_import",
            surface=row["surface"],
            prompt=row["prompt"],
            answer_text=row["answer_text"],
            cited_urls=row["cited_urls"],
            mentioned_brands=row["mentioned_brands"],
            competitor_mentions=row.get("competitor_mentions"),
            sentiment=row.get("sentiment"),
            run_at=row["run_at"],
        )
        created.append(run)
    return created


async def probe_set_visibility_score(
    db: AsyncSession,
    workspace_id: UUID,
    probe_set_id: UUID,
):
    probe_set = await db.get(AIProbeSet, probe_set_id)
    if probe_set is None or probe_set.workspace_id != workspace_id:
        raise not_found("AI probe set")
    result = await db.execute(
        select(AIProbeRun).where(
            AIProbeRun.workspace_id == workspace_id,
            AIProbeRun.probe_set_id == probe_set_id,
        )
    )
    runs = list(result.scalars().all())
    return compute_visibility_metrics(runs)


async def run_entity_check(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
) -> dict:
    entity = await _load_brand_entity(db, workspace_id, site_id)
    if entity is None:
        raise not_found("Brand entity")
    mentions_result = await db.execute(
        select(BrandMention).where(
            BrandMention.workspace_id == workspace_id,
            BrandMention.site_id == site_id,
        )
    )
    mentions = list(mentions_result.scalars().all())
    result = check_entity_consistency(
        canonical_name=entity.canonical_name,
        description=entity.description,
        aliases=entity.aliases_json or [],
        mentions=mentions,
    )
    entity.entity_consistency_score = result.consistency_score
    await db.flush()
    return {
        "consistency_score": result.consistency_score,
        "inconsistencies": [
            {
                "source_url": i.source_url,
                "mention_text": i.mention_text,
                "sentiment": i.sentiment,
                "reason": i.reason,
            }
            for i in result.inconsistencies
        ],
        "recommended_actions": result.recommended_actions,
    }


async def capture_serpo_snapshot(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
    *,
    brand_query: str,
    keyword: str | None,
    surface: str,
) -> SerpoRecord:
    mentions_result = await db.execute(
        select(BrandMention).where(
            BrandMention.workspace_id == workspace_id,
            BrandMention.site_id == site_id,
        )
    )
    all_mentions = list(mentions_result.scalars().all())
    query_lower = brand_query.lower()
    filtered = [
        m
        for m in all_mentions
        if query_lower in (m.mention_text or "").lower()
        or (keyword and keyword.lower() in (m.mention_text or "").lower())
    ]
    snapshot = aggregate_serpo_from_mentions(
        brand_query=brand_query,
        keyword=keyword,
        surface=surface,
        mentions=filtered or all_mentions,
    )
    record = SerpoRecord(
        workspace_id=workspace_id,
        site_id=site_id,
        brand_query=snapshot.brand_query,
        keyword=snapshot.keyword,
        surface=snapshot.surface,
        first_page_positive_count=snapshot.first_page_positive_count,
        first_page_neutral_count=snapshot.first_page_neutral_count,
        first_page_negative_count=snapshot.first_page_negative_count,
        first_page_wrong_info_count=snapshot.first_page_wrong_info_count,
        recommended_actions_json=snapshot.recommended_actions_json,
        captured_at=snapshot.captured_at,
    )
    db.add(record)
    await db.flush()
    return record


async def generate_ai_opportunities(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
) -> int:
    probe_sets = await db.execute(
        select(AIProbeSet).where(
            AIProbeSet.workspace_id == workspace_id,
            AIProbeSet.site_id == site_id,
            AIProbeSet.active.is_(True),
        )
    )
    asset_count = await db.execute(
        select(ExposureAsset).where(
            ExposureAsset.workspace_id == workspace_id,
            ExposureAsset.site_id == site_id,
            ExposureAsset.status.in_(("active", "candidate")),
        )
    )
    has_assets = asset_count.scalars().first() is not None
    created = 0

    for probe_set in probe_sets.scalars().all():
        for prompt in probe_set.prompts_json or []:
            if not isinstance(prompt, str) or not prompt.strip():
                continue
            runs_result = await db.execute(
                select(AIProbeRun).where(
                    AIProbeRun.workspace_id == workspace_id,
                    AIProbeRun.probe_set_id == probe_set.id,
                    AIProbeRun.prompt == prompt,
                )
            )
            runs = list(runs_result.scalars().all())
            candidate = detect_ai_citation_ready(
                prompt=prompt,
                runs=runs,
                has_reinforceable_asset=has_assets,
            )
            if candidate:
                existing = await db.execute(
                    select(ExposureOpportunity).where(
                        ExposureOpportunity.workspace_id == workspace_id,
                        ExposureOpportunity.site_id == site_id,
                        ExposureOpportunity.opportunity_type == "ai_citation_ready",
                        ExposureOpportunity.keyword == prompt,
                        ExposureOpportunity.status == "open",
                    )
                )
                if existing.scalar_one_or_none():
                    continue
                score = score_opportunity(
                    ScoreInput(
                        query_impressions_28d=100,
                        site_p95_query_impressions=500,
                        current_position=None,
                        targetable_slot_count=1,
                        ai_citation_score=0.3,
                        zero_click_value_score=0.8,
                        execution_confidence=0.7,
                    )
                )
                db.add(
                    _build_opportunity(
                        workspace_id,
                        site_id,
                        opportunity_type=candidate.opportunity_type,
                        keyword=candidate.keyword,
                        current_url=None,
                        impressions=0,
                        position=None,
                        reason=candidate.reason,
                        rule_id=candidate.rule_id,
                        score=score,
                        extra_evidence=candidate.extra_evidence,
                    )
                )
                created += 1

    runs_result = await db.execute(
        select(AIProbeRun).where(
            AIProbeRun.workspace_id == workspace_id,
            AIProbeRun.site_id == site_id,
        )
    )
    for run in runs_result.scalars().all():
        candidate = detect_entity_fix(
            prompt=run.prompt,
            sentiment=run.sentiment,
            our_brand_mentioned=run.our_brand_mentioned,
            probe_run_id=str(run.id),
        )
        if not candidate:
            continue
        existing = await db.execute(
            select(ExposureOpportunity).where(
                ExposureOpportunity.workspace_id == workspace_id,
                ExposureOpportunity.site_id == site_id,
                ExposureOpportunity.opportunity_type == "entity_fix",
                ExposureOpportunity.keyword == run.prompt,
                ExposureOpportunity.status == "open",
            )
        )
        if existing.scalar_one_or_none():
            continue
        score = score_opportunity(
            ScoreInput(
                query_impressions_28d=50,
                site_p95_query_impressions=500,
                current_position=None,
                targetable_slot_count=0,
                ai_citation_score=0.9,
                zero_click_value_score=0.8,
                execution_confidence=0.6,
            )
        )
        db.add(
            _build_opportunity(
                workspace_id,
                site_id,
                opportunity_type=candidate.opportunity_type,
                keyword=candidate.keyword,
                current_url=None,
                impressions=0,
                position=None,
                reason=candidate.reason,
                rule_id=candidate.rule_id,
                score=score,
                extra_evidence=candidate.extra_evidence,
            )
        )
        created += 1

    await db.flush()
    return created
