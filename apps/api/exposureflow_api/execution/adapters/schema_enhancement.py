"""Schema enhancement adapter — FAQ / Article JSON-LD blocks."""

from __future__ import annotations

import json

from exposureflow_api.execution.adapters.base import AdapterResult


def build_faq_schema(entities: list[dict]) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": e.get("question") or e.get("subject", ""),
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": e.get("answer") or e.get("fact_text", ""),
                },
            }
            for e in entities
            if (e.get("question") or e.get("subject")) and (e.get("answer") or e.get("fact_text"))
        ],
    }


def build_article_schema(*, headline: str, description: str, url: str | None = None) -> dict:
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": headline,
        "description": description,
    }
    if url:
        schema["mainEntityOfPage"] = url
    return schema


def run_schema_adapter(input_json: dict) -> AdapterResult:
    schema_type = input_json.get("schema_type", "faq")
    entities = input_json.get("entities") or input_json.get("faq_items") or []
    if schema_type == "faq":
        if not entities:
            return AdapterResult(success=False, output={}, error_message="faq entities required")
        schema = build_faq_schema(entities)
    else:
        headline = input_json.get("headline") or input_json.get("keyword") or "Article"
        description = input_json.get("description") or ""
        schema = build_article_schema(
            headline=headline,
            description=description,
            url=input_json.get("target_url"),
        )

    block = f"<!-- schema:{schema_type} -->\n```json\n{json.dumps(schema, ensure_ascii=False, indent=2)}\n```\n"
    return AdapterResult(
        success=True,
        output={
            "adapter": "schema_enhancement",
            "schema_type": schema_type,
            "schema_json": schema,
            "output_markdown": block,
        },
    )
