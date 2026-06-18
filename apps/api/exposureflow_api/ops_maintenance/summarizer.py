"""Deterministic + optional LLM ops health summary."""

from __future__ import annotations

import json
import re

from exposureflow_api.llm.client import achat, llm_available
from exposureflow_api.ops_maintenance.checks import OpsCheckResult

_AUTH_BEARER_PATTERN = re.compile(r"(authorization)\s*:\s*bearer\s+\S+", re.I)
_SECRET_PATTERN = re.compile(
    r"(api[_-]?key|secret|token|password|authorization)\s*[:=]\s*\S+",
    re.I,
)
_BEARER_PATTERN = re.compile(r"Bearer\s+\S+", re.I)


def redact_text(text: str) -> str:
    text = _AUTH_BEARER_PATTERN.sub(r"\1: Bearer ***", text)
    text = _SECRET_PATTERN.sub(r"\1=***", text)
    return _BEARER_PATTERN.sub("Bearer ***", text)


def build_deterministic_summary(signals: list[OpsCheckResult]) -> tuple[str, str]:
    actionable = [s for s in signals if s.severity != "pass"]
    critical = [s for s in actionable if s.severity == "critical"]
    warn = [s for s in actionable if s.severity == "warn"]

    if not actionable:
        title = "今日平台正常 — PASS"
        body = "# 今日維護晨報 — PASS\n\n整體平台可用，未偵測到 WARN 或 CRITICAL 項目。"
        return title, body

    if critical:
        title = f"今日平台需立即處理 — CRITICAL（{len(critical)}）"
        status = "CRITICAL"
    else:
        title = f"今日平台大致正常 — WARN（{len(warn)}）"
        status = "WARN"

    lines = [f"# 今日維護晨報 — {status}", ""]
    if critical:
        lines.append("## Critical")
        for i, s in enumerate(critical, 1):
            lines.append(f"{i}. **{s.title}** — {s.message}")
            lines.append(f"   - 建議：{s.recommended_action}")
        lines.append("")
    if warn:
        lines.append("## Warn")
        for i, s in enumerate(warn, 1):
            lines.append(f"{i}. **{s.title}** — {s.message}")
            lines.append(f"   - 建議：{s.recommended_action}")
        lines.append("")
    lines.append("## 今日建議順序")
    for i, s in enumerate(actionable[:5], 1):
        lines.append(f"{i}. {s.title}")
    return title, "\n".join(lines)


async def build_summary(
    signals: list[OpsCheckResult],
    *,
    use_llm: bool = True,
) -> tuple[str, str, str | None, str | None]:
    title, markdown = build_deterministic_summary(signals)
    actionable = [s for s in signals if s.severity != "pass"]
    if not use_llm or not llm_available() or not actionable:
        return title, markdown, None, None

    payload = [
        {
            "check_id": s.check_id,
            "severity": s.severity,
            "category": s.category,
            "title": s.title,
            "message": redact_text(s.message),
            "recommended_action": s.recommended_action,
            "evidence": s.evidence,
        }
        for s in actionable
    ]
    prompt = (
        "你是 ExposureFlow 的 AI 維護工程師。以下是規則系統產生的 production health signals。\n"
        "你只能根據 JSON 內容摘要，不得新增未出現的故障。\n"
        "請輸出繁體中文 Markdown：\n"
        "1. 今日總結（一句話）\n"
        "2. Critical\n3. Warn\n4. 建議處理順序\n"
        "5. 哪些需要工程師，哪些需要顧問\n\n"
        f"Signals JSON:\n{json.dumps(payload, ensure_ascii=False)}"
    )
    try:
        raw = await achat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1200,
        )
        llm_md = redact_text(raw.strip())
        if llm_md:
            return title, llm_md, "openai", "gpt-4o-mini"
    except Exception:  # noqa: BLE001
        pass
    return title, markdown, None, None
