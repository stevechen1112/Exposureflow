"""Tests for execution adapters."""

from exposureflow_api.execution.adapters.merge_pages import run_merge_pages_adapter
from exposureflow_api.execution.adapters.content_generation import run_content_generation_adapter
from exposureflow_api.execution.dispatcher import _resolve_adapter_key
from types import SimpleNamespace


def test_merge_pages_adapter_outputs_plan() -> None:
    result = run_merge_pages_adapter(
        {
            "keyword": "換紗窗價格",
            "canonical_url": "https://example.com/pricing",
            "urls": ["https://example.com/old-a", "https://example.com/old-b"],
        }
    )
    assert result.success
    assert result.output["canonical_url"] == "https://example.com/pricing"
    assert len(result.output["competing_urls"]) == 2


def test_content_generation_adapter_requires_brief() -> None:
    fail = run_content_generation_adapter({})
    assert not fail.success
    ok = run_content_generation_adapter({"brief_id": "abc"})
    assert ok.success


def test_dispatcher_resolves_action_type_from_input() -> None:
    job = SimpleNamespace(
        job_type="content_generation",
        input_json={"action_type": "merge_pages"},
    )
    assert _resolve_adapter_key(job) == "merge_pages"
