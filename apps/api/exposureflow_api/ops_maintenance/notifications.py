"""Ops health WARN/CRITICAL notifications — email log + optional Slack webhook."""

from __future__ import annotations

import logging

import httpx

from exposureflow_api.config import settings
from exposureflow_api.models.ops_health import OpsHealthRun
from exposureflow_api.ops_maintenance.checks import OpsCheckResult
from exposureflow_api.ops_maintenance.summarizer import redact_text

logger = logging.getLogger(__name__)


def _actionable(signals: list[OpsCheckResult]) -> list[OpsCheckResult]:
    return [s for s in signals if s.severity in {"warn", "critical"}]


def _build_digest(run: OpsHealthRun, signals: list[OpsCheckResult]) -> tuple[str, str]:
    actionable = _actionable(signals)
    status = run.status.upper()
    title = run.summary_title or f"ExposureFlow Ops — {status}"
    lines = [
        f"[ExposureFlow Ops] {status}",
        "",
        f"狀態：{status}",
        f"觸發：{run.trigger}",
        "",
    ]
    for idx, sig in enumerate(actionable[:10], start=1):
        lines.append(f"{idx}. [{sig.severity.upper()}] {sig.title} — {sig.message}")
        if sig.recommended_action:
            lines.append(f"   建議：{sig.recommended_action}")
    if len(actionable) > 10:
        lines.append(f"... 另有 {len(actionable) - 10} 項")
    lines.extend(
        [
            "",
            f"詳情：{settings.app_base_url.rstrip('/')}/internal-admin/ops-maintenance",
        ]
    )
    body = redact_text("\n".join(lines))
    return title, body


async def dispatch_ops_health_notifications(
    run: OpsHealthRun,
    signals: list[OpsCheckResult],
) -> dict[str, str | bool]:
    """Send digest for WARN/CRITICAL runs. PASS is DB-only."""
    if run.status == "pass":
        return {"skipped": True, "reason": "pass"}

    title, body = _build_digest(run, signals)
    channels: dict[str, str | bool] = {}

    if settings.notification_email_enabled and settings.ops_notification_email_to:
        logger.info(
            "ops_health_email",
            extra={
                "run_id": str(run.id),
                "status": run.status,
                "to": settings.ops_notification_email_to,
                "title": title,
                "body_preview": body[:500],
            },
        )
        channels["email"] = "logged"
    else:
        channels["email"] = "skipped"

    webhook = settings.ops_slack_webhook_url
    if webhook:
        prefix = ":rotating_light:" if run.status == "critical" else ":warning:"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    webhook,
                    json={"text": f"{prefix} {title}\n\n{body}"},
                )
                resp.raise_for_status()
            channels["slack"] = "sent"
        except Exception as exc:  # noqa: BLE001
            logger.exception("ops_health_slack_failed", extra={"run_id": str(run.id)})
            channels["slack"] = f"failed:{exc.__class__.__name__}"
    else:
        channels["slack"] = "skipped"

    return channels
