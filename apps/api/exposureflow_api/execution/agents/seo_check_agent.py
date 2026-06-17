"""SEO Check Agent: rule-based SEO quality verification.

Modeled after ContentFlow's seo_check_agent.py.
Checks: keyword density, meta quality, H2 structure, FAQ presence,
keyword stuffing, internal link suggestions, schema readiness.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class SEOCheckResult:
    """Result of SEO quality check."""
    passed: bool
    score: int  # 0-100
    checks: list[dict] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    critical_failures: list[str] = field(default_factory=list)


def _count_chinese_chars(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text or ""))


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _get_h2s(markdown: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"^##\s+(.+)$", markdown or "", re.MULTILINE)]


def _get_h3s(markdown: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"^###\s+(.+)$", markdown or "", re.MULTILINE)]


def _contains_faq(markdown: str) -> bool:
    return bool(re.search(r"^##\s+(FAQ|常見問題)", markdown or "", re.MULTILINE | re.IGNORECASE))


def _keyword_in_text(keyword: str, text: str) -> bool:
    return bool(keyword and keyword in (text or ""))


def _count_keyword_occurrences(keyword: str, text: str) -> int:
    if not keyword or not text:
        return 0
    return len(re.findall(re.escape(keyword), text))


def _get_first_paragraph(markdown: str) -> str:
    lines = (markdown or "").splitlines()
    paragraph: list[str] = []
    started = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if started:
                break
            continue
        if stripped.startswith("#"):
            continue
        if not started:
            started = True
        paragraph.append(stripped)
    return _clean_text(" ".join(paragraph))


def _keyword_density(keyword: str, content: str) -> float:
    """Calculate keyword density (occurrences * keyword_len / total chars)."""
    if not keyword or not content:
        return 0.0
    count = _count_keyword_occurrences(keyword, content)
    total_chars = len(content.replace(" ", ""))
    if total_chars == 0:
        return 0.0
    return round((count * len(keyword)) / total_chars, 4)


def _check_meta_title(title: str, keyword: str) -> tuple[bool, str]:
    """Check meta title quality."""
    if not title:
        return False, "缺少 meta title"
    if len(title) < 15:
        return False, f"meta title 過短（{len(title)} 字，建議 30-60 字）"
    if len(title) > 70:
        return False, f"meta title 過長（{len(title)} 字，建議 ≤60 字）"
    if keyword and keyword not in title:
        return False, f"meta title 缺少主關鍵字「{keyword}」"
    return True, f"meta title OK（{len(title)} 字，含關鍵字）"


def _check_meta_description(desc: str, keyword: str) -> tuple[bool, str]:
    """Check meta description quality."""
    if not desc:
        return False, "缺少 meta description"
    if len(desc) < 50:
        return False, f"meta description 過短（{len(desc)} 字，建議 120-160 字）"
    if len(desc) > 170:
        return False, f"meta description 過長（{len(desc)} 字，建議 ≤160 字）"
    if keyword and keyword not in desc:
        return False, f"meta description 缺少主關鍵字「{keyword}」"
    return True, f"meta description OK（{len(desc)} 字）"


def _check_h2_structure(h2s: list[str], keyword: str) -> tuple[bool, str]:
    """Check H2 heading structure."""
    if not h2s:
        return False, "缺少 H2 標題（文章結構不完整）"
    if len(h2s) < 3:
        return False, f"H2 數量不足（{len(h2s)} 個，建議 ≥4 個）"
    if keyword and not any(keyword in h for h in h2s):
        return False, f"所有 H2 都缺少主關鍵字「{keyword}」"
    return True, f"H2 結構 OK（{len(h2s)} 個標題）"


def _check_faq_section(markdown: str) -> tuple[bool, str]:
    """Check FAQ section presence."""
    if _contains_faq(markdown):
        return True, "有 FAQ 區塊"
    return False, "缺少 FAQ 區塊（建議加入以爭取 PAA 版位）"


def _check_keyword_stuffing(
    keyword: str,
    first_paragraph: str,
    full_content: str,
) -> tuple[bool, str]:
    """Check for keyword stuffing in first paragraph and overall."""
    if not keyword:
        return True, "無主關鍵字"

    # First paragraph check
    fp_count = _count_keyword_occurrences(keyword, first_paragraph)
    if fp_count > 3:
        return False, f"首段關鍵字「{keyword}」出現 {fp_count} 次（疑似堆砌，建議 ≤2 次）"

    # Overall density check
    density = _keyword_density(keyword, full_content)
    if density > 0.03:
        return False, f"關鍵字密度 {density:.2%} 偏高（建議 0.5%-2%）"
    if density < 0.002:
        return False, f"關鍵字密度 {density:.2%} 偏低（建議 ≥0.5%）"

    return True, f"關鍵字密度 OK（{density:.2%}）"


def _check_word_count(markdown: str, target: int = 1500) -> tuple[bool, str]:
    """Check total word count."""
    cjk = _count_chinese_chars(markdown)
    eng = len(re.findall(r"[a-zA-Z]+", markdown))
    total = cjk + eng // 2
    if total < target * 0.7:
        return False, f"字數不足（{total}，目標 ≥{int(target * 0.7)}）"
    return True, f"字數 OK（{total}）"


def _check_internal_links(markdown: str) -> tuple[bool, str]:
    """Check for internal link suggestions."""
    # Count markdown links
    links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", markdown)
    if len(links) < 2:
        return False, f"內部連結不足（{len(links)} 個，建議 ≥3 個）"
    return True, f"內部連結 OK（{len(links)} 個）"


def _check_schema_readiness(markdown: str) -> tuple[bool, str]:
    """Check if content has schema blocks."""
    if "<!-- schema:" in markdown:
        return True, "已包含 schema 標記"
    return False, "缺少 schema 標記（建議加入 FAQ/Article schema）"


def run_seo_check(
    *,
    markdown: str,
    keyword: str,
    meta_title: str = "",
    meta_description: str = "",
    target_word_count: int = 1500,
) -> SEOCheckResult:
    """Run full SEO quality check on generated content.

    Returns SEOCheckResult with score 0-100 and detailed checks.
    """
    checks: list[dict] = []
    critical_failures: list[str] = []
    suggestions: list[str] = []
    total_weight = 0.0
    earned_weight = 0.0

    # 1. Meta title (weight: 10)
    passed, msg = _check_meta_title(meta_title, keyword)
    checks.append({"check": "meta_title", "passed": passed, "message": msg, "weight": 10})
    total_weight += 10
    if passed:
        earned_weight += 10
    else:
        suggestions.append(f"修復 meta title：{msg}")

    # 2. Meta description (weight: 8)
    passed, msg = _check_meta_description(meta_description, keyword)
    checks.append({"check": "meta_description", "passed": passed, "message": msg, "weight": 8})
    total_weight += 8
    if passed:
        earned_weight += 8
    else:
        suggestions.append(f"修復 meta description：{msg}")

    # 3. H2 structure (weight: 15)
    h2s = _get_h2s(markdown)
    passed, msg = _check_h2_structure(h2s, keyword)
    checks.append({"check": "h2_structure", "passed": passed, "message": msg, "weight": 15})
    total_weight += 15
    if passed:
        earned_weight += 15
    else:
        suggestions.append(f"改善 H2 結構：{msg}")
        if not h2s:
            critical_failures.append("文章完全缺少 H2 標題")

    # 4. FAQ section (weight: 10)
    passed, msg = _check_faq_section(markdown)
    checks.append({"check": "faq_section", "passed": passed, "message": msg, "weight": 10})
    total_weight += 10
    if passed:
        earned_weight += 10
    else:
        suggestions.append(msg)

    # 5. Keyword stuffing (weight: 12)
    first_p = _get_first_paragraph(markdown)
    passed, msg = _check_keyword_stuffing(keyword, first_p, markdown)
    checks.append({"check": "keyword_stuffing", "passed": passed, "message": msg, "weight": 12})
    total_weight += 12
    if passed:
        earned_weight += 12
    else:
        suggestions.append(f"調整關鍵字密度：{msg}")

    # 6. Word count (weight: 10)
    passed, msg = _check_word_count(markdown, target_word_count)
    checks.append({"check": "word_count", "passed": passed, "message": msg, "weight": 10})
    total_weight += 10
    if passed:
        earned_weight += 10
    else:
        suggestions.append(msg)

    # 7. Internal links (weight: 8)
    passed, msg = _check_internal_links(markdown)
    checks.append({"check": "internal_links", "passed": passed, "message": msg, "weight": 8})
    total_weight += 8
    if passed:
        earned_weight += 8
    else:
        suggestions.append(msg)

    # 8. Schema readiness (weight: 7)
    passed, msg = _check_schema_readiness(markdown)
    checks.append({"check": "schema_readiness", "passed": passed, "message": msg, "weight": 7})
    total_weight += 7
    if passed:
        earned_weight += 7
    else:
        suggestions.append(msg)

    # 9. H3 structure bonus (weight: 5)
    h3s = _get_h3s(markdown)
    has_h3 = len(h3s) >= 2
    checks.append({
        "check": "h3_structure",
        "passed": has_h3,
        "message": f"H3 子標題 {'OK' if has_h3 else '不足'}（{len(h3s)} 個）",
        "weight": 5,
    })
    total_weight += 5
    if has_h3:
        earned_weight += 5
    else:
        suggestions.append("建議加入 H3 子標題以改善內容結構")

    # 10. Keyword in H1/first heading (weight: 5)
    h1_match = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
    h1_text = h1_match.group(1) if h1_match else ""
    kw_in_h1 = keyword and keyword in h1_text
    checks.append({
        "check": "keyword_in_h1",
        "passed": kw_in_h1,
        "message": f"主關鍵字{'在' if kw_in_h1 else '不在'} H1 標題中",
        "weight": 5,
    })
    total_weight += 5
    if kw_in_h1:
        earned_weight += 5
    else:
        suggestions.append("建議將主關鍵字放入 H1 標題")

    # Calculate score
    score = round((earned_weight / total_weight) * 100) if total_weight > 0 else 0
    passed = score >= 85 and len(critical_failures) == 0

    return SEOCheckResult(
        passed=passed,
        score=score,
        checks=checks,
        suggestions=suggestions,
        critical_failures=critical_failures,
    )
