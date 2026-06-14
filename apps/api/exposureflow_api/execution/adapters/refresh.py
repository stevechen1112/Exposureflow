"""Refresh page execution adapter — section-aware update suggestions."""

from __future__ import annotations

from exposureflow_api.execution.adapters.base import AdapterResult


def run_refresh_adapter(input_json: dict) -> AdapterResult:
    target_url = input_json.get("current_url") or input_json.get("target_url")
    keyword = input_json.get("keyword")
    if not target_url:
        return AdapterResult(success=False, output={}, error_message="current_url is required")

    sections = input_json.get("stale_sections") or ["title", "intro", "proof_points", "cta"]
    suggestions = []
    for section in sections:
        suggestions.append(
            {
                "section": section,
                "action": "refresh",
                "rationale": f"Update {section} for query '{keyword}' freshness and snippet alignment"
                if keyword
                else f"Refresh stale {section}",
                "priority": "high" if section in ("title", "intro") else "medium",
            }
        )

    markdown = "\n".join(
        f"- **{s['section']}**: {s['rationale']}" for s in suggestions
    )
    return AdapterResult(
        success=True,
        output={
            "adapter": "refresh",
            "target_url": target_url,
            "keyword": keyword,
            "update_suggestions": suggestions,
            "output_markdown": f"# Refresh plan for {target_url}\n\n{markdown}\n",
        },
    )
