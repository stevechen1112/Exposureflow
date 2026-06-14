"""Unit tests for Business Fit Gate."""

from types import SimpleNamespace
from uuid import uuid4

from exposureflow_api.strategy.business_fit import (
    BusinessFitResult,
    evaluate_keyword_fit,
    normalize_keyword,
    score_from_fit_status,
)


def test_normalize_keyword() -> None:
    assert normalize_keyword("  SEO Tools  ") == "seo tools"
    assert normalize_keyword(None) == ""


def test_score_from_fit_status_blocked() -> None:
    assert score_from_fit_status("blocked") == 0.0
    assert score_from_fit_status("out_of_scope") == 0.0


def test_score_from_fit_status_in_scope_active() -> None:
    assert score_from_fit_status("in_scope", scope_status="active", approved=True) == 1.0


def test_score_from_fit_status_planned() -> None:
    score = score_from_fit_status("in_scope", scope_status="planned", approved=True)
    assert score == 0.8


def test_evaluate_keyword_fit_no_match() -> None:
    result = evaluate_keyword_fit("unknown keyword", {}, {})
    assert result.business_fit_score == 0.5
    assert result.blocked is False
    assert result.business_fit_status == "needs_review"


def test_evaluate_keyword_fit_blocked() -> None:
    scope_id = uuid4()
    node = SimpleNamespace(
        id=uuid4(),
        keyword="competitor product",
        business_fit_status="blocked",
        product_service_scope_id=scope_id,
        approved_at=None,
        node_type="cluster",
        priority=3,
    )
    scope = SimpleNamespace(id=scope_id, status="active")
    result = evaluate_keyword_fit(
        "competitor product",
        {normalize_keyword(node.keyword): node},
        {scope_id: scope},
    )
    assert isinstance(result, BusinessFitResult)
    assert result.business_fit_score == 0.0
    assert result.blocked is True


def test_evaluate_keyword_fit_in_scope() -> None:
    scope_id = uuid4()
    node = SimpleNamespace(
        id=uuid4(),
        keyword="industrial pump",
        business_fit_status="in_scope",
        product_service_scope_id=scope_id,
        approved_at="2026-01-01",
        node_type="pillar",
        priority=5,
    )
    scope = SimpleNamespace(id=scope_id, status="active")
    result = evaluate_keyword_fit(
        "industrial pump",
        {normalize_keyword(node.keyword): node},
        {scope_id: scope},
    )
    assert result.business_fit_score == 1.0
    assert result.blocked is False
