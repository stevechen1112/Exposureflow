"""Regression: content service and orchestrator must not circular-import."""

from types import SimpleNamespace


def test_app_and_pipeline_import_without_cycle() -> None:
    from exposureflow_api.main import app
    from exposureflow_api.execution.agents.orchestrator import run_generation_pipeline
    from exposureflow_api.content.service import create_generation_run

    assert app is not None
    assert callable(run_generation_pipeline)
    assert callable(create_generation_run)


def test_pipeline_params_from_brief_reads_search_context() -> None:
    from exposureflow_api.content.repository import pipeline_params_from_brief

    brief = SimpleNamespace(
        brief_type="article",
        brief_json={
            "title_hint": "換紗窗價格",
            "search_context": {"node_type": "long_tail", "intent": "informational"},
        },
    )
    params = pipeline_params_from_brief(brief)
    assert params["keyword"] == "換紗窗價格"
    assert params["node_type"] == "long_tail"
    assert params["intent"] == "informational"
