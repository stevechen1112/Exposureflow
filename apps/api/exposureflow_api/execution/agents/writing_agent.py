"""Writing Agent — LLM section writing with evidence binding.

Ported from ContentFlow writing_agent + section_generator for ExposureFlow.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from exposureflow_api.execution.action_router import sanitize_source_refs
from exposureflow_api.execution.agents.strategy_agent import StrategyReport
from exposureflow_api.execution.compiler.outline_planner import (
    SectionPlan,
    plan_outline_from_strategy,
)
from exposureflow_api.execution.compiler.content_normalizer import normalize_article_markdown
from exposureflow_api.execution.compiler.section_generator import (
    build_schema_block,
    generate_section_markdown,
)
from exposureflow_api.execution.claim_verifier import extract_claims
from exposureflow_api.config import settings
from exposureflow_api.llm.client import chat_sync, llm_available
from exposureflow_api.models.execution_content import ContentBrief, ContentSourcePack


@dataclass(frozen=True)
class WritingResult:
    markdown: str
    meta_title: str
    meta_description: str
    evidence_map: dict
    generation_mode: str
    provider: str
    model: str | None
    qa_report: dict


class LlmCallBudget:
    def __init__(self, limit: int) -> None:
        self.limit = max(limit, 1)
        self.used = 0

    def consume(self) -> None:
        self.used += 1
        if self.used > self.limit:
            raise RuntimeError(
                f"LLM call budget exceeded ({self.used}>{self.limit}) for this generation run"
            )


def _budgeted_chat_sync(budget: LlmCallBudget | None, **kwargs: object) -> str:
    if budget is not None:
        budget.consume()
    return chat_sync(**kwargs)  # type: ignore[arg-type]


def _language_label(language: str | None) -> str:
    if not language:
        return "繁體中文"
    if language.lower().startswith("zh"):
        return "繁體中文"
    return language


def _format_facts_block(refs: list[dict]) -> str:
    if not refs:
        return "（無可用佐證事實，請僅撰寫概括性說明，避免具體數字或療效宣稱。）"
    lines: list[str] = []
    for ref in refs[:8]:
        subject = ref.get("subject") or ref.get("title") or "事實"
        fact = (ref.get("fact_text") or "").strip()
        if fact:
            lines.append(f"- {subject}：{fact}")
    return "\n".join(lines) if lines else "（無可用佐證事實。）"


def _generate_section_llm(
    *,
    keyword: str,
    plan: SectionPlan,
    refs: list[dict],
    strategy: StrategyReport | None,
    language: str,
    industry: str | None,
    forbidden_claims: list[str],
    temperature: float,
    budget: LlmCallBudget | None = None,
) -> str:
    bound_refs = [refs[i] for i in plan.source_ref_indexes if i < len(refs)]
    facts_block = _format_facts_block(bound_refs)
    strategy_ctx = strategy.to_context_dict() if strategy else {}

    forbidden_block = ""
    if forbidden_claims:
        forbidden_block = "禁止宣稱：" + "、".join(forbidden_claims[:10])

    system = f"""你是專業的 B2B/B2C 內容撰稿人，以{_language_label(language)}撰寫。
規則：
1. 僅能根據「佐證事實」撰寫，不得捏造數據、療效、排名或保證。
2. 不得輸出英文段落標題（如 Introduction）；H2 使用繁體中文。
3. 不得輸出內部診斷碼（OG-xxx）或英文 CTA。
4. 段落約 {plan.target_word_count} 字，語氣專業、可讀。
{forbidden_block}"""

    user = f"""主題關鍵字：{keyword}
章節標題（H2）：{plan.heading}
章節目的：{plan.purpose}
產業：{industry or "一般"}
內容角度：{strategy_ctx.get("content_angle", "")}
競品缺口：{strategy_ctx.get("competitor_gap", "")}

佐證事實：
{facts_block}

請輸出 Markdown，以「## {plan.heading}」開頭，接著 2-4 段正文。不要輸出其他章節。"""

    raw = _budgeted_chat_sync(budget, messages=[{"role": "system", "content": system}, {"role": "user", "content": user}], temperature=temperature)
    raw = _strip_artifacts(raw)
    if not raw.strip().startswith("##"):
        raw = f"## {plan.heading}\n\n{raw.strip()}\n"
    return raw


def _generate_faq_llm(
    *,
    keyword: str,
    questions: list[str],
    refs: list[dict],
    language: str,
    word_budget: int,
    temperature: float,
    budget: LlmCallBudget | None = None,
) -> str:
    facts_block = _format_facts_block(refs)
    qs = questions[:6] if questions else [f"什麼是{keyword}？", f"{keyword}有哪些注意事項？"]
    system = f"""以{_language_label(language)}撰寫 FAQ。
每題以 **Q：** / **A：** 格式，問題須自然口語（避免「{keyword}是什麼是什麼」這類重複句）。
答案須有據於佐證事實，總字數約 {word_budget} 字。"""
    user = f"主題：{keyword}\n\n問題：\n" + "\n".join(f"{i+1}. {q}" for i, q in enumerate(qs)) + f"\n\n佐證事實：\n{facts_block}"
    raw = _budgeted_chat_sync(budget, messages=[{"role": "system", "content": system}, {"role": "user", "content": user}], temperature=temperature)
    raw = _strip_artifacts(raw)
    if not raw.strip().startswith("##"):
        raw = f"## 常見問題 FAQ\n\n{raw.strip()}\n"
    return raw


def _strip_artifacts(text: str) -> str:
    text = re.sub(r"OG-\d{3}[^\n]*", "", text)
    text = re.sub(r"\[Learn more\]\([^)]+\)", "", text)
    text = re.sub(r"^##\s+(Introduction|Market context|Solution overview|Call to action)\s*$", "", text, flags=re.MULTILINE | re.IGNORECASE)
    return text.strip()


