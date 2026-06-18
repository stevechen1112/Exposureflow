"""Content generation execution adapter — delegates to generation run pipeline."""

from __future__ import annotations

from exposureflow_api.execution.adapters.base import AdapterResult


def run_content_generation_adapter(input_json: dict) -> AdapterResult:
    brief_id = input_json.get("brief_id")
    generation_run_id = input_json.get("generation_run_id")
    if not brief_id and not generation_run_id:
        return AdapterResult(
            success=False,
            output={},
            error_message="brief_id or generation_run_id is required",
        )
    return AdapterResult(
        success=True,
        output={
            "adapter": "content_generation",
            "brief_id": brief_id,
            "generation_run_id": generation_run_id,
            "status": "handled_by_generation_run_api",
            "note": "Draft compilation runs via ContentGenerationRun pipeline.",
        },
    )
