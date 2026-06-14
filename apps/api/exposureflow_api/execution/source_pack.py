"""Build evidence source packs for grounded content execution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.knowledge.service import is_fact_usable
from exposureflow_api.models.execution_content import ContentSourcePack
from exposureflow_api.models.exposure import ExposureOpportunity
from exposureflow_api.models.knowledge import KnowledgeFact, KnowledgeSource

MIN_FACTS_FOR_READY = 1
HIGH_RISK_BRIEF_TYPES = frozenset({"comparison", "case_study", "solution_page"})


@dataclass(frozen=True)
class SourcePackBuildResult:
    source_pack: ContentSourcePack
    needs_human_evidence: bool
    coverage_score: float


def _classify_source_ref(source: KnowledgeSource, fact: KnowledgeFact) -> dict:
    category = "company_owned"
    if source.source_type in ("serp_observation", "serp"):
        category = "serp_observation"
    elif source.source_type in ("ai_observation", "ai_citation"):
        category = "ai_observation"
    elif source.source_type in ("manual", "manual_evidence"):
        category = "manual_evidence"
    elif source.source_type in ("external", "url", "pdf", "csv"):
        category = "external_source"
    return {
        "ref_type": category,
        "source_id": str(source.id),
        "fact_id": str(fact.id),
        "title": source.title,
        "fact_type": fact.fact_type,
        "subject": fact.subject,
        "fact_text": fact.fact_text,
        "market": fact.market or source.market,
        "language": fact.language or source.language,
        "confidence": float(fact.confidence),
    }


def compute_coverage_score(source_refs: list[dict], *, brief_type: str | None = None) -> float:
    if not source_refs:
        return 0.0
    categories = {ref["ref_type"] for ref in source_refs}
    score = min(1.0, len(source_refs) / 5)
    if "company_owned" in categories:
        score = min(1.0, score + 0.2)
    if brief_type in HIGH_RISK_BRIEF_TYPES and len(categories) < 2:
        score = min(score, 0.5)
    return round(score, 2)


async def build_source_pack(
    db: AsyncSession,
    *,
    workspace_id: UUID,
    site_id: UUID,
    opportunity_id: UUID | None = None,
    execution_job_id: UUID | None = None,
    market: str | None = None,
    language: str | None = None,
    brief_type: str | None = None,
) -> SourcePackBuildResult:
    now = datetime.now(timezone.utc)
    facts_result = await db.execute(
        select(KnowledgeFact, KnowledgeSource)
        .join(KnowledgeSource, KnowledgeSource.id == KnowledgeFact.knowledge_source_id)
        .where(
            KnowledgeFact.workspace_id == workspace_id,
            KnowledgeFact.site_id == site_id,
            KnowledgeFact.status == "approved",
            KnowledgeSource.status == "approved",
        )
    )
    source_refs: list[dict] = []
    for fact, source in facts_result.all():
        if not is_fact_usable(fact, now=now):
            continue
        if market and fact.market and fact.market != market:
            continue
        if language and fact.language and fact.language != language:
            continue
        source_refs.append(_classify_source_ref(source, fact))

    if opportunity_id:
        opp = await db.get(ExposureOpportunity, opportunity_id)
        if opp and opp.workspace_id == workspace_id:
            source_refs.append(
                {
                    "ref_type": "serp_observation",
                    "source_id": None,
                    "fact_id": None,
                    "title": "Opportunity context",
                    "fact_type": "opportunity",
                    "subject": opp.keyword or "exposure opportunity",
                    "fact_text": opp.reason or "",
                    "market": market,
                    "language": language,
                    "confidence": 1.0,
                }
            )

    coverage = compute_coverage_score(source_refs, brief_type=brief_type)
    needs_human = coverage < 0.5 or len(source_refs) < MIN_FACTS_FOR_READY
    status = "needs_human_evidence" if needs_human else "ready"

    pack = ContentSourcePack(
        workspace_id=workspace_id,
        site_id=site_id,
        opportunity_id=opportunity_id,
        execution_job_id=execution_job_id,
        market=market,
        language=language,
        required_coverage_json={
            "min_facts": MIN_FACTS_FOR_READY,
            "min_coverage_score": 0.5,
            "brief_type": brief_type,
        },
        source_refs_json=source_refs,
        coverage_score=coverage,
        status=status,
    )
    db.add(pack)
    await db.flush()
    return SourcePackBuildResult(
        source_pack=pack,
        needs_human_evidence=needs_human,
        coverage_score=coverage,
    )
