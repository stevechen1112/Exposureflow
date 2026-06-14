from exposureflow_api.ai_visibility.citation_extractor import (
    extract_citations,
    extract_urls_from_text,
    merge_cited_urls,
)


def test_extract_urls_from_text() -> None:
    text = "See https://example.com/page and https://rival.com/x for details."
    urls = extract_urls_from_text(text)
    assert "https://example.com/page" in urls
    assert "https://rival.com/x" in urls


def test_merge_cited_urls_dedupes() -> None:
    merged = merge_cited_urls(
        ["https://example.com/a"],
        "Also see https://example.com/a and https://other.com",
    )
    assert merged == ["https://example.com/a", "https://other.com"]


def test_extract_citations_classifies_own_site() -> None:
    citations = extract_citations(
        answer_text="Best shoes at https://mybrand.com/shoes",
        explicit_urls=[],
        site_domain="mybrand.com",
        competitor_domains={"rival.com"},
        our_brand_names={"MyBrand"},
    )
    assert len(citations) == 1
    assert citations[0].is_own_site is True
    assert citations[0].is_competitor is False
