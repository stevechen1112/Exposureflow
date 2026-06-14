from types import SimpleNamespace

from exposureflow_api.ai_visibility.brand_monitor import (
    compute_visibility_metrics,
    detect_mentioned_brands,
)


def test_detect_mentioned_brands() -> None:
    brands = detect_mentioned_brands(
        "MyBrand and RivalCo are mentioned here",
        explicit_brands=[],
        known_brands={"MyBrand", "RivalCo"},
    )
    assert "MyBrand" in brands
    assert "RivalCo" in brands


def test_compute_visibility_metrics() -> None:
    runs = [
        SimpleNamespace(our_brand_mentioned=True, our_url_cited=False, competitor_mentions_json=[]),
        SimpleNamespace(our_brand_mentioned=False, our_url_cited=True, competitor_mentions_json=[{}]),
        SimpleNamespace(our_brand_mentioned=False, our_url_cited=False, competitor_mentions_json=[{}]),
    ]
    metrics = compute_visibility_metrics(runs)
    assert metrics.total_runs == 3
    assert metrics.visibility_score == 66.67
    assert metrics.competitor_mention_rate == 66.67
