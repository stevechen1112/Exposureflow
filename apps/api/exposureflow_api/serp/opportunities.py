"""SERP-specific opportunity rules (OG-002, OG-007, OG-008)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SerpOpportunityCandidate:
    rule_id: str
    opportunity_type: str
    keyword: str
    current_url: str | None
    impressions: int
    position: float | None
    reason: str
    targetable_slot_count: int
    extra_evidence: dict


def detect_featured_snippet_opportunity(
    *,
    keyword: str,
    impressions: int,
    position: float | None,
    p75: int,
    featured_slot: dict | None,
    current_url: str | None,
) -> SerpOpportunityCandidate | None:
    if impressions < p75:
        return None
    if position is None or not (4 <= position <= 10):
        return None
    if not featured_slot or featured_slot.get("is_own_site"):
        return None
    return SerpOpportunityCandidate(
        rule_id="OG-002",
        opportunity_type="optimize_snippet",
        keyword=keyword,
        current_url=current_url,
        impressions=impressions,
        position=position,
        reason="OG-002: Position 4-10 with featured snippet owned by competitor",
        targetable_slot_count=2,
        extra_evidence={
            "featured_snippet_url": featured_slot.get("url"),
            "featured_owner_domain": featured_slot.get("owner_domain"),
        },
    )


def detect_paa_opportunities(
    *,
    keyword: str,
    current_url: str | None,
    impressions: int,
    paa_slots: list[dict],
    own_urls: set[str],
) -> list[SerpOpportunityCandidate]:
    if not paa_slots:
        return []
    missing = []
    for paa in paa_slots:
        question = paa.get("title") or paa.get("snippet") or ""
        if not question:
            continue
        answer_url = paa.get("url")
        if answer_url and answer_url in own_urls:
            continue
        missing.append(question)
    if not missing:
        return []
    return [
        SerpOpportunityCandidate(
            rule_id="OG-007",
            opportunity_type="add_faq",
            keyword=keyword,
            current_url=current_url,
            impressions=impressions,
            position=None,
            reason="OG-007: SERP PAA questions without matching FAQ on target page",
            targetable_slot_count=len(missing),
            extra_evidence={"paa_questions": missing[:10]},
        )
    ]


def detect_media_slot_opportunities(
    *,
    keyword: str,
    current_url: str | None,
    impressions: int,
    image_slot: dict | None,
    video_slot: dict | None,
    has_image_asset: bool,
    has_video_asset: bool,
) -> list[SerpOpportunityCandidate]:
    results: list[SerpOpportunityCandidate] = []
    if image_slot and not has_image_asset:
        results.append(
            SerpOpportunityCandidate(
                rule_id="OG-008",
                opportunity_type="add_image_asset",
                keyword=keyword,
                current_url=current_url,
                impressions=impressions,
                position=None,
                reason="OG-008: SERP image slot present without matching image asset",
                targetable_slot_count=1,
                extra_evidence={"slot_type": "image"},
            )
        )
    if video_slot and not has_video_asset:
        results.append(
            SerpOpportunityCandidate(
                rule_id="OG-008",
                opportunity_type="add_video_asset",
                keyword=keyword,
                current_url=current_url,
                impressions=impressions,
                position=None,
                reason="OG-008: SERP video slot present without matching video asset",
                targetable_slot_count=1,
                extra_evidence={"slot_type": "video"},
            )
        )
    return results
