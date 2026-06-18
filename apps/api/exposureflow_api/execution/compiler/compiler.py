"""Grounded content compiler: brief → outline → draft → evidence map → QA report."""

from __future__ import annotations

from dataclasses import dataclass

from exposureflow_api.execution.agents.strategy_agent import StrategyReport
from exposureflow_api.execution.action_router import sanitize_source_refs
from exposureflow_api.execution.compiler.outline_planner import plan_outline, plan_outline_from_strategy
from exposureflow_api.execution.compiler.section_generator import (
    build_schema_block,
    generate_section_markdown,
)
from exposureflow_api.execution.claim_verifier import extract_claims
from exposureflow_api.models.execution_content import ContentBrief, ContentSourcePack


@dataclass(frozen=True)
class CompileResult:
    markdown: str
    evidence_map: dict
    qa_report: dict
    generation_mode: str
    review_level: str


def compile_grounded_draft(
    brief: ContentBrief,
    source_pack: ContentSourcePack,
    *,
    generation_mode: str = "grounded_template",
    review_level: str | None = None,
    strategy_report: StrategyReport | None = None,
    keyword: str | None = None,
    site_context: dict | None = None,
) -> CompileResult:
    if generation_mode == "grounded_llm":
        from exposureflow_api.execution.agents.writing_agent import run_writing_agent

        kw = keyword or brief.brief_json.get("title_hint") or brief.brief_type
        result = run_writing_agent(
            keyword=kw,
            brief=brief,
            source_pack=source_pack,
            strategy_report=strategy_report,
            site_context=site_context,
            forbidden_claims=list(brief.forbidden_claims_json or []),
        )
        level = review_level or brief.brief_json.get("review_policy", "editor_review")
        return CompileResult(
            markdown=result.markdown,
            evidence_map=result.evidence_map,
            qa_report=result.qa_report,
            generation_mode=result.generation_mode,
            review_level=level,
        )

    refs = sanitize_source_refs(list(source_pack.source_refs_json or []))
    title = brief.brief_json.get("title_hint") or brief.brief_type.replace("_", " ").title()
    market = brief.market or source_pack.market
    language = brief.language or source_pack.language
    level = review_level or brief.brief_json.get("review_policy", "editor_review")

    sections = plan_outline_from_strategy(brief, source_pack, strategy_report) if strategy_report else plan_outline(brief, source_pack)
    parts: list[str] = [f"# {title}\n"]
    evidence_map: dict[str, list] = {}
    total_words = 0

    for plan in sections:
        section_md, bound = generate_section_markdown(
            plan, refs, market=market, language=language
        )
        parts.append(section_md)
        evidence_map[plan.section_id] = bound
        total_words += len(section_md.split())

    if brief.brief_type == "faq":
        parts.append(build_schema_block("faq", refs))

    cta_url = brief.brief_json.get("target_url") or brief.brief_json.get("current_url")
    lang = (language or "").lower()
    if cta_url and brief.brief_type not in ("faq",):
        if lang.startswith("zh"):
            parts.append(f"\n---\n\n[了解更多]({cta_url})\n")
        else:
            parts.append(f"\n---\n\n[Learn more]({cta_url})\n")

    markdown = "\n".join(parts)
    from exposureflow_api.execution.compiler.content_normalizer import normalize_article_markdown

    markdown = normalize_article_markdown(markdown, keyword=keyword or title, title=title)
    claims = extract_claims(markdown)
    qa_report = {
        "word_count": total_words,
        "section_count": len(sections),
        "source_coverage_score": float(source_pack.coverage_score or 0),
        "claim_count": len(claims),
        "market": market,
        "language": language,
        "brief_type": brief.brief_type,
        "generation_mode": generation_mode,
        "review_level": level,
        "human_review_notes": [],
        "warnings": [],
    }
    if float(source_pack.coverage_score or 0) < 0.5:
        qa_report["warnings"].append("source_coverage_below_threshold")
    if not refs:
        qa_report["warnings"].append("no_source_refs")

    return CompileResult(
        markdown=markdown,
        evidence_map=evidence_map,
        qa_report=qa_report,
        generation_mode=generation_mode,
        review_level=level,
    )