def _build_meta(
    *,
    keyword: str,
    brief: ContentBrief,
    strategy: StrategyReport | None,
    language: str,
    budget: LlmCallBudget | None = None,
) -> tuple[str, str]:
    hint_title = brief.brief_json.get("title_hint") or keyword
    hint_desc = brief.brief_json.get("description") or ""
    if llm_available():
        try:
            system = f"以{_language_label(language)}產出 SEO meta，JSON 格式：{{\"title\":\"\",\"description\":\"\"}}"
            user = f"關鍵字：{keyword}\n標題提示：{hint_title}\n角度：{(strategy.content_angle if strategy else '')}\n描述提示：{hint_desc}"
            raw = _budgeted_chat_sync(
                budget,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=0.3,
                max_tokens=200,
            )
            import json

            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                data = json.loads(match.group())
                title = str(data.get("title") or hint_title)[:60]
                desc = str(data.get("description") or hint_desc)[:160]
                return title, desc
        except Exception:
            pass
    title = f"{keyword}完整指南" if keyword else str(hint_title)
    if len(title) > 60:
        title = title[:57] + "…"
    desc = hint_desc or f"深入了解{keyword}的選擇要點、常見問題與實用建議。"
    return title[:60], desc[:160]


def run_writing_agent(
    *,
    keyword: str,
    brief: ContentBrief,
    source_pack: ContentSourcePack,
    strategy_report: StrategyReport | None = None,
    site_context: dict | None = None,
    forbidden_claims: list[str] | None = None,
    temperature: float = 0.55,
) -> WritingResult:
    """Compile evidence-bound draft via LLM (fallback: template sections)."""
    site_context = site_context or {}
    industry = site_context.get("industry")
    language = brief.language or source_pack.language or site_context.get("primary_locale") or "zh-TW"
    market = brief.market or source_pack.market
    refs = sanitize_source_refs(list(source_pack.source_refs_json or []))
    forbidden = list(forbidden_claims or brief.forbidden_claims_json or [])

    sections = plan_outline_from_strategy(brief, source_pack, strategy_report)
    use_llm = llm_available()
    provider = "openai" if use_llm else "grounded_template"
    model = None
    generation_mode = "grounded_llm" if use_llm else "grounded_template"
    llm_budget = LlmCallBudget(settings.llm_max_calls_per_run) if use_llm else None

    title = brief.brief_json.get("title_hint") or keyword or brief.brief_type.replace("_", " ")
    parts: list[str] = [f"# {title}\n"]
    evidence_map: dict[str, list] = {}
    total_words = 0

    faq_questions = list(strategy_report.faq_questions) if strategy_report else []
    faq_written = False

    for plan in sections:
        if plan.purpose in ("faq",) or "常見問題" in plan.heading or "FAQ" in plan.heading.upper():
            if use_llm:
                section_md = _generate_faq_llm(
                    keyword=keyword,
                    questions=faq_questions,
                    refs=refs,
                    language=language,
                    word_budget=plan.target_word_count,
                    temperature=temperature,
                    budget=llm_budget,
                )
                bound = refs[:6]
            else:
                section_md, bound = generate_section_markdown(plan, refs, market=market, language=language)
            faq_written = True
        elif use_llm:
            try:
                section_md = _generate_section_llm(
                    keyword=keyword,
                    plan=plan,
                    refs=refs,
                    strategy=strategy_report,
                    language=language,
                    industry=industry,
                    forbidden_claims=forbidden,
                    temperature=temperature,
                    budget=llm_budget,
                )
                bound = [refs[i] for i in plan.source_ref_indexes if i < len(refs)]
            except Exception:
                section_md, bound = generate_section_markdown(plan, refs, market=market, language=language)
                generation_mode = "grounded_template"
                provider = "grounded_template"
        else:
            section_md, bound = generate_section_markdown(plan, refs, market=market, language=language)

        parts.append(section_md)
        evidence_map[plan.section_id] = bound
        total_words += len(re.findall(r"[\u4e00-\u9fff]", section_md))

    if not faq_written and faq_questions:
        faq_plan = SectionPlan("faq", "常見問題 FAQ", "faq", 300, list(range(min(len(refs), 6))))
        if use_llm:
            parts.append(
                _generate_faq_llm(
                    keyword=keyword,
                    questions=faq_questions,
                    refs=refs,
                    language=language,
                    word_budget=300,
                    temperature=temperature,
                    budget=llm_budget,
                )
            )
            evidence_map["faq"] = refs[:6]
        else:
            md, bound = generate_section_markdown(faq_plan, refs, market=market, language=language)
            parts.append(md)
            evidence_map["faq"] = bound

    if brief.brief_type == "faq":
        parts.append(build_schema_block("faq", refs))

    markdown = "\n".join(parts)
    markdown = _strip_artifacts(markdown)
    title = brief.brief_json.get("title_hint") or keyword or brief.brief_type.replace("_", " ")
    markdown = normalize_article_markdown(markdown, keyword=keyword, title=title)
    meta_title, meta_description = _build_meta(
        keyword=keyword, brief=brief, strategy=strategy_report, language=language, budget=llm_budget
    )

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
        "industry": industry,
        "warnings": [],
    }
    if float(source_pack.coverage_score or 0) < 0.5:
        qa_report["warnings"].append("source_coverage_below_threshold")
    if not refs:
        qa_report["warnings"].append("no_source_refs")

    return WritingResult(
        markdown=markdown,
        meta_title=meta_title,
        meta_description=meta_description,
        evidence_map=evidence_map,
        generation_mode=generation_mode,
        provider=provider,
        model=model,
        qa_report=qa_report,
    )
