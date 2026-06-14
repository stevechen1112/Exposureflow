from exposureflow_api.serp.owner import apply_owner_classification


class _Slot:
    url = "https://rival.com/page"
    owner_domain = None
    is_own_site = False
    is_competitor = False
    is_third_party = False


def test_apply_owner_classification_competitor() -> None:
    slot = _Slot()
    owner = apply_owner_classification(
        slot,
        site_domain="example.com",
        competitor_domains={"rival.com"},
    )
    assert owner.owner_type == "competitor"
    assert slot.is_competitor is True
