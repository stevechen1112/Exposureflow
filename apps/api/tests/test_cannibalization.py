from exposureflow_api.topics.cannibalization import detect_gsc_cannibalization
from exposureflow_api.topics.graph_builder import QueryPageRow


def test_detect_gsc_cannibalization() -> None:
    rows = [
        QueryPageRow("widget reviews", "https://example.com/a", 60, 2, 8.0),
        QueryPageRow("widget reviews", "https://example.com/b", 50, 1, 12.0),
        QueryPageRow("widget reviews", "https://example.com/c", 5, 0, 25.0),
    ]
    findings = detect_gsc_cannibalization(rows, min_impressions=50)
    assert len(findings) == 1
    assert findings[0].recommendation in {"merge", "differentiate", "redirect"}
    assert len(findings[0].competing_urls) >= 2
    assert "gsc_query_overlap" in findings[0].evidence["source"]
