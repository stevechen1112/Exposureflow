from types import SimpleNamespace

from exposureflow_api.decision.roadmap_builder import build_roadmap_items
from exposureflow_api.decision.selector import build_rule_rationale, rank_candidates


def test_build_rule_rationale_includes_rule_id() -> None:
    candidate = SimpleNamespace(
        action_type="optimize_snippet",
        action_payload_json={"keyword": "running shoes"},
        expected_exposure_impact=65.0,
        risk_level="high",
        evidence_json={"rule_id": "OG-002"},
    )
    text = build_rule_rationale(candidate)
    assert "OG-002" in text
    assert "optimize_snippet" in text


def test_rank_candidates_by_score() -> None:
    rows = [
        SimpleNamespace(id="b", rank_score=40, expected_exposure_impact=40, risk_level="medium"),
        SimpleNamespace(id="a", rank_score=80, expected_exposure_impact=80, risk_level="high"),
    ]
    ranked = rank_candidates(rows)
    assert ranked[0].id == "a"


def test_build_roadmap_items_weeks() -> None:
    decision = SimpleNamespace(id="d1")
    candidate = SimpleNamespace(
        id="c1",
        action_type="technical_fix",
        action_payload_json={"keyword": "brand", "current_url": "https://example.com"},
        risk_level="high",
        expected_exposure_impact=90.0,
    )
    items = build_roadmap_items(
        approved_rows=[(decision, candidate)],
        horizon_weeks=8,
    )
    assert len(items) == 1
    assert 1 <= items[0].week_number <= 8
