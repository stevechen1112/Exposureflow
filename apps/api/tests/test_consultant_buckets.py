"""Consultant inbox bucketing and action hint tests."""

from exposureflow_api.consultant import action_hints
from exposureflow_api.consultant.schemas import ConsultantInboxItem
from exposureflow_api.consultant.service import _bucket_item


def _item(**kwargs: object) -> ConsultantInboxItem:
    base = {
        "id": "x-1",
        "category": "strategy",
        "priority": "medium",
        "title": "t",
        "detail": "d",
        "site_id": "s",
        "site_name": "Site",
        "site_domain": "example.com",
        "action_path": "/app/w/sites/s/dashboard",
        "source_type": "test",
        "source_id": "1",
    }
    base.update(kwargs)
    return ConsultantInboxItem(**base)


def test_urgent_technical_high() -> None:
    item = _item(category="technical", priority="high")
    assert _bucket_item(item) == "urgent"


def test_strategy_goes_to_monitoring() -> None:
    item = _item(category="strategy", priority="medium")
    assert _bucket_item(item) == "monitoring"


def test_opportunity_goes_to_monitoring() -> None:
    item = _item(category="opportunity", priority="medium")
    assert _bucket_item(item) == "monitoring"


def test_roadmap_active_goes_in_progress() -> None:
    item = _item(category="roadmap", priority="high")
    assert _bucket_item(item) == "in_progress"


def test_roadmap_planned_goes_monitoring() -> None:
    item = _item(category="roadmap", priority="medium")
    assert _bucket_item(item) == "monitoring"


def test_action_hints_non_empty() -> None:
    assert "技術問題" in action_hints.hint_for_technical("other", None, None)
    assert "內容審核" in action_hints.hint_for_content("needs_review")
    assert "關鍵字金字塔" in action_hints.hint_for_keyword_pyramid("kw", "pillar")
    assert "曝光地圖" in action_hints.hint_for_topic_gap("kw", 100)
    assert "整合設定" in action_hints.hint_for_sync("gsc")
