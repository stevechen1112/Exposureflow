"""Tests for delivery report mode mapping."""

from exposureflow_api.reporting.delivery_reports import DELIVERY_BUILDERS, REPORT_TYPE_BY_MODE


def test_delivery_mode_mappings_complete() -> None:
    for mode in ("audit", "roadmap", "monthly_retainer", "execution_tracker"):
        assert mode in DELIVERY_BUILDERS
        assert mode in REPORT_TYPE_BY_MODE


def test_report_type_by_mode_values() -> None:
    assert REPORT_TYPE_BY_MODE["monthly_retainer"] == "monthly_exposure"
    assert REPORT_TYPE_BY_MODE["audit"] == "audit"
    assert REPORT_TYPE_BY_MODE["execution_tracker"] == "client_summary"
