from types import SimpleNamespace

from exposureflow_api.decision.candidate_generator import (
    generate_candidates_from_opportunities,
    opportunity_to_candidate,
)


def test_opportunity_to_candidate_deterministic() -> None:
    opp = SimpleNamespace(
        id="11111111-1111-1111-1111-111111111111",
        opportunity_type="refresh_page",
        exposure_asset_id=None,
        keyword="seo tools",
        current_url="https://example.com/page",
        target_url=None,
        search_context=None,
        priority="high",
        total_opportunity_score=72.5,
        current_impressions=500,
        current_position=12.0,
        reason="OG-001 test",
        evidence_json={"rule_id": "OG-001"},
    )
    first = opportunity_to_candidate(opp)
    second = opportunity_to_candidate(opp)
    assert first == second
    assert first.action_type == "refresh_page"
    assert first.risk_level == "high"
    assert first.evidence_json["rule_id"] == "OG-001"


def test_generate_candidates_ordering() -> None:
    opps = [
        SimpleNamespace(
            id="22222222-2222-2222-2222-222222222222",
            opportunity_type="add_faq",
            exposure_asset_id=None,
            keyword="a",
            current_url=None,
            target_url=None,
            search_context=None,
            priority="medium",
            total_opportunity_score=40.0,
            current_impressions=10,
            current_position=None,
            reason="low",
            evidence_json={},
        ),
        SimpleNamespace(
            id="11111111-1111-1111-1111-111111111111",
            opportunity_type="technical_fix",
            exposure_asset_id=None,
            keyword="b",
            current_url="https://example.com/x",
            target_url=None,
            search_context=None,
            priority="critical",
            total_opportunity_score=70.0,
            current_impressions=100,
            current_position=None,
            reason="high",
            evidence_json={},
        ),
    ]
    ranked = generate_candidates_from_opportunities(opps)
    assert ranked[0].action_type == "technical_fix"


def test_blocked_technical_fix_does_not_get_rank_boost() -> None:
    from exposureflow_api.strategy.business_fit import BusinessFitResult

    opp = SimpleNamespace(
        id="33333333-3333-3333-3333-333333333333",
        opportunity_type="technical_fix",
        exposure_asset_id=None,
        keyword="blocked kw",
        current_url="https://example.com/x",
        target_url=None,
        search_context=None,
        priority="critical",
        total_opportunity_score=70.0,
        current_impressions=100,
        current_position=None,
        reason="blocked",
        evidence_json={},
    )
    fit = BusinessFitResult(
        business_fit_score=0.0,
        business_fit_status="blocked",
        keyword_pyramid_node_id=None,
        product_service_scope_id=None,
        blocked=True,
        evidence={"status": "blocked"},
    )
    candidate = opportunity_to_candidate(opp, fit=fit)
    assert candidate.action_type == "no_op"
    assert candidate.rank_score == 0.0
