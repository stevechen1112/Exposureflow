"""Unit tests for execution adapters EF-0810–0813."""

from exposureflow_api.execution.adapters.outreach import run_outreach_adapter
from exposureflow_api.execution.adapters.refresh import run_refresh_adapter
from exposureflow_api.execution.adapters.schema_enhancement import run_schema_adapter
from exposureflow_api.execution.adapters.technical_fix import run_technical_fix_adapter


def test_refresh_adapter() -> None:
    result = run_refresh_adapter(
        {"current_url": "https://example.com/page", "keyword": "industrial pump"}
    )
    assert result.success
    assert result.output["adapter"] == "refresh"
    assert "update_suggestions" in result.output


def test_schema_adapter_faq() -> None:
    result = run_schema_adapter(
        {
            "schema_type": "faq",
            "entities": [{"subject": "Q1", "fact_text": "A1"}],
        }
    )
    assert result.success
    assert "schema:faq" in result.output["output_markdown"]


def test_technical_fix_adapter() -> None:
    result = run_technical_fix_adapter(
        {"issue_type": "noindex", "current_url": "https://example.com/x"}
    )
    assert result.success
    assert result.output["issue_type"] == "noindex"


def test_outreach_adapter() -> None:
    result = run_outreach_adapter(
        {"keyword": "pump", "outreach_targets": ["industry-blog.com"]}
    )
    assert result.success
    assert result.output["requires_human"] is True
