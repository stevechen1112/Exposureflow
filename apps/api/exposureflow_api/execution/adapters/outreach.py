"""Outreach manual task adapter — consultant workflow, not auto-publish."""

from __future__ import annotations

from exposureflow_api.execution.adapters.base import AdapterResult


def run_outreach_adapter(input_json: dict) -> AdapterResult:
    keyword = input_json.get("keyword")
    targets = input_json.get("outreach_targets") or input_json.get("third_party_domains") or []
    if not targets and not keyword:
        return AdapterResult(
            success=False,
            output={},
            error_message="outreach_targets or keyword required",
        )

    tasks = []
    for domain in targets or ["research_needed"]:
        tasks.append(
            {
                "task_type": "outreach_manual",
                "target_domain": domain,
                "keyword": keyword,
                "status": "pending_consultant",
                "instructions": "Research contact, draft pitch, obtain client approval before outreach",
            }
        )

    return AdapterResult(
        success=True,
        output={
            "adapter": "outreach",
            "manual_tasks": tasks,
            "requires_human": True,
            "output_markdown": (
                "# Outreach manual tasks\n\n"
                + "\n".join(
                    f"- [{t['target_domain']}] {t['instructions']}" for t in tasks
                )
                + "\n"
            ),
        },
    )
