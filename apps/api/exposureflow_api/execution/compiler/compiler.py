"""Grounded content compiler: brief → outline → draft → evidence map → QA report."""

from __future__ import annotations

from dataclasses import dataclass

from exposureflow_api.execution.compiler.outline_planner import plan_outline
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
) -> CompileResult:
    refs = list(source_pack.source_refs_json or [])
    title = brief.brief_json.get("title_hint") or brief.brief_type.replace("_", " ").title()
    market = brief.market or source_pack.market
    language = brief.language or source_pack.language
    level = review_level or brief.brief_json.get("review_policy", "editor_review")

    sections = plan_outline(brief, source_pack)
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
    if cta_url and brief.brief_type not in ("faq",):
        parts.append(f"\n---\n\n[Learn more]({cta_url})\n")

    markdown = "\n".join(parts)
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
