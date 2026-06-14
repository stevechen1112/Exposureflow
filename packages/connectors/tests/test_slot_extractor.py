from connectors.serp.slot_extractor import extract_slots


def test_extract_organic_and_paa_slots() -> None:
    raw = {
        "_provider": "serper",
        "organic": [
            {
                "position": 1,
                "title": "Example",
                "link": "https://example.com/page",
                "snippet": "Snippet text",
            }
        ],
        "peopleAlsoAsk": [{"question": "What is example?"}],
        "relatedSearches": [{"query": "example guide"}],
    }
    slots = extract_slots(raw, site_domain="example.com")
    types = {s.slot_type for s in slots}
    assert "organic" in types
    assert "paa" in types
    assert "related_search" in types
    organic = next(s for s in slots if s.slot_type == "organic")
    assert organic.is_own_site is True


def test_ai_overview_only_when_provider_returns_it() -> None:
    raw = {"organic": [], "ai_overview": {"present": True}}
    slots = extract_slots(raw, site_domain="example.com")
    assert any(s.slot_type == "ai_overview" for s in slots)

    raw_no_ai = {"organic": []}
    slots_no_ai = extract_slots(raw_no_ai, site_domain="example.com")
    assert not any(s.slot_type == "ai_overview" for s in slots_no_ai)


def test_forum_classified_as_third_party() -> None:
    raw = {
        "organic": [
            {
                "position": 2,
                "link": "https://www.reddit.com/r/seo/comments/abc",
                "title": "Discussion",
            }
        ]
    }
    slots = extract_slots(raw, site_domain="mysite.com")
    organic = next(s for s in slots if s.slot_type == "organic")
    assert organic.is_third_party is True
