"""Tests for keyword_scorer.py — five-factor exposure opportunity model."""

from exposureflow_api.strategy.keyword_scorer import (
    KeywordScoreInput,
    _score_volume,
    _score_feasibility,
    _score_serp_diversity,
    _score_ai_citation,
    _score_topic_contribution,
    _classify_priority,
    estimate_search_volume_from_serp,
    estimate_competition_from_slots,
    extract_serp_features_from_slots,
    score_keyword,
    score_keywords_batch,
)


class TestVolumeScoring:
    def test_very_high_volume(self):
        assert _score_volume(5000) == 1.0

    def test_high_volume(self):
        assert _score_volume(2000) == 0.85

    def test_medium_volume(self):
        assert _score_volume(500) == 0.65

    def test_low_volume(self):
        assert _score_volume(200) == 0.40

    def test_very_low_volume(self):
        assert _score_volume(50) == 0.20

    def test_negligible_volume(self):
        assert _score_volume(5) == 0.05

    def test_zero_volume(self):
        assert _score_volume(0) == 0.05


class TestFeasibilityScoring:
    def test_already_ranking_top10(self):
        score = _score_feasibility(5, 50, True, 5.0)
        assert score == 0.95

    def test_already_ranking_top20(self):
        score = _score_feasibility(5, 50, True, 15.0)
        assert score == 0.75

    def test_low_competition(self):
        score = _score_feasibility(2, 15, False, 99.0)
        assert score >= 0.70

    def test_high_competition(self):
        score = _score_feasibility(9, 70, True, 99.0)
        assert score <= 0.40

    def test_medium_competition(self):
        score = _score_feasibility(5, 35, False, 99.0)
        assert 0.40 <= score <= 0.80


class TestSerpDiversity:
    def test_no_features(self):
        assert _score_serp_diversity([]) == 0.10

    def test_many_features(self):
        features = ["featured_snippet", "paa", "image", "ai_overview"]
        score = _score_serp_diversity(features)
        assert score >= 0.50

    def test_single_feature(self):
        assert _score_serp_diversity(["paa"]) > 0.10


class TestAICitation:
    def test_ai_overview_present(self):
        score = _score_ai_citation(True, ["has_faq_format"])
        assert score >= 0.40

    def test_no_ai_signals(self):
        score = _score_ai_citation(False, [])
        assert score == 0.10

    def test_multiple_signals(self):
        score = _score_ai_citation(True, ["has_faq_format", "has_original_data", "has_clear_structure"])
        assert score >= 0.60


class TestTopicContribution:
    def test_pillar_missing_page(self):
        score = _score_topic_contribution("pillar", 0.2, False)
        assert score >= 0.80

    def test_well_covered_cluster(self):
        score = _score_topic_contribution("cluster", 0.95, True)
        assert score <= 0.50

    def test_gap_cluster(self):
        score = _score_topic_contribution("cluster", 0.2, False)
        assert score >= 0.60


class TestPriorityClassification:
    def test_p1_high_feasibility(self):
        tier, label = _classify_priority(60.0, 0.75)
        assert tier == "P1"

    def test_p2_medium(self):
        tier, label = _classify_priority(30.0, 0.50)
        assert tier == "P2"

    def test_p3_low(self):
        tier, label = _classify_priority(10.0, 0.20)
        assert tier == "P3"


class TestFullScoring:
    def test_high_potential_keyword(self):
        inp = KeywordScoreInput(
            keyword="台中紗窗維修",
            node_type="pillar",
            intent="commercial",
            estimated_monthly_searches=800,
            volume_source="serper",
            competitor_domain_count=3,
            avg_competitor_da=25.0,
            top10_has_strong_domains=False,
            serp_features_present=["featured_snippet", "paa"],
            ai_overview_present=False,
            ai_citation_signals=["has_clear_structure"],
            topic_cluster_coverage=0.3,
            pillar_has_page=False,
            business_fit_status="in_scope",
            is_approved=True,
        )
        result = score_keyword(inp)
        assert result.total_score > 0
        assert result.priority_tier in ("P1", "P2")
        assert result.volume_score > 0
        assert result.feasibility_score > 0

    def test_low_potential_keyword(self):
        inp = KeywordScoreInput(
            keyword="紗窗",
            node_type="pillar",
            intent="informational",
            estimated_monthly_searches=50,
            volume_source="none",
            competitor_domain_count=9,
            avg_competitor_da=70.0,
            top10_has_strong_domains=True,
            serp_features_present=[],
            ai_overview_present=False,
            ai_citation_signals=[],
            topic_cluster_coverage=0.9,
            pillar_has_page=True,
            business_fit_status="in_scope",
            is_approved=True,
        )
        result = score_keyword(inp)
        assert result.total_score < 30
        assert result.priority_tier == "P3"

    def test_batch_scoring_sorts_by_score(self):
        inputs = [
            KeywordScoreInput(keyword="kw1", node_type="cluster", intent="commercial", estimated_monthly_searches=1000, competitor_domain_count=2, avg_competitor_da=15, serp_features_present=["paa", "featured_snippet"]),
            KeywordScoreInput(keyword="kw2", node_type="cluster", intent="informational", estimated_monthly_searches=50, competitor_domain_count=8, avg_competitor_da=70, serp_features_present=[]),
        ]
        results = score_keywords_batch(inputs)
        assert results[0].keyword == "kw1"
        assert results[0].total_score > results[1].total_score


class TestSerpDataExtraction:
    def test_extract_features_from_slots(self):
        slots = [
            {"slot_type": "organic", "position": 1},
            {"slot_type": "featured_snippet", "position": 0},
            {"slot_type": "paa", "position": None},
            {"slot_type": "paa", "position": None},
        ]
        features = extract_serp_features_from_slots(slots)
        assert "organic" in features
        assert "featured_snippet" in features
        assert "paa" in features

    def test_estimate_volume_from_serper(self):
        raw = {"searchVolume": 1200, "organic": [{}] * 10}
        vol = estimate_search_volume_from_serp(raw)
        assert vol == 1200

    def test_estimate_volume_fallback(self):
        raw = {"organic": [{}] * 10}
        vol = estimate_search_volume_from_serp(raw)
        assert vol == 200

    def test_estimate_competition(self):
        slots = [
            {"slot_type": "organic", "owner_domain": "competitor1.com", "is_own_site": False},
            {"slot_type": "organic", "owner_domain": "competitor2.com", "is_own_site": False},
            {"slot_type": "organic", "owner_domain": "competitor1.com", "is_own_site": False},
            {"slot_type": "organic", "owner_domain": "wikipedia.org", "is_own_site": False},
        ]
        count, avg_da, has_strong = estimate_competition_from_slots(slots)
        assert count == 3  # unique domains: competitor1, competitor2, wikipedia
        assert has_strong  # wikipedia
        assert avg_da >= 30
