"""Classify run status from check severities."""

from __future__ import annotations

from exposureflow_api.ops_maintenance.checks import OpsCheckResult

_SEVERITY_RANK = {"pass": 0, "warn": 1, "critical": 2}


def aggregate_run_status(signals: list[OpsCheckResult]) -> str:
    worst = max((_SEVERITY_RANK.get(s.severity, 0) for s in signals), default=0)
    if worst >= 2:
        return "critical"
    if worst >= 1:
        return "warn"
    return "pass"


def non_pass_signals(signals: list[OpsCheckResult]) -> list[OpsCheckResult]:
    return [s for s in signals if s.severity != "pass"]
