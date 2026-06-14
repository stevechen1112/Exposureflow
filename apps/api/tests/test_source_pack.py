"""Unit tests for source pack builder."""

from exposureflow_api.execution.source_pack import compute_coverage_score


def test_coverage_score_empty() -> None:
    assert compute_coverage_score([]) == 0.0


def test_coverage_score_with_company_owned() -> None:
    refs = [
        {"ref_type": "company_owned", "fact_text": "a"},
        {"ref_type": "company_owned", "fact_text": "b"},
        {"ref_type": "external_source", "fact_text": "c"},
    ]
    score = compute_coverage_score(refs)
    assert score > 0.5


def test_high_risk_brief_needs_multiple_categories() -> None:
    refs = [{"ref_type": "company_owned", "fact_text": "only one"}]
    score = compute_coverage_score(refs, brief_type="comparison")
    assert score <= 0.5
