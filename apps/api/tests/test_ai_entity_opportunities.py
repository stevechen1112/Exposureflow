from types import SimpleNamespace

from exposureflow_api.ai_visibility.entity_checker import check_entity_consistency
from exposureflow_api.ai_visibility.opportunities import (
    detect_ai_citation_ready,
    detect_entity_fix,
)


def test_entity_consistency_wrong_info() -> None:
    mentions = [
        SimpleNamespace(
            source_url="https://ai.example",
            mention_text="Wrong founding year",
            sentiment="wrong_info",
        )
    ]
    result = check_entity_consistency(
        canonical_name="Acme",
        description="Founded 2020",
        aliases=[],
        mentions=mentions,
    )
    assert result.consistency_score == 75.0
    assert len(result.inconsistencies) == 1


def test_og010_ai_citation_ready() -> None:
    runs = [
        SimpleNamespace(our_url_cited=False, external_url_cited=True),
        SimpleNamespace(our_url_cited=False, external_url_cited=True),
    ]
    candidate = detect_ai_citation_ready(
        prompt="best running shoes",
        runs=runs,
        has_reinforceable_asset=True,
    )
    assert candidate is not None
    assert candidate.rule_id == "OG-010"


def test_og011_entity_fix() -> None:
    candidate = detect_entity_fix(
        prompt="what is acme",
        sentiment="wrong_info",
        our_brand_mentioned=True,
        probe_run_id="run-1",
    )
    assert candidate is not None
    assert candidate.opportunity_type == "entity_fix"
