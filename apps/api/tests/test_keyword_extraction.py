"""Tests for keyword extraction from Strategy Intake."""

from exposureflow_api.models.strategy import BusinessIntake
from exposureflow_api.strategy.keyword_extraction import (
    assign_parent_ids,
    extract_keyword_candidates,
)


def _intake(**kwargs) -> BusinessIntake:
    base = {
        "workspace_id": "00000000-0000-0000-0000-000000000001",
        "site_id": "00000000-0000-0000-0000-000000000002",
        "company_summary": "台中紗窗維修與換紗窗服務",
        "sales_regions_json": ["台中"],
        "strategic_goals_json": [
            "台中紗窗維修自然搜尋曝光成為區域第一",
            "提升「修理紗窗」「換紗窗價格」等服務詞能見度",
        ],
        "constraints_json": ["不做全台服務", "不做 B2B 批發"],
    }
    base.update(kwargs)
    return BusinessIntake(**base)


def test_extracts_quoted_phrases_not_whole_goals() -> None:
    candidates = extract_keyword_candidates(_intake())
    keywords = {item.keyword for item in candidates}

    assert "修理紗窗" in keywords
    assert "換紗窗價格" in keywords
    assert "台中紗窗維修自然搜尋曝光成為區域第一" not in keywords
    assert "提升「修理紗窗」「換紗窗價格」等服務詞能見度" not in keywords


def test_extracts_region_service_cluster_candidates() -> None:
    candidates = extract_keyword_candidates(_intake())
    region_service = [item for item in candidates if item.source == "market_service"]
    assert any("台中" in item.keyword and "紗窗" in item.keyword for item in region_service)
    assert all(item.node_type == "cluster" for item in region_service)
    assert all("台中市換" not in item.keyword for item in candidates)


def test_assign_parent_ids_links_cluster_to_pillar() -> None:
    intake = _intake()
    rows = assign_parent_ids(extract_keyword_candidates(intake))
    child = next((row for row in rows if row["keyword"] == "修理紗窗"), None)
    assert child is not None
    assert child["business_fit_status"] == "needs_review"
    assert child["node_type"] in ("cluster", "long_tail", "pillar")
