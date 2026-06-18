"""Orchestrator claim gate ordering regression tests."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from exposureflow_api.execution.agents.orchestrator import run_generation_pipeline


@pytest.mark.asyncio
async def test_pipeline_flushes_markdown_before_claim_verify() -> None:
    """Claim verification must read persisted output_markdown, not empty string."""
    workspace_id = uuid4()
    run_id = uuid4()
    site_id = uuid4()
    brief_id = uuid4()
    pack_id = uuid4()

    run = MagicMock()
    run.site_id = site_id
    run.content_brief_id = brief_id
    run.output_markdown = None
    run.generation_mode = "grounded_llm"
    run.provider = "llm"
    run.evidence_map_json = {}
    run.status = "queued"

    brief = MagicMock()
    brief.source_pack_id = pack_id
    brief.brief_type = "article"
    brief.language = "zh-TW"
    brief.forbidden_claims_json = []
    brief.brief_json = {
        "title_hint": "測試關鍵字",
        "search_context": {"node_type": "cluster", "intent": "informational"},
        "review_policy": "editor_review",
    }

    pack = MagicMock()
    pack.source_refs_json = [{"subject": "A", "fact_text": "事實 A"}]

    flush_calls: list[str] = []
    verify_markdown_at_call: list[str | None] = []

    async def fake_flush():
        flush_calls.append("flush")
        run.output_markdown = "# 測試\n\n內容"

    async def fake_verify(db, ws, rid):
        verify_markdown_at_call.append(run.output_markdown)
        gate = MagicMock()
        gate.status = "passed"
        run.status = "claim_verified"
        return gate

    db = AsyncMock()
    db.flush = fake_flush
    db.refresh = AsyncMock()
    db.get = AsyncMock(return_value=None)

    with (
        patch("exposureflow_api.execution.agents.orchestrator.get_generation_run", AsyncMock(return_value=run)),
        patch("exposureflow_api.execution.agents.orchestrator.get_brief", AsyncMock(return_value=brief)),
        patch("exposureflow_api.execution.agents.orchestrator.get_source_pack", AsyncMock(return_value=pack)),
        patch("exposureflow_api.execution.agents.orchestrator._run_research_stage", AsyncMock()),
        patch("exposureflow_api.execution.agents.orchestrator._run_strategy_stage") as mock_strategy,
        patch("exposureflow_api.execution.agents.orchestrator._run_writing_stage") as mock_writing,
        patch("exposureflow_api.execution.agents.orchestrator._run_seo_check_stage", return_value=True),
        patch(
            "exposureflow_api.content.service.verify_generation_run_claims",
            AsyncMock(side_effect=fake_verify),
        ),
    ):
        mock_strategy.side_effect = lambda state: setattr(state, "strategy_report", None)
        mock_writing.side_effect = lambda state, b, p, s: (
            setattr(state, "draft_markdown", "# 測試\n\n內容"),
            setattr(state, "evidence_map", {"sec_0": []}),
            setattr(state, "generation_mode", "grounded_llm"),
            setattr(state, "provider", "llm"),
            setattr(state, "meta_title", "測試"),
            setattr(state, "meta_description", "描述"),
        )

        state = await run_generation_pipeline(
            db,
            workspace_id,
            run_id,
            keyword="測試關鍵字",
        )

    assert "flush" in flush_calls
    assert verify_markdown_at_call == ["# 測試\n\n內容"]
    assert run.status == "claim_verified"
    assert state.pipeline_status == "complete"
