"""Outline and section planning from content brief."""

from __future__ import annotations

from dataclasses import dataclass

from exposureflow_api.models.execution_content import ContentBrief, ContentSourcePack

DEFAULT_SECTIONS: dict[str, list[tuple[str, str, int]]] = {
    "article": [
        ("intro", "Introduction", 120),
        ("context", "Market context", 150),
        ("solution", "Solution overview", 200),
        ("proof", "Proof points", 180),
        ("cta", "Call to action", 80),
    ],
    "solution_page": [
        ("overview", "Solution overview", 150),
        ("capabilities", "Core capabilities", 220),
        ("use_cases", "Use cases", 200),
        ("proof", "Customer proof", 180),
        ("cta", "Next steps", 80),
    ],
    "refresh": [
        ("summary", "Updated summary", 150),
        ("changes", "Key updates", 200),
        ("proof", "Supporting evidence", 150),
    ],
    "enrich": [
        ("addition", "Enrichment section", 180),
        ("proof", "Supporting facts", 120),
    ],
    "faq": [
        ("faq", "FAQ block", 300),
    ],
}


@dataclass(frozen=True)
class SectionPlan:
    section_id: str
    heading: str
    purpose: str
    target_word_count: int
    source_ref_indexes: list[int]


def plan_outline(
    brief: ContentBrief,
    source_pack: ContentSourcePack,
) -> list[SectionPlan]:
    templates = DEFAULT_SECTIONS.get(brief.brief_type, DEFAULT_SECTIONS["article"])
    refs = source_pack.source_refs_json or []
    if not refs:
        return [
            SectionPlan(
                section_id="intro",
                heading="Introduction",
                purpose="intro",
                target_word_count=100,
                source_ref_indexes=[],
            )
        ]

    plans: list[SectionPlan] = []
    ref_count = len(refs)
    for idx, (section_id, heading, word_count) in enumerate(templates):
        start = (idx * ref_count) // len(templates)
        end = ((idx + 1) * ref_count) // len(templates)
        indexes = list(range(start, max(start + 1, end)))
        if not indexes and ref_count:
            indexes = [idx % ref_count]
        plans.append(
            SectionPlan(
                section_id=section_id,
                heading=heading,
                purpose=section_id,
                target_word_count=word_count,
                source_ref_indexes=indexes,
            )
        )
    return plans
