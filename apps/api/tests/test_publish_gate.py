"""Unit tests for publish gate."""

from types import SimpleNamespace

from exposureflow_api.execution.publish_gate import evaluate_publish_readiness


def _run(**kwargs):
    defaults = {
        "status": "claim_verified",
        "output_markdown": "# Title\n\nSupported product fact about Pump X100.",
        "review_level": "editor_review",
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _brief():
    return SimpleNamespace(
        brief_type="article",
        forbidden_claims_json=[],
        brief_json={},
        market="TW",
    )


def _pack(coverage=0.8):
    return SimpleNamespace(coverage_score=coverage, market="TW")


def _claim_gate(status="passed"):
    return SimpleNamespace(status=status)


def test_publish_gate_passes_when_all_checks_ok() -> None:
    result = evaluate_publish_readiness(
        run=_run(status="approved"),
        brief=_brief(),
        source_pack=_pack(),
        claim_gate=_claim_gate("passed"),
    )
    assert result.status == "passed"


def test_publish_gate_blocked_without_claim_verification() -> None:
    result = evaluate_publish_readiness(
        run=_run(),
        brief=_brief(),
        source_pack=_pack(),
        claim_gate=None,
    )
    assert result.status == "blocked"


def test_publish_gate_blocked_on_low_coverage() -> None:
    result = evaluate_publish_readiness(
        run=_run(status="approved"),
        brief=_brief(),
        source_pack=_pack(coverage=0.2),
        claim_gate=_claim_gate("passed"),
    )
    assert result.status == "blocked"
