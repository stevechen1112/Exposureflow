"""Keyword enrichment helpers stored in evidence_json."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

TARGETABLE_SLOT_TYPES = frozenset(
    {
        "featured_snippet",
        "paa",
        "image",
        "video",
        "product",
        "ai_overview",
        "related_search",
    }
)


def merge_enrichment(existing: dict | None, patch: dict) -> dict:
    base = dict(existing or {})
    current = dict(base.get("enrichment") or {})
    current.update(patch)
    current.setdefault("last_enriched_at", datetime.now(UTC).isoformat())
    base["enrichment"] = current
    return base


def targetable_slot_count(slots: list[Any]) -> int:
    seen: set[str] = set()
    for slot in slots:
        slot_type = getattr(slot, "slot_type", None) or (slot.get("slot_type") if isinstance(slot, dict) else None)
        if slot_type in TARGETABLE_SLOT_TYPES:
            seen.add(str(slot_type))
    return len(seen)


def serp_features_from_slots(slots: list[Any]) -> list[str]:
    features: list[str] = []
    for slot in slots:
        slot_type = getattr(slot, "slot_type", None) or (slot.get("slot_type") if isinstance(slot, dict) else None)
        if slot_type and slot_type not in features:
            features.append(str(slot_type))
    return features


def paa_questions_from_slots(slots: list[Any]) -> list[str]:
    out: list[str] = []
    for slot in slots:
        slot_type = getattr(slot, "slot_type", None) or (slot.get("slot_type") if isinstance(slot, dict) else None)
        if slot_type != "paa":
            continue
        title = getattr(slot, "title", None) or (slot.get("title") if isinstance(slot, dict) else None)
        if title and str(title).strip():
            out.append(str(title).strip())
    return out


def related_searches_from_slots(slots: list[Any]) -> list[str]:
    out: list[str] = []
    for slot in slots:
        slot_type = getattr(slot, "slot_type", None) or (slot.get("slot_type") if isinstance(slot, dict) else None)
        if slot_type != "related_search":
            continue
        title = getattr(slot, "title", None) or (slot.get("title") if isinstance(slot, dict) else None)
        if title and str(title).strip():
            out.append(str(title).strip())
    return out


def organic_top_domains(slots: list[Any], *, limit: int = 5) -> list[str]:
    domains: list[str] = []
    for slot in slots:
        slot_type = getattr(slot, "slot_type", None) or (slot.get("slot_type") if isinstance(slot, dict) else None)
        if slot_type != "organic":
            continue
        domain = getattr(slot, "owner_domain", None) or (slot.get("owner_domain") if isinstance(slot, dict) else None)
        if domain and domain not in domains:
            domains.append(str(domain))
        if len(domains) >= limit:
            break
    return domains


def enrichment_from_serp(
    *,
    slots: list[Any],
    provider: str,
    source: str,
    seed_keyword: str | None = None,
) -> dict[str, Any]:
    return {
        "targetable_slot_count": targetable_slot_count(slots),
        "serp_features": serp_features_from_slots(slots),
        "paa_questions": paa_questions_from_slots(slots),
        "related_searches": related_searches_from_slots(slots),
        "organic_top_domains": organic_top_domains(slots),
        "source": source,
        "provider": provider,
        "seed_keyword": seed_keyword,
        "last_enriched_at": datetime.now(UTC).isoformat(),
    }
