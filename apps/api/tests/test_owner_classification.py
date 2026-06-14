from exposureflow_api.exposure.owner_classification import classify_url_owner


def test_classify_own_domain() -> None:
    result = classify_url_owner(
        "https://www.example.com/blog/post",
        site_domain="example.com",
        competitor_domains={"rival.com"},
    )
    assert result.owner_type == "owned"
    assert result.is_own is True


def test_classify_competitor_subdomain() -> None:
    result = classify_url_owner(
        "https://shop.rival.com/page",
        site_domain="example.com",
        competitor_domains={"rival.com"},
    )
    assert result.owner_type == "competitor"
    assert result.is_competitor is True


def test_classify_third_party_forum() -> None:
    result = classify_url_owner(
        "https://www.reddit.com/r/seo",
        site_domain="example.com",
        competitor_domains=set(),
    )
    assert result.owner_type == "third_party"
    assert result.is_third_party is True
