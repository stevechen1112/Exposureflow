"""Strategy Agent: content angle + outline planning.

Modeled after ContentFlow's strategy_agent.py.
Takes ResearchReport and produces:
- Content angle (differentiation from competitors)
- Article outline (H2/H3 structure)
- FAQ questions to include
- Writing architecture recommendation
"""

from __future__ import annotations

from dataclasses import dataclass, field

from exposureflow_api.execution.agents.research_agent import ResearchReport, SerpIntelligence


@dataclass
class StrategyReport:
    """SEO strategy analysis for a single keyword/article."""
    keyword: str
    search_intent: str  # informational / commercial / transactional / navigational
    target_audience: str  # reader profile + pain points
    writing_architecture: str  # guide / comparison / howto / faq / listicle
    content_angle: str  # differentiation angle vs competitors
    competitor_gap: str  # what competitors are missing
    faq_questions: list[str] = field(default_factory=list)
    outline_h2: list[str] = field(default_factory=list)
    confidence: float = 0.8

    def to_context_dict(self) -> dict:
        """Convert to dict for writing agent consumption."""
        return {
            "search_intent": self.search_intent,
            "target_audience": self.target_audience,
            "writing_architecture": self.writing_architecture,
            "content_angle": self.content_angle,
            "competitor_gap": self.competitor_gap,
            "faq_questions": self.faq_questions[:6],
            "outline_h2": self.outline_h2,
        }


# ── Writing architecture templates ─────────────────────────────────────────

ARCHITECTURE_TEMPLATES: dict[str, dict] = {
    "comprehensive_guide": {
        "label": "完整指南型",
        "structure": [
            "什麼是{keyword}？（定義與背景）",
            "{keyword}的重要性與影響",
            "{keyword}的關鍵因素/挑選要點",
            "常見類型/選項分析",
            "實用建議與注意事項",
            "常見問題 FAQ",
        ],
        "best_for": ["informational", "pillar"],
    },
    "comparison_with_recommendations": {
        "label": "比較推薦型",
        "structure": [
            "{keyword}的常見選項概覽",
            "選項 A vs 選項 B 深度比較",
            "不同情境下的最佳選擇",
            "價格/CP值分析",
            "專家建議與推薦",
            "常見問題 FAQ",
        ],
        "best_for": ["commercial", "comparison"],
    },
    "faq_driven_with_deep_answers": {
        "label": "FAQ 驅動型",
        "structure": [
            "核心問題：{keyword}是什麼？",
            "讀者最常問的 5 個問題（逐一深答）",
            "進階問題與特殊情境",
            "專家補充觀點",
            "總結與行動建議",
        ],
        "best_for": ["informational", "faq", "long_tail"],
    },
    "howto_step_by_step": {
        "label": "步驟教學型",
        "structure": [
            "{keyword}的前置準備",
            "步驟一：...",
            "步驟二：...",
            "步驟三：...",
            "常見錯誤與避免方法",
            "常見問題 FAQ",
        ],
        "best_for": ["informational", "howto"],
    },
    "listicle_with_analysis": {
        "label": "清單分析型",
        "structure": [
            "{keyword}的評選標準",
            "Top N 推薦（逐一分析）",
            "綜合比較表",
            "不同需求的最佳選擇",
            "常見問題 FAQ",
        ],
        "best_for": ["commercial", "cluster"],
    },
}


def _infer_architecture(intent: str, node_type: str, difficulty_hint: str) -> str:
    """Infer best writing architecture from intent and SERP signals."""
    if node_type == "comparison" or intent == "commercial":
        return "comparison_with_recommendations"
    if node_type == "faq":
        return "faq_driven_with_deep_answers"
    if node_type == "long_tail" and intent == "informational":
        return "faq_driven_with_deep_answers"
    if difficulty_hint == "high":
        return "comprehensive_guide"  # need depth to compete
    if node_type == "pillar":
        return "comprehensive_guide"
    return "comprehensive_guide"


