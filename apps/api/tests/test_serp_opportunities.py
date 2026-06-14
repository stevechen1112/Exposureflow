from exposureflow_api.serp.opportunities import (
    detect_featured_snippet_opportunity,
    detect_media_slot_opportunities,
    detect_paa_opportunities,
)


def test_og002_featured_snippet() -> None:
    cand = detect_featured_snippet_opportunity(
        keyword="seo audit",
        impressions=500,
        position=6.0,
        p75=100,
        featured_slot={
            "url": "https://rival.com",
            "is_own_site": False,
            "owner_domain": "rival.com",
        },
        current_url="https://example.com/page",
    )
    assert cand is not None
    assert cand.rule_id == "OG-002"


def test_og007_paa_gap() -> None:
    cands = detect_paa_opportunities(
        keyword="seo audit",
        current_url="https://example.com/page",
        impressions=200,
        paa_slots=[{"title": "What is SEO audit?", "url": "https://other.com"}],
        own_urls={"https://example.com/page"},
    )
    assert len(cands) == 1
    assert cands[0].opportunity_type == "add_faq"


def test_og008_media_slots() -> None:
    cands = detect_media_slot_opportunities(
        keyword="running shoes",
        current_url="https://example.com/shoes",
        impressions=100,
        image_slot={"slot_type": "image"},
        video_slot={"slot_type": "video"},
        has_image_asset=False,
        has_video_asset=False,
    )
    types = {c.opportunity_type for c in cands}
    assert "add_image_asset" in types
    assert "add_video_asset" in types
