"""Execution agents package.

Research Agent → Strategy Agent → Writing Agent
→ SEO Check Agent ⇄ SEO QA Agent
→ FactCheck Agent → Publish Gate

Modeled after ContentFlow's 7-agent pipeline.
"""

from exposureflow_api.execution.agents.research_agent import (
    ResearchReport,
    SerpIntelligence,
    CompetitorDepth,
    ContentPatternSignals,
    run_research_agent,
)
from exposureflow_api.execution.agents.strategy_agent import (
    StrategyReport,
    run_strategy_agent,
)
from exposureflow_api.execution.agents.seo_check_agent import (
    SEOCheckResult,
    run_seo_check,
)

__all__ = [
    "ResearchReport",
    "SerpIntelligence",
    "CompetitorDepth",
    "ContentPatternSignals",
    "run_research_agent",
    "StrategyReport",
    "run_strategy_agent",
    "SEOCheckResult",
    "run_seo_check",
]
