"""Outline and section planning from content brief."""

from __future__ import annotations

from dataclasses import dataclass

from exposureflow_api.execution.agents.strategy_agent import StrategyReport
from exposureflow_api.models.execution_content import ContentBrief, ContentSourcePack

ZH_DEFAULT_SECTIONS: dict[str, list[tuple[str, str, int]]] = {
    "article": [
        ("intro", "什麼是此主題？", 150),
        ("context", "為什麼重要", 180),
        ("solution", "如何選擇與比較", 220),
        ("proof", "實務建議與注意事項", 200),
        ("faq", "常見問題 FAQ", 280),
    ],
    "solution_page": [
        ("overview", "方案總覽", 180),
        ("capabilities", "核心能力", 220),
        ("use_cases", "適用情境", 200),
        ("proof", "客戶實績", 180),
        ("cta", "下一步", 80),
    ],
    "refresh": [
        ("summary", "更新摘要", 150),
        ("changes", "重點更新", 200),
        ("proof", "佐證資料", 150),
    ],
    "enrich": [
        ("addition", "補充說明", 200),
        ("proof", "佐證事實", 150),
    ],
    "faq": [
        ("faq", "常見問題 FAQ", 320),
    ],
}

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
    *,
    prefer_zh: bool = True,
) -> list[SectionPlan]:
    lang = (brief.language or source_pack.language or "").lower()
    use_zh = prefer_zh and (not lang or lang.startswith("zh"))
    catalog = ZH_DEFAULT_SECTIONS if use_zh else DEFAULT_SECTIONS
    templates = catalog.get(brief.brief_type, catalog["article"])
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


def plan_outline_from_strategy(
    brief: ContentBrief,
    source_pack: ContentSourcePack,
    strategy_report: StrategyReport | None = None,
) -> list[SectionPlan]:
    """Prefer strategy H2 outline; fallback to locale-aware default sections."""
    if not strategy_report or not strategy_report.outline_h2:
        return plan_outline(brief, source_pack)

    refs = source_pack.source_refs_json or []
    ref_count = max(len(refs), 1)
    outline = strategy_report.outline_h2
    plans: list[SectionPlan] = []

    for idx, heading in enumerate(outline):
        purpose = "faq" if ("FAQ" in heading.upper() or "常見問題" in heading) else "body"
        start = (idx * ref_count) // len(outline)
        end = ((idx + 1) * ref_count) // len(outline)
        indexes = list(range(start, max(start + 1, end))) or [idx % ref_count]
        plans.append(
            SectionPlan(
                section_id=f"sec_{idx}",
                heading=heading,
                purpose=purpose,
                target_word_count=200 if purpose != "faq" else 280,
                source_ref_indexes=indexes,
            )
        )
    return plans
