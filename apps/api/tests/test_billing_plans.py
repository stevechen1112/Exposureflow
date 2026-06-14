"""Plan definition unit tests."""

from exposureflow_api.billing.plans import METRIC_TO_LIMIT_KEY, PLAN_DEFINITIONS


def test_plan_definitions_cover_all_tiers() -> None:
    codes = {p["plan_code"] for p in PLAN_DEFINITIONS}
    assert codes == {"starter", "professional", "agency", "enterprise"}


def test_starter_has_conservative_limits() -> None:
    starter = next(p for p in PLAN_DEFINITIONS if p["plan_code"] == "starter")
    limits = starter["limits_json"]
    assert limits["workspace_limit"] == 1
    assert limits["site_limit"] == 1
    assert limits["white_label_enabled"] is False


def test_agency_enables_white_label() -> None:
    agency = next(p for p in PLAN_DEFINITIONS if p["plan_code"] == "agency")
    assert agency["limits_json"]["white_label_enabled"] is True
    assert agency["limits_json"]["workspace_limit"] >= 10


def test_metric_mapping_keys() -> None:
    assert "serp_snapshots" in METRIC_TO_LIMIT_KEY
    assert METRIC_TO_LIMIT_KEY["serp_snapshots"] == "serp_snapshots_per_month"
