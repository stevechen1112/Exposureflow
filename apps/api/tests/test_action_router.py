"""Tests for content action routing."""

import pytest

from exposureflow_api.common.errors import APIError
from exposureflow_api.execution.action_router import (
    assert_content_generation_eligible,
    format_candidate_label,
    is_content_generation_action,
    is_usable_source_fact,
    sanitize_source_refs,
)


def test_content_generation_action_types() -> None:
    assert is_content_generation_action("create_page")
    assert is_content_generation_action("enrich")
    assert not is_content_generation_action("merge_pages")
    assert not is_content_generation_action("refresh_page")


def test_assert_content_generation_eligible_raises() -> None:
    with pytest.raises(APIError) as exc:
        assert_content_generation_eligible("merge_pages")
    assert exc.value.detail["error"]["code"] == "ACTION_NOT_CONTENT_ELIGIBLE"


def test_format_candidate_label() -> None:
    label = format_candidate_label(
        action_type="create_page",
        action_payload_json={"keyword": "換紗窗價格", "target_url": "https://example.com/pricing"},
    )
    assert "換紗窗價格" in label
    assert "create_page" in label
    assert "example.com" in label


def test_sanitize_source_refs_filters_diagnostics() -> None:
    refs = [
        {"fact_text": "OG-004: Multiple URLs competing for same keyword"},
        {"fact_text": "換紗窗價格約 3,000–8,000 元", "subject": "價格"},
    ]
    cleaned = sanitize_source_refs(refs)
    assert len(cleaned) == 1
    assert is_usable_source_fact(cleaned[0]["fact_text"])
