from exposureflow_api.topics.internal_links import suggest_internal_links


def test_anchor_relevance() -> None:
    from exposureflow_api.topics.internal_links import anchor_relevance

    score = anchor_relevance("seo audit guide", "seo audit checklist")
    assert score > 0.2


def test_suggest_internal_links_sorted() -> None:
    suggestions = suggest_internal_links(
        pillar_url="https://example.com/pillar",
        pillar_keyword="seo audit",
        gap_nodes=[
            {"keyword": "seo audit tool", "current_best_url": "https://example.com/tool", "status": "gap"},
            {"keyword": "unrelated topic", "current_best_url": "https://example.com/other", "status": "gap"},
        ],
    )
    assert len(suggestions) == 2
    assert suggestions[0].anchor_relevance_score >= suggestions[1].anchor_relevance_score


def test_suggest_internal_links_for_gap_without_url() -> None:
    suggestions = suggest_internal_links(
        pillar_url="https://example.com/pillar",
        pillar_keyword="seo audit",
        gap_nodes=[{"keyword": "seo audit tool", "status": "gap"}],
        site_domain="example.com",
    )
    assert len(suggestions) == 1
    assert "seo-audit-tool" in suggestions[0].target_url
    assert suggestions[0].evidence.get("target_type") == "proposed_page"
