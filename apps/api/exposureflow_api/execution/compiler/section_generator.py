"""Section-level grounded draft generation from source refs."""

from __future__ import annotations

from exposureflow_api.execution.compiler.outline_planner import SectionPlan


def _truncate_words(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "…"


def generate_section_markdown(
    plan: SectionPlan,
    source_refs: list[dict],
    *,
    market: str | None = None,
    language: str | None = None,
) -> tuple[str, list[dict]]:
    bound_refs = [source_refs[i] for i in plan.source_ref_indexes if i < len(source_refs)]
    if not bound_refs:
        lang = (language or "").lower()
        if lang.startswith("zh"):
            body = (
                f"本節說明{plan.heading.replace('？', '')}的重點。"
                "發布前請補充更多佐證資料。"
            )
        else:
            body = (
                f"This section covers {plan.purpose.replace('_', ' ')}. "
                "Additional evidence should be added before publish."
            )
        return f"## {plan.heading}\n\n{body}\n", []

    paragraphs: list[str] = []
    for ref in bound_refs:
        subject = ref.get("subject") or ref.get("title") or plan.heading
        fact = ref.get("fact_text") or ""
        if fact:
            paragraphs.append(f"**{subject}**: {_truncate_words(fact, plan.target_word_count // max(len(bound_refs), 1))}")

    locale_note = ""
    if market or language:
        locale_note = f"\n\n*Target market: {market or 'default'} | Language: {language or 'default'}*"

    body = "\n\n".join(paragraphs) if paragraphs else "Evidence-backed content pending."
    markdown = f"## {plan.heading}\n\n{body}{locale_note}\n"
    return markdown, bound_refs


def build_schema_block(brief_type: str, faq_refs: list[dict]) -> str:
    if brief_type != "faq" or not faq_refs:
        return ""
    items = []
    for ref in faq_refs[:8]:
        q = ref.get("subject") or "Question"
        a = ref.get("fact_text") or ""
        items.append(f'- {{ "@type": "Question", "name": "{q}", "acceptedAnswer": {{ "@type": "Answer", "text": "{a}" }} }}')
    if not items:
        return ""
    inner = ",\n    ".join(items)
    return f"\n<!-- schema:faq -->\n```json\n{{\n  \"@context\": \"https://schema.org\",\n  \"@type\": \"FAQPage\",\n  \"mainEntity\": [\n    {inner}\n  ]\n}}\n```\n"
