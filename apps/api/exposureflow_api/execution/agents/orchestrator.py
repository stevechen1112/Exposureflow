"""Content Generation Orchestrator: 7-Agent Pipeline.

Modeled after ContentFlow's orchestrator.py.
Coordinates: research → strategy → write → seo_check ↔ seo_qa → claim_gate
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.content.repository import (
    get_brief,
    get_generation_run,
    get_source_pack,
    pipeline_params_from_brief,
)
from exposureflow_api.execution.agents.research_agent import run_research_agent
from exposureflow_api.execution.agents.seo_check_agent import run_seo_check
from exposureflow_api.execution.agents.seo_qa_agent import apply_seo_qa_fixes
from exposureflow_api.execution.agents.strategy_agent import run_strategy_agent
from exposureflow_api.execution.agents.writing_agent import run_writing_agent
from exposureflow_api.execution.compiler.content_normalizer import normalize_article_markdown
from exposureflow_api.execution.review_policy import resolve_review_policy
from exposureflow_api.models.execution_content import (
    ContentBrief,
    ContentSourcePack,
)
from exposureflow_api.models.tenant import Site

SEO_PASS_THRESHOLD = 85
SEO_MAX_RETRIES = 3


@dataclass
class PipelineState:
    run_id: UUID
    workspace_id: UUID
    site_id: UUID
    keyword: str = ""
    node_type: str = "cluster"
    intent: str | None = None

    research_report: Any = None
    strategy_report: Any = None

    draft_markdown: str = ""
    meta_title: str = ""
    meta_description: str = ""
    evidence_map: dict = field(default_factory=dict)
    generation_mode: str = "grounded_llm"
    provider: str = "llm"
    claim_gate_status: str | None = None

    seo_score: int = 0
    best_seo_score: int = 0
    best_draft_markdown: str = ""
    seo_retry_count: int = 0
    seo_checks: list[dict] = field(default_factory=list)

    pipeline_status: str = "pending"
    errors: list[str] = field(default_factory=list)
    agent_decisions: list[dict] = field(default_factory=list)


def _record_decision(state: PipelineState, agent: str, decision: str, reason: str) -> None:
    state.agent_decisions.append({
        "agent": agent,
        "decision": decision,
        "reason": reason,
        "timestamp": datetime.now(UTC).isoformat(),
    })


def _site_context(site: Site | None) -> dict:
    if site is None:
        return {}
    return {
        "industry": site.industry,
        "business_model": site.business_model,
        "primary_locale": site.primary_locale,
        "target_countries": site.target_countries or [],
        "target_languages": site.target_languages or [],
    }


async def _run_research_stage(
    state: PipelineState,
    brief: ContentBrief,
    pack: ContentSourcePack,
) -> None:
    _record_decision(state, "research_agent", "start", f"Researching keyword: {state.keyword}")

    serp_slots: list[dict] = []
    for ref in pack.source_refs_json or []:
        evidence = ref.get("evidence_json", {}) or {}
        serp_data = evidence.get("serp_enrichment", {}) or {}
        if serp_data.get("slots"):
            serp_slots.extend(serp_data["slots"])

    report = await run_research_agent(
        keyword=state.keyword,
        serp_slots=serp_slots if serp_slots else None,
    )
    state.research_report = report
    state.pipeline_status = "research_done"
    _record_decision(
        state, "research_agent", "complete",
        f"Found {len(report.serp_intelligence.top_results)} organic results, "
        f"{report.serp_intelligence.paa_count} PAA questions, "
        f"difficulty={report.serp_intelligence.difficulty_hint}",
    )


def _run_strategy_stage(state: PipelineState) -> None:
    _record_decision(state, "strategy_agent", "start", "Building content strategy")

    if state.research_report is None:
        state.errors.append("Research report missing, cannot run strategy")
        return

    report = run_strategy_agent(
        state.research_report,
        node_type=state.node_type,
        intent=state.intent,
    )
    state.strategy_report = report
    state.pipeline_status = "strategy_done"
    _record_decision(
        state, "strategy_agent", "complete",
        f"Architecture={report.writing_architecture}, "
        f"Angle={report.content_angle}, "
        f"FAQ count={len(report.faq_questions)}",
    )


def _run_writing_stage(
    state: PipelineState,
    brief: ContentBrief,
    pack: ContentSourcePack,
    site: Site | None,
) -> None:
    _record_decision(state, "writing_agent", "start", "LLM grounded writing")

    policy = resolve_review_policy(
        industry=site.industry if site else None,
        brand_review_policy=brief.brief_json.get("review_policy"),
        brief_type=brief.brief_type,
    )

    result = run_writing_agent(
        keyword=state.keyword,
        brief=brief,
        source_pack=pack,
        strategy_report=state.strategy_report,
        site_context=_site_context(site),
        forbidden_claims=list(brief.forbidden_claims_json or []),
        temperature=policy.writing_temperature,
    )

    state.draft_markdown = result.markdown
    state.meta_title = result.meta_title
    state.meta_description = result.meta_description
    state.evidence_map = result.evidence_map
    state.generation_mode = result.generation_mode
    state.provider = result.provider
    state.pipeline_status = "draft"
    _record_decision(
        state, "writing_agent", "complete",
        f"Draft mode={result.generation_mode}, sections={len(result.evidence_map)}",
    )


def _run_seo_check_stage(state: PipelineState) -> bool:
    _record_decision(state, "seo_check_agent", "start", f"Retry #{state.seo_retry_count + 1}")

    result = run_seo_check(
        markdown=state.draft_markdown,
        keyword=state.keyword,
        meta_title=state.meta_title,
        meta_description=state.meta_description,
    )

    state.seo_score = result.score
    state.seo_checks = result.checks

    if result.score > state.best_seo_score:
        state.best_seo_score = result.score
        state.best_draft_markdown = state.draft_markdown

    if result.passed:
        state.pipeline_status = "seo_passed"
        _record_decision(
            state, "seo_check_agent", "pass",
            f"SEO score={result.score}/100 >= {SEO_PASS_THRESHOLD}",
        )
        return True

    state.seo_retry_count += 1
    if state.seo_retry_count >= SEO_MAX_RETRIES:
        state.pipeline_status = "seo_failed"
        _record_decision(
            state, "seo_check_agent", "force_output",
            f"Max retries ({SEO_MAX_RETRIES}) reached, best score={state.best_seo_score}",
        )
        state.draft_markdown = state.best_draft_markdown or state.draft_markdown
        return True

    _record_decision(
        state, "seo_check_agent", "retry",
        f"SEO score={result.score}/100 < {SEO_PASS_THRESHOLD}, "
        f"suggestions: {result.suggestions[:3]}",
    )
    return False


def _apply_seo_fixes(state: PipelineState, brief: ContentBrief) -> None:
    _record_decision(state, "seo_qa_agent", "fix", "Applying SEO QA fixes")
    failed = [c for c in state.seo_checks if not c.get("passed", True)]
    md, title, desc = apply_seo_qa_fixes(
        markdown=state.draft_markdown,
        keyword=state.keyword,
        meta_title=state.meta_title,
        meta_description=state.meta_description,
        failed_checks=failed,
        strategy_report=state.strategy_report,
        language=brief.language or "zh-TW",
    )
    state.draft_markdown = md
    state.meta_title = title
    state.meta_description = desc


async def _run_claim_stage(
    db: AsyncSession,
    state: PipelineState,
) -> None:
    """Verify claims against persisted markdown (must run after output_markdown is saved)."""
    _record_decision(state, "claim_verifier", "start", "Running claim verification gate")
    from exposureflow_api.content.service import verify_generation_run_claims

    try:
        gate = await verify_generation_run_claims(db, state.workspace_id, state.run_id)
        state.claim_gate_status = gate.status
        _record_decision(
            state, "claim_verifier", gate.status,
            f"Claim gate status={gate.status}",
        )
    except Exception as exc:
        state.errors.append(f"claim_verification_failed: {exc}")
        state.claim_gate_status = "error"
        _record_decision(state, "claim_verifier", "error", str(exc))
        raise


async def run_generation_pipeline(
    db: AsyncSession,
    workspace_id: UUID,
    run_id: UUID,
    *,
    keyword: str = "",
    node_type: str = "cluster",
    intent: str | None = None,
) -> PipelineState:
    """Run the full content generation pipeline and persist results on the run."""
    state = PipelineState(
        run_id=run_id,
        workspace_id=workspace_id,
        site_id=UUID("00000000-0000-0000-0000-000000000000"),
        keyword=keyword,
        node_type=node_type,
        intent=intent,
    )

    run = await get_generation_run(db, workspace_id, run_id)
    state.site_id = run.site_id
    site = await db.get(Site, run.site_id)

    brief = await get_brief(db, workspace_id, run.content_brief_id)
    pack = await get_source_pack(db, workspace_id, brief.source_pack_id)

    params = pipeline_params_from_brief(brief)
    if not state.keyword:
        state.keyword = params["keyword"] or ""
    if state.intent is None:
        state.intent = params["intent"]
    if state.node_type == "cluster":
        state.node_type = params["node_type"] or "cluster"

    await _run_research_stage(state, brief, pack)
    _run_strategy_stage(state)
    _run_writing_stage(state, brief, pack, site)

    while True:
        passed = _run_seo_check_stage(state)
        if passed:
            break
        _apply_seo_fixes(state, brief)

    # Persist draft before claim verification reads output_markdown.
    title_hint = brief.brief_json.get("title_hint") or state.keyword or brief.brief_type
    run.output_markdown = normalize_article_markdown(
        state.draft_markdown,
        keyword=state.keyword,
        title=title_hint,
    )
    run.generation_mode = state.generation_mode
    run.provider = state.provider
    run.evidence_map_json = {
        "sections": state.evidence_map,
        "meta": {
            "title": state.meta_title,
            "description": state.meta_description,
        },
        "pipeline_state": {
            "seo_score": state.best_seo_score,
            "seo_checks": state.seo_checks,
            "agent_decisions": state.agent_decisions,
            "research": {
                "difficulty": state.research_report.serp_intelligence.difficulty_hint if state.research_report else None,
                "paa_count": state.research_report.serp_intelligence.paa_count if state.research_report else 0,
            },
            "strategy": {
                "architecture": state.strategy_report.writing_architecture if state.strategy_report else None,
                "angle": state.strategy_report.content_angle if state.strategy_report else None,
                "outline_h2": state.strategy_report.outline_h2 if state.strategy_report else [],
            },
        },
    }
    await db.flush()

    await _run_claim_stage(db, state)

    state.pipeline_status = "complete"
    _record_decision(state, "orchestrator", "complete", f"Pipeline complete, SEO score={state.best_seo_score}")

    # verify_generation_run_claims sets claim_verified / claim_blocked — do not overwrite.
    await db.refresh(run)

    return state
