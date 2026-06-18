"""Normalize generated article markdown before persist/publish."""

from __future__ import annotations

import re

_FAQ_Q_RE = re.compile(r"^\*\*Q\d*[：:]\s*(.+?)\*\*\s*$")
_PARAGRAPH_SPLIT_RE = re.compile(r"\n\s*\n+")

_HEADING_REWRITES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^什麼是.+？（定義與背景）$"), "先了解狀況與常見原因"),
    (re.compile(r"^.+的重要性與影響$"), "為什麼值得認真處理"),
    (re.compile(r"^.+的關鍵因素/挑選要點$"), "挑選與比較時要看什麼"),
    (re.compile(r"^常見類型/選項分析$"), "常見做法與適用情境"),
    (re.compile(r"^核心問題：.+是什麼？$"), "先搞懂核心問題"),
]


def _paragraph_fingerprint(text: str) -> str:
    t = re.sub(r"[，。！？、；：\s]", "", text.strip())
    t = (
        t.replace("會因為", "因")
        .replace("可能會因", "因")
        .replace("可能因", "因")
        .replace("出現破損", "破損")
        .replace("出現破洞", "破洞")
    )
    return t[:140]


def _strip_h1(markdown: str) -> str:
    lines = markdown.splitlines()
    if lines and lines[0].startswith("# "):
        return "\n".join(lines[1:]).lstrip("\n")
    return markdown


def _humanize_heading(heading: str) -> str:
    title = heading.strip()
    for pattern, replacement in _HEADING_REWRITES:
        if pattern.match(title):
            return replacement
    return title


def _humanize_headings(markdown: str) -> str:
    lines: list[str] = []
    for line in markdown.splitlines():
        if line.startswith("## "):
            heading = line[3:].strip()
            lines.append(f"## {_humanize_heading(heading)}")
        else:
            lines.append(line)
    return "\n".join(lines)


def _dedupe_paragraphs(markdown: str) -> str:
    blocks = _PARAGRAPH_SPLIT_RE.split(markdown.strip())
    seen: set[str] = set()
    kept: list[str] = []
    for block in blocks:
        stripped = block.strip()
        if not stripped:
            continue
        if stripped.startswith("## "):
            kept.append(stripped)
            continue
        key = _paragraph_fingerprint(stripped)
        if key in seen:
            continue
        seen.add(key)
        kept.append(stripped)
    return "\n\n".join(kept)


def _humanize_faq_question(question: str, keyword: str) -> str:
    q = question.strip().rstrip("？?")
    if q.endswith("是什麼") and keyword in q:
        if "價格" in keyword or "費用" in keyword:
            return f"{keyword}大概多少？"
        if "怎麼" in keyword or "如何" in keyword:
            return keyword if keyword.endswith("？") else f"{keyword}？"
        return f"什麼是{keyword}？"
    if q.startswith("如何選擇適合的"):
        return f"什麼情況建議請專業師傅處理？"
    if q.startswith(keyword) and "有哪些常見類型" in q:
        return "常見的破損類型有哪些？"
    if q.startswith(keyword) and "價格範圍" in q:
        return "維修或更換大概要多少錢？"
    if q.startswith(keyword) and "需要注意什麼" in q:
        return "處理時有哪些注意事項？"
    if not q.endswith("？") and not q.endswith("?"):
        q += "？"
    return q


def _normalize_faq_block(markdown: str, keyword: str) -> str:
    lines = markdown.splitlines()
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        match = _FAQ_Q_RE.match(stripped)
        if match:
            question = _humanize_faq_question(match.group(1), keyword)
            out.append(f"**Q：{question}**")
            continue
        if stripped.startswith("**Q") and "：" in stripped:
            qtext = stripped.split("：", 1)[-1].strip().strip("*")
            out.append(f"**Q：{_humanize_faq_question(qtext, keyword)}**")
            continue
        if stripped.startswith("A：") or stripped.startswith("A:"):
            answer = stripped.split("：", 1)[-1].strip()
            out.append("")
            out.append(f"**A：** {answer}")
            out.append("")
            continue
        out.append(line)
    return "\n".join(out)


def extract_excerpt(markdown: str, *, keyword: str = "", max_len: int = 160) -> str:
    if keyword:
        hook = f"師傅整理{keyword}的常見狀況、處理方式與注意事項，方便您快速判斷下一步。"
        return hook[:max_len]
    for block in _PARAGRAPH_SPLIT_RE.split(markdown.strip()):
        text = block.strip()
        if not text or text.startswith("## ") or text.startswith("**Q"):
            continue
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        if len(text) <= max_len:
            return text
        return text[: max_len - 1].rstrip() + "…"
    return ""


def infer_category(keyword: str, brief_type: str | None = None) -> str:
    if brief_type == "faq":
        return "常見問題"
    if any(token in keyword for token in ("價格", "費用", "報價", "多少錢")):
        return "價格說明"
    if any(token in keyword for token in ("保養", "清潔", "維護")):
        return "保養知識"
    if any(token in keyword for token in ("怎麼", "如何", "步驟")):
        return "維修建議"
    return "維修建議"


def normalize_article_markdown(
    markdown: str,
    *,
    keyword: str = "",
    title: str = "",
) -> str:
    """Produce publish-ready markdown: no H1 duplicate body, deduped paragraphs, cleaner FAQ."""
    text = markdown.strip()
    if not text:
        return text

    text = _strip_h1(text)
    if title:
        title_plain = title.strip()
        blocks = _PARAGRAPH_SPLIT_RE.split(text)
        filtered: list[str] = []
        for block in blocks:
            stripped = block.strip()
            if stripped == title_plain and not stripped.startswith("## "):
                continue
            filtered.append(stripped)
        text = "\n\n".join(filtered)

    text = _humanize_headings(text)
    text = _dedupe_paragraphs(text)
    if keyword:
        text = _normalize_faq_block(text, keyword)
    return text.strip() + "\n"
