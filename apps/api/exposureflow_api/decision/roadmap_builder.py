"""Schedule approved decisions into 4/8/16-week roadmaps."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class RoadmapPlanItem:
    decision_id: str
    candidate_id: str
    action_type: str
    title: str
    week_number: int
    due_date: date | None
    risk_level: str
    expected_exposure_impact: float
    dependency_item_ids: list[str]
    sort_order: int


def _week_for_item(
    *,
    index: int,
    risk_level: str,
    action_type: str,
    horizon_weeks: int,
) -> int:
    if risk_level == "high" or action_type in {"technical_fix", "entity_fix", "fix_indexability"}:
        return min(2, 1 + (index % 2))
    if risk_level == "medium":
        mid = max(2, horizon_weeks // 2)
        return min(mid, 2 + (index % 3))
    tail_start = max(3, horizon_weeks - 2)
    return min(horizon_weeks, tail_start + (index % 3))


def _title_for_action(action_type: str, payload: dict) -> str:
    keyword = payload.get("keyword") or ""
    label = action_type.replace("_", " ").title()
    if keyword:
        return f"{label}: {keyword}"
    return label


def build_roadmap_items(
    *,
    approved_rows: list[tuple],
    horizon_weeks: int,
    start_date: date | None = None,
) -> list[RoadmapPlanItem]:
    """approved_rows: (decision, candidate) tuples sorted by rank."""
    if horizon_weeks not in {4, 8, 16}:
        raise ValueError("horizon_weeks must be 4, 8, or 16")
    base = start_date or date.today()
    items: list[RoadmapPlanItem] = []
    url_to_item_id: dict[str, str] = {}

    for index, (decision, candidate) in enumerate(approved_rows):
        week = _week_for_item(
            index=index,
            risk_level=candidate.risk_level,
            action_type=candidate.action_type,
            horizon_weeks=horizon_weeks,
        )
        payload = candidate.action_payload_json or {}
        title = _title_for_action(candidate.action_type, payload)
        due = base + timedelta(weeks=week)
        dependency_ids: list[str] = []
        current_url = payload.get("current_url")
        if current_url and current_url in url_to_item_id:
            if candidate.action_type == "refresh_page":
                dependency_ids.append(url_to_item_id[current_url])

        item = RoadmapPlanItem(
            decision_id=str(decision.id),
            candidate_id=str(candidate.id),
            action_type=candidate.action_type,
            title=title,
            week_number=week,
            due_date=due,
            risk_level=candidate.risk_level,
            expected_exposure_impact=float(candidate.expected_exposure_impact or 0),
            dependency_item_ids=dependency_ids,
            sort_order=index,
        )
        items.append(item)
        if candidate.action_type == "technical_fix" and current_url:
            url_to_item_id[current_url] = str(decision.id)

    return items
