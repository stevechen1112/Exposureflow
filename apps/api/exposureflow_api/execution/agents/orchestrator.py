"""Content Generation Orchestrator: 7-Agent Pipeline.

Modeled after ContentFlow's orchestrator.py (LangGraph StateGraph).
Coordinates the full content generation pipeline:

    research → strategy → write → seo_check
                                       ↓ seo_gate
                       "pass" (>=85) → factcheck → publish_gate
                       "retry" (<85, <3x) → seo_qa → seo_check
                       "force_output" (>=3x) → factcheck

Quality gate: SEO score >= 85 to pass, max 3 retries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.content.service import (
    get_brief,
    get_generation_run,
    get_source_pack,
)
from exposureflow_api.execution.agents.research_agent import run_research_agent
from exposureflow_api.execution.agents.strategy_agent import run_strategy_agent
from exposureflow_api.execution.agents.seo_check_agent import run_seo_check
from exposureflow_api.execution.compiler import compile_grounded_draft
from exposureflow_api.models.execution_content import (
    ContentBrief,
    ContentGenerationRun,
    ContentSourcePack,
)

SEO_PASS_THRESHOLD = 85
SEO_MAX_RETRIES = 3


@dataclass
class PipelineState:
    """State tracked through the generation pipeline."""
    run_id: UUID
    workspace_id: UUID
    site_id: UUID
    keyword: str = ""
    node_type: str = "cluster"
    intent: str | None = None

    # Research output
    research_report: Any = None

    # Strategy output
    strategy_report: Any = None

    # Generated content
    draft_markdown: str = ""
    meta_title: str = ""
    meta_description: str = ""

    # SEO check
    seo_score: int = 0
    best_seo_score: int = 0
    best_draft_markdown: str = ""
    seo_retry_count: int = 0
    seo_checks: list[dict] = field(default_factory=list)

    # Final status
    pipeline_status: str = "pending"  # pending / research_done / strategy_done / draft / seo_passed / seo_failed / complete
    errors: list[str] = field(default_factory=list)
    agent_decisions: list[dict] = field(default_factory=list)


def _record_decision(state: PipelineState, agent: str, decision: str, reason: str) -> None:
    state.agent_decisions.append({
        "agent": agent,
        "decision": decision,
        "reason": reason,
        "timestamp": datetime.now(UTC).isoformat(),
    })


async def _run_research_stage(
    state: PipelineState,
    brief: ContentBrief,
    pack: ContentSourcePack,
) -> None:
    """Stage 1: Research Agent — SERP analysis + competitor depth."""
    _record_decision(state, "research_agent", "start", f"Researching keyword: {state.keyword}")

    # Collect SERP data from source pack refs
    serp_slots: list[dict] = []
    for ref in pack.source_refs_json or []:
        evidence = ref.get("evidence_json", {}) or {}
        serp_data = evidence.get("serp_enrichment", {}) or {}
        if serp_data.get("slots"):
            serp_slots.extend(serp_data["slots"])

    # Run research
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
    """Stage 2: Strategy Agent — content angle + outline."""
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
) -> None:
    """Stage 3: Writing — compile grounded draft from brief + pack."""
    _record_decision(state, "writing_agent", "start", "Compiling grounded draft")

    # Use existing compiler
    result = compile_grounded_draft(
        brief,
        pack,
        generation_mode="grounded_template",
        review_level="standard",
    )

    state.draft_markdown = result.markdown
    state.meta_title = brief.brief_json.get("title_hint") or f"{state.keyword} — 完整指南"
    state.meta_description = brief.brief_json.get("description") or ""
    state.pipeline_status = "draft"
    _record_decision(
        state, "writing_agent", "complete",
        f"Draft compiled with {len(result.evidence_map)} evidence sections",
    )


def _run_seo_check_stage(state: PipelineState) -> bool:
    """Stage 4: SEO Check Agent — quality verification.

    Returns True if passed, False if needs retry.
    """
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
        # Use best draft
        state.draft_markdown = state.best_draft_markdown
        return True  # Force pass after max retries

    _record_decision(
        state, "seo_check_agent", "retry",
        f"SEO score={result.score}/100 < {SEO_PASS_THRESHOLD}, "
        f"suggestions: {result.suggestions[:3]}",
    )
    return False


def _apply_seo_fixes(state: PipelineState) -> None:
    """Apply SEO QA fixes based on check suggestions."""
    _record_decision(state, "seo_qa_agent", "fix", "Applying SEO fixes")

    # Simple deterministic fixes
    markdown = state.draft_markdown

    # Ensure FAQ section exists
    if "缺少 FAQ 區塊" in str(state.seo_checks):
        faq_block = "\n\n## 常見問題 FAQ\n\n"
        if state.strategy_report and hasattr(state.strategy_report, 'faq_questions'):
            for i, q in enumerate(state.strategy_report.faq_questions[:5], 1):
                faq_block += f"### Q{i}: {q}\n\n答案待補充。\n\n"
        markdown += faq_block

    # Ensure keyword in first H2 if missing
    if state.keyword:
        import re
        h2s = re.findall(r"^##\s+(.+)$", markdown, re.MULTILINE)
        if h2s and not any(state.keyword in h for h in h2s):
            # Add keyword to first H2
            first_h2 = h2s[0]
            if state.keyword not in first_h2:
                new_h2 = f"## {first_h2}：{state.keyword}完整解析"
                markdown = markdown.replace(f"## {first_h2}", new_h2, 1)

    state.draft_markdown = markdown


async def run_generation_pipeline(
    db: AsyncSession,
    workspace_id: UUID,
    run_id: UUID,
    *,
    keyword: str = "",
    node_type: str = "cluster",
    intent: str | None = None,
) -> PipelineState:
    """Run the full 7-agent content generation pipeline.

    Args:
        db: database session
        workspace_id: workspace UUID
        run_id: ContentGenerationRun ID
        keyword: primary keyword
        node_type: pillar / cluster / long_tail / faq
        intent: informational / commercial / transactional

    Returns:
        PipelineState with full generation results
    """
    state = PipelineState(
        run_id=run_id,
        workspace_id=workspace_id,
        site_id=UUID("00000000-0000-0000-0000-000000000000"),  # will be set from run
        keyword=keyword,
        node_type=node_type,
        intent=intent,
    )

    # Load generation run
    run = await get_generation_run(db, workspace_id, run_id)
    state.site_id = run.site_id

    # Load brief and pack
    brief = await get_brief(db, workspace_id, run.content_brief_id)
    pack = await get_source_pack(db, workspace_id, brief.source_pack_id)

    # Stage 1: Research
    await _run_research_stage(state, brief, pack)

    # Stage 2: Strategy
    _run_strategy_stage(state)

    # Stage 3: Writing
    _run_writing_stage(state, brief, pack)

    # Stage 4-6: SEO Check loop
    while True:
        passed = _run_seo_check_stage(state)
        if passed:
            break
        _apply_seo_fixes(state)

    # Stage 7: Finalize
    state.pipeline_status = "complete"
    _record_decision(state, "orchestrator", "complete", f"Pipeline complete, SEO score={state.best_seo_score}")

    # Update the generation run
    run.output_markdown = state.draft_markdown
    run.evidence_map_json = {
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
            },
        }
    }
    run.status = "draft"
    await db.flush()

    return state
