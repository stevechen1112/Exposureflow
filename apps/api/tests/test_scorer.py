from exposureflow_api.exposure.scorer import ScoreInput, score_opportunity


def test_scorer_is_deterministic() -> None:
    data = ScoreInput(
        query_impressions_28d=500,
        site_p95_query_impressions=1000,
        current_position=8.0,
        targetable_slot_count=2,
    )
    a = score_opportunity(data)
    b = score_opportunity(data)
    assert a.total_opportunity_score == b.total_opportunity_score
    assert "subscores" in a.evidence
    assert a.evidence["subscores"]["search_demand_score"] > 0


def test_scorer_evidence_trace() -> None:
    result = score_opportunity(
        ScoreInput(
            query_impressions_28d=100,
            site_p95_query_impressions=500,
            current_position=15.0,
            targetable_slot_count=1,
        )
    )
    assert "formula" in result.evidence
    assert result.evidence["inputs"]["current_position"] == 15.0
