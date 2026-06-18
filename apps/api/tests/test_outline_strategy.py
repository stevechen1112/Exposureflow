"""Tests for strategy-driven outline planning."""

from types import SimpleNamespace

from exposureflow_api.execution.agents.strategy_agent import StrategyReport
from exposureflow_api.execution.compiler.outline_planner import plan_outline_from_strategy


def _brief(**kwargs):
    defaults = {"brief_type": "article", "language": "zh-TW", "brief_json": {}}
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _pack(**kwargs):
    defaults = {
        "source_refs_json": [
            {"subject": "A", "fact_text": "事實 A"},
            {"subject": "B", "fact_text": "事實 B"},
        ],
        "language": "zh-TW",
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_plan_outline_from_strategy_uses_h2_headings() -> None:
    strategy = StrategyReport(
        keyword="換紗窗價格",
        search_intent="informational",
        target_audience="屋主",
        writing_architecture="comprehensive_guide",
        content_angle="價格透明",
        competitor_gap="缺少 FAQ",
        outline_h2=["換紗窗價格怎麼算？", "常見問題 FAQ"],
        faq_questions=["換紗窗要多少錢？"],
    )
    plans = plan_outline_from_strategy(_brief(), _pack(), strategy)
    assert len(plans) == 2
    assert plans[0].heading == "換紗窗價格怎麼算？"
    assert plans[1].purpose == "faq"
