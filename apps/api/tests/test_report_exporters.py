"""Tests for report exporters."""

from exposureflow_api.reporting.exporters import export_docx, export_markdown, export_pdf

SAMPLE = "# Title\n\n## Section\n\n- bullet one\n- bullet two\n"


def test_export_markdown_bytes() -> None:
    data = export_markdown(SAMPLE)
    assert data.decode("utf-8") == SAMPLE


def test_export_pdf_non_empty() -> None:
    data = export_pdf(SAMPLE, title="Test Report")
    assert data.startswith(b"%PDF")


def test_export_docx_non_empty() -> None:
    data = export_docx(SAMPLE, title="Test Report")
    assert data[:2] == b"PK"
