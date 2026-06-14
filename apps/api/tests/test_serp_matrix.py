from exposureflow_api.serp.matrix import build_matrix_from_slots, slot_matrix_status, target_status_from_matrix


def test_slot_matrix_status_owned() -> None:
    assert slot_matrix_status(
        slot_type="featured_snippet",
        is_own_site=True,
        is_competitor=False,
        is_third_party=False,
        has_slot=True,
    ) == "owned"


def test_build_matrix_from_slots() -> None:
    cells = build_matrix_from_slots(
        keyword="seo tool",
        snapshot_id="snap-1",
        slots=[
            {
                "slot_type": "featured_snippet",
                "url": "https://rival.com/page",
                "is_own_site": False,
                "is_competitor": True,
                "is_third_party": False,
                "owner_domain": "rival.com",
                "title": "Best SEO",
            }
        ],
    )
    fs = next(c for c in cells if c.slot_type == "featured_snippet")
    assert fs.matrix_status == "competitor"
    assert target_status_from_matrix(fs.matrix_status) == "target"
