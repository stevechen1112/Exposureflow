"""Unit tests for grounded content compiler."""

from types import SimpleNamespace

from exposureflow_api.execution.compiler.compiler import compile_grounded_draft


def _brief(**kwargs):
    defaults = {
        "brief_type": "article",
        "market": "TW",
        "language": "zh-TW",
        "brief_json": {"title_hint": "Industrial Pump Guide", "review_policy": "editor_review"},
        "forbidden_claims_json": [],
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _pack(**kwargs):
    defaults = {
        "source_refs_json": [
            {
                "ref_type": "company_owned",
                "subject": "Pump X100",
                "fact_text": "Flow rate 500 L/min with corrosion-resistant coating.",
                "title": "Product sheet",
            }
        ],
        "coverage_score": 0.8,
        "market": "TW",
        "language": "zh-TW",
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_compile_grounded_draft_produces_markdown_and_evidence_map() -> None:
    result = compile_grounded_draft(_brief(), _pack())
    assert "Industrial Pump Guide" in result.markdown
    assert "Pump X100" in result.markdown
    assert result.evidence_map
    assert result.qa_report["claim_count"] >= 0
    assert result.generation_mode == "grounded_template"


def test_compile_faq_includes_schema_marker() -> None:
    pack = _pack(
        source_refs_json=[
            {"subject": "What is Pump X100?", "fact_text": "A high-flow industrial pump."}
        ]
    )
    result = compile_grounded_draft(_brief(brief_type="faq"), pack)
    assert "schema:faq" in result.markdown
