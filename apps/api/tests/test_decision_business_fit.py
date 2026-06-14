def test_blocked_keyword_always_no_op() -> None:
    from types import SimpleNamespace
    from uuid import uuid4

    from exposureflow_api.decision.candidate_generator import opportunity_to_candidate
    from exposureflow_api.strategy.business_fit import BusinessFitResult

    opp = SimpleNamespace(
        id=str(uuid4()),
        opportunity_type="add_image_asset",
        exposure_asset_id=None,
        keyword="blocked",
        current_url=None,
        target_url=None,
        search_context=None,
        priority="high",
        total_opportunity_score=50.0,
        current_impressions=10,
        current_position=None,
        reason="test",
        evidence_json={},
    )
    fit = BusinessFitResult(
        business_fit_score=0.0,
        business_fit_status="blocked",
        keyword_pyramid_node_id=None,
        product_service_scope_id=None,
        blocked=True,
        evidence={},
    )
    candidate = opportunity_to_candidate(opp, fit=fit)
    assert candidate.action_type == "no_op"
