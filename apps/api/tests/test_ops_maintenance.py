"""Unit tests for ops maintenance checks and summarizer."""

import pytest

from exposureflow_api.ops_maintenance.checks import OpsCheckResult
from exposureflow_api.ops_maintenance.classifier import aggregate_run_status
from exposureflow_api.ops_maintenance.summarizer import build_deterministic_summary, redact_text
from exposureflow_api.ops_maintenance.notifications import dispatch_ops_health_notifications


def test_aggregate_run_status_critical_worst():
    signals = [
        OpsCheckResult("a", "infra", "pass", "ok", "ok", "none"),
        OpsCheckResult("b", "jobs", "warn", "w", "w", "fix"),
        OpsCheckResult("c", "jobs", "critical", "c", "c", "fix"),
    ]
    assert aggregate_run_status(signals) == "critical"


def test_aggregate_run_status_pass_only():
    signals = [
        OpsCheckResult("a", "infra", "pass", "ok", "ok", "none"),
    ]
    assert aggregate_run_status(signals) == "pass"


def test_deterministic_summary_pass():
    signals = [
        OpsCheckResult("infra.api_health", "infra", "pass", "API", "ok", "none"),
    ]
    title, body = build_deterministic_summary(signals)
    assert "PASS" in title
    assert "PASS" in body


def test_deterministic_summary_warn():
    signals = [
        OpsCheckResult("jobs.failed_24h", "jobs", "warn", "failed jobs", "3 failed", "check jobs"),
    ]
    title, body = build_deterministic_summary(signals)
    assert "WARN" in title
    assert "failed jobs" in body


def test_redact_secrets():
    text = "Authorization: Bearer sk-secret-token-12345"
    out = redact_text(text)
    assert "sk-secret" not in out
    assert "***" in out


@pytest.mark.asyncio
async def test_ops_notifications_skip_pass():
    from datetime import UTC, datetime
    from uuid import uuid4

    from exposureflow_api.models.ops_health import OpsHealthRun

    run = OpsHealthRun(id=uuid4(), status="pass", trigger="scheduled", started_at=datetime.now(UTC))
    result = await dispatch_ops_health_notifications(run, [])
    assert result.get("skipped") is True