def _infer_audience(intent: str, keyword: str) -> str:
    """Infer target audience from intent and keyword signals."""
    if "價格" in keyword or "費用" in keyword or "報價" in keyword:
        return "正在比較價格、準備做購買決策的消費者"
    if "推薦" in keyword or "比較" in keyword:
        return "正在搜尋選項、評估不同方案的潛在客戶"
    if "如何" in keyword or "怎麼" in keyword or "步驟" in keyword:
        return "遇到具體問題、正在尋找解決方法的使用者"
    if intent == "commercial":
        return "有明確需求、正在比較產品/服務的潛在客戶"
    return "對主題有初步興趣、想了解更多資訊的一般讀者"


def _identify_competitor_gap(serp: SerpIntelligence) -> str:
    """Identify what competitors are missing."""
    gaps: list[str] = []

    if serp.content_patterns.faq_presence_rate < 0.5:
        gaps.append("多數競品缺少 FAQ 區塊")
    if serp.content_patterns.table_presence_rate < 0.3:
        gaps.append("競品少用比較表格")
    if serp.content_patterns.avg_word_count < 1500:
        gaps.append("競品內容深度不足（平均字數偏低）")
    if not serp.heading_patterns:
        gaps.append("競品文章結構較弱")

    if not gaps:
        # Look for missing angles in headings
        common_angles = {"定義", "原因", "症狀", "治療", "預防", "比較", "推薦", "價格", "步驟"}
        found_angles = set()
        for h in serp.heading_patterns:
            for angle in common_angles:
                if angle in h:
                    found_angles.add(angle)
        missing = common_angles - found_angles
        if missing:
            gaps.append(f"競品未覆蓋的角度：{', '.join(list(missing)[:3])}")

    if not gaps:
        return "競品內容完整，需以更深度或更在地化的角度切入"

    return "；".join(gaps)


def _build_outline(
    architecture: str,
    keyword: str,
    serp: SerpIntelligence,
    faq_questions: list[str],
) -> list[str]:
    """Build H2 outline based on architecture template and SERP data."""
    template = ARCHITECTURE_TEMPLATES.get(architecture, ARCHITECTURE_TEMPLATES["comprehensive_guide"])
    structure = template["structure"]

    # Fill in keyword placeholders
    outline = []
    for item in structure:
        filled = item.replace("{keyword}", keyword)
        outline.append(filled)

    # Add FAQ section if not already present
    if not any("FAQ" in h or "常見問題" in h for h in outline):
        outline.append("常見問題 FAQ")

    return outline


def _extract_faq_from_serp(serp: SerpIntelligence, keyword: str, max_faq: int = 8) -> list[str]:
    """Extract FAQ questions from PAA and related searches."""
    faq: list[str] = []

    # PAA questions are primary source
    for q in serp.paa_questions[:max_faq]:
        if q not in faq:
            faq.append(q)

    # Related searches as supplementary
    for q in serp.related_searches[:max_faq - len(faq)]:
        if q not in faq:
            faq.append(q)

    # Generate basic FAQ if none found
    if not faq:
        faq = [
            f"{keyword}是什麼？",
            f"{keyword}有哪些常見類型？",
            f"如何選擇適合的{keyword}？",
            f"{keyword}的價格範圍？",
            f"{keyword}需要注意什麼？",
        ]

    return faq[:max_faq]


def run_strategy_agent(
    research: ResearchReport,
    *,
    node_type: str = "cluster",
    intent: str | None = None,
) -> StrategyReport:
    """Run the Strategy Agent to produce content strategy from research.

    This is a deterministic (non-LLM) agent that uses SERP intelligence
    to recommend content angle, architecture, and outline.
    """
    serp = research.serp_intelligence

    # Infer search intent
    search_intent = intent or serp.top_intent

    # Infer writing architecture
    architecture = _infer_architecture(search_intent, node_type, serp.difficulty_hint)

    # Infer target audience
    audience = _infer_audience(search_intent, research.keyword)

    # Identify competitor gap
    competitor_gap = _identify_competitor_gap(serp)

    # Determine content angle
    angle = research.recommended_angle or "comprehensive_guide"

    # Extract FAQ questions
    faq = _extract_faq_from_serp(serp, research.keyword)

    # Build outline
    outline = _build_outline(architecture, research.keyword, serp, faq)

    return StrategyReport(
        keyword=research.keyword,
        search_intent=search_intent,
        target_audience=audience,
        writing_architecture=architecture,
        content_angle=angle,
        competitor_gap=competitor_gap,
        faq_questions=faq,
        outline_h2=outline,
        confidence=0.85,
    )
