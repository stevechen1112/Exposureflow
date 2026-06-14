"""SERP slot matrix construction and owner status mapping."""

from __future__ import annotations

from dataclasses import dataclass

MATRIX_SLOT_TYPES = [
    "organic",
    "featured_snippet",
    "paa",
    "image",
    "video",
    "product",
    "ai_overview",
]


@dataclass
class SlotCell:
    keyword: str
    slot_type: str
    matrix_status: str
    owner_url: str | None
    owner_domain: str | None
    title: str | None
    snapshot_id: str | None


def slot_matrix_status(
    *,
    slot_type: str,
    is_own_site: bool,
    is_competitor: bool,
    is_third_party: bool,
    has_slot: bool,
) -> str:
    if not has_slot:
        return "available"
    if is_own_site:
        return "owned"
    if is_competitor:
        return "competitor"
    if is_third_party:
        return "third_party"
    return "blocked"


def target_status_from_matrix(matrix_status: str) -> str:
    if matrix_status == "owned":
        return "achieved"
    if matrix_status == "available":
        return "target"
    if matrix_status in {"competitor", "third_party", "blocked"}:
        return "target"
    return "not_applicable"


def recommended_action_for(matrix_status: str, slot_type: str) -> str | None:
    if matrix_status == "owned":
        return None
    if matrix_status == "available":
        return f"capture_{slot_type}"
    if matrix_status == "competitor":
        return f"outrank_{slot_type}"
    if matrix_status == "third_party":
        return f"earn_mention_{slot_type}"
    return f"improve_{slot_type}"


def build_matrix_from_slots(
    *,
    keyword: str,
    snapshot_id: str,
    slots: list[dict],
) -> list[SlotCell]:
    """Build keyword × slot_type matrix cells from normalized slot rows."""
    by_type: dict[str, dict] = {}
    for slot in slots:
        st = slot.get("slot_type")
        if st:
            by_type[st] = slot

    cells: list[SlotCell] = []
    for slot_type in MATRIX_SLOT_TYPES:
        slot = by_type.get(slot_type)
        has_slot = slot is not None
        matrix_status = slot_matrix_status(
            slot_type=slot_type,
            is_own_site=bool(slot and slot.get("is_own_site")),
            is_competitor=bool(slot and slot.get("is_competitor")),
            is_third_party=bool(slot and slot.get("is_third_party")),
            has_slot=has_slot,
        )
        cells.append(
            SlotCell(
                keyword=keyword,
                slot_type=slot_type,
                matrix_status=matrix_status,
                owner_url=slot.get("url") if slot else None,
                owner_domain=slot.get("owner_domain") if slot else None,
                title=slot.get("title") if slot else None,
                snapshot_id=snapshot_id,
            )
        )
    return cells
