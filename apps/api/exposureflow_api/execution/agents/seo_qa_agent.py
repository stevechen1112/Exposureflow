"""SEO QA Agent — low-risk SEO micro-fixes after seo_check failures."""

from __future__ import annotations

import re

from exposureflow_api.execution.agents.strategy_agent import StrategyReport
from exposureflow_api.llm.client import chat_sync, llm_available


def _normalize_meta_title(meta_title: str, keyword: str) -> str:
    meta_title = meta_title.strip()
    if keyword and keyword not in meta_title:
        meta_title = f"{keyword}｜{meta_title}" if meta_title else keyword
    return meta_title[:60].strip()


def _normalize_meta_description(meta_description: str, keyword: str) -> str:
    meta_description = meta_description.strip()
    if keyword and keyword not in meta_description:
        meta_description = f"深入了解{keyword}的重點資訊。{meta_description}".strip()
    return meta_description[:160].strip()


def _append_faq_block(markdown: str, strategy: StrategyReport | None, keyword: str) -> str:
    if "## 常見問題" in markdown or "## FAQ" in markdown.upper():
        return markdown
    faq_block = "\n\n## 常見問題 FAQ\n\n"
    questions = strategy.faq_questions[:5] if strategy and strategy.faq_questions else [
        f"{keyword}要注意什麼？",
        f"什麼情況建議請專業師傅處理？",
    ]
    for q in questions:
        faq_block += f"**Q：{q}**\n\n**A：** 以下整理常見重點，詳情請參考上文說明。\n\n"
    return markdown.rstrip() + faq_block


def apply_seo_qa_fixes(
    *,
    markdown: str,
    keyword: str,
    meta_title: str,
    meta_description: str,
    failed_checks: list[dict] | None = None,
    strategy_report: StrategyReport | None = None,
    language: str = "zh-TW",
) -> tuple[str, str, str]:
    """Apply deterministic + optional LLM SEO fixes."""
    failed = failed_checks or []
    failed_names = {c.get("name") or c.get("check") or "" for c in failed}
    out_md = markdown
    out_title = meta_title
    out_desc = meta_description

    if any("FAQ" in n or "faq" in n.lower() for n in failed_names):
        out_md = _append_faq_block(out_md, strategy_report, keyword)

    out_title = _normalize_meta_title(out_title, keyword)
    out_desc = _normalize_meta_description(out_desc, keyword)

    if llm_available() and failed:
        try:
            system = f"以繁體中文微調文章首段與 meta，保留事實、低風險。語言：{language}"
            user = (
                f"關鍵字：{keyword}\n"
                f"未通過檢查：{failed_names}\n"
                f"meta_title：{out_title}\n"
                f"meta_description：{out_desc}\n"
                f"文章前 800 字：\n{out_md[:800]}\n\n"
                "請回傳 JSON：{\"meta_title\":\"\",\"meta_description\":\"\",\"opening_paragraph\":\"\"}"
            )
            raw = chat_sync(messages=[{"role": "system", "content": system}, {"role": "user", "content": user}], temperature=0.2, max_tokens=400)
            import json

            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                data = json.loads(match.group())
                if data.get("meta_title"):
                    out_title = str(data["meta_title"])[:60]
                if data.get("meta_description"):
                    out_desc = str(data["meta_description"])[:160]
                opening = data.get("opening_paragraph")
                if opening and isinstance(opening, str):
                    lines = out_md.splitlines()
                    h1_end = 0
                    for i, line in enumerate(lines):
                        if line.startswith("# ") and i == 0:
                            h1_end = i + 1
                            break
                    rest = "\n".join(lines[h1_end:]).lstrip()
                    out_md = lines[0] + "\n\n" + opening.strip() + "\n\n" + rest
        except Exception:
            pass

    return out_md, out_title, out_desc
