from connectors.types import SerpSlotData

from exposureflow_api.strategy.keyword_enrichment import (
    enrichment_from_serp,
    merge_enrichment,
    targetable_slot_count,
)
from exposureflow_api.strategy.keyword_research import (
    expand_candidates_from_serp,
    infer_keyword_level,
    infer_node_type,
)


def test_targetable_slot_count_deduplicates_types():
    slots = [
        SerpSlotData(slot_type="paa", title="問題 A"),
        SerpSlotData(slot_type="paa", title="問題 B"),
        SerpSlotData(slot_type="featured_snippet", title="摘要"),
    ]
    assert targetable_slot_count(slots) == 2


def test_enrichment_from_serp_includes_paa_and_related():
    slots = [
        SerpSlotData(slot_type="paa", title="紗窗怎麼修？"),
        SerpSlotData(slot_type="related_search", title="台中紗窗維修"),
        SerpSlotData(slot_type="organic", position=1, owner_domain="example.com"),
    ]
    enrichment = enrichment_from_serp(
        slots=slots,
        provider="serper",
        source="test",
        seed_keyword="修理紗窗",
    )
    assert enrichment["targetable_slot_count"] >= 2
    assert "紗窗怎麼修？" in enrichment["paa_questions"]
    assert "台中紗窗維修" in enrichment["related_searches"]


def test_merge_enrichment_preserves_existing_keys():
    merged = merge_enrichment({"source": "cold_start"}, {"targetable_slot_count": 3})
    assert merged["source"] == "cold_start"
    assert merged["enrichment"]["targetable_slot_count"] == 3


def test_expand_candidates_from_serp_adds_seed_and_related():
    slots = [
        SerpSlotData(slot_type="related_search", title="換紗窗價格"),
        SerpSlotData(slot_type="paa", title="紗窗修理費用多少"),
    ]
    candidates = expand_candidates_from_serp(
        seed_keyword="修理紗窗",
        slots=slots,
        provider="serper",
        max_expansions=5,
    )
    keywords = [c.keyword for c in candidates]
    assert "修理紗窗" in keywords
    assert "換紗窗價格" in keywords


def test_infer_node_type_and_level():
    assert infer_node_type("紗窗修理費用多少") == "faq"
    assert infer_keyword_level("faq") == "long_tail"
    assert infer_keyword_level("core") == "head"
