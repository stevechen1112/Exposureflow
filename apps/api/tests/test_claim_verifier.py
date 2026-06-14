"""Unit tests for claim verification gate."""

from exposureflow_api.execution.claim_verifier import (
    extract_claims,
    verify_claims_against_sources,
)


def test_extract_claims_from_markdown() -> None:
    text = "Our pump delivers 500 L/min flow rate. It is better than competitors."
    claims = extract_claims(text)
    assert len(claims) >= 2
    types = {c[1] for c in claims}
    assert "data" in types or "comparison" in types


def test_verify_supported_claim() -> None:
    refs = [
        {
            "ref_type": "company_owned",
            "fact_text": "Flow rate 500 L/min for Pump X100",
            "subject": "Pump X100",
        }
    ]
    markdown = "Pump X100 delivers industry-leading performance for factories."
    findings = verify_claims_against_sources(markdown, refs)
    supported = [f for f in findings if f.verification_status == "supported"]
    assert supported


def test_verify_forbidden_claim() -> None:
    findings = verify_claims_against_sources(
        "We guarantee 100% market share within one month.",
        [],
        forbidden_claims=["100% market share"],
    )
    assert any(f.verification_status == "forbidden" for f in findings)


def test_verify_unsupported_data_claim() -> None:
    findings = verify_claims_against_sources(
        "Our product improves efficiency by 95% within 30 days.",
        [],
    )
    unsupported = [f for f in findings if f.verification_status == "unsupported"]
    assert unsupported
    assert unsupported[0].severity == "high"
