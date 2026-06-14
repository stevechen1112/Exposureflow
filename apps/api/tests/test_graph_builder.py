from exposureflow_api.topics.graph_builder import (
    QueryPageRow,
    aggregate_query_stats,
    build_query_graph,
    coverage_score,
    jaccard_similarity,
    keyword_level,
    tokenize,
)


def test_jaccard_similarity() -> None:
    a = tokenize("seo audit tool")
    b = tokenize("seo audit checklist")
    assert jaccard_similarity(a, b) > 0.3


def test_build_query_graph_clusters_cooccurring_queries() -> None:
    rows = [
        QueryPageRow("seo tips", "https://example.com/a", 100, 5, 8.0),
        QueryPageRow("seo guide", "https://example.com/a", 80, 3, 10.0),
        QueryPageRow("paid ads", "https://example.com/b", 200, 10, 5.0),
    ]
    uf = build_query_graph(rows)
    groups = uf.groups()
    assert len(groups) == 2


def test_coverage_score() -> None:
    assert coverage_score(3, 4) == 75.0


def test_keyword_level() -> None:
    assert keyword_level("seo") == "head"
    assert keyword_level("best seo audit tool") == "mid_tail"
