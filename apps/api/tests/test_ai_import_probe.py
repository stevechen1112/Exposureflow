from exposureflow_api.ai_visibility.import_probe import parse_csv_import, parse_json_import


def test_parse_json_import() -> None:
    rows = parse_json_import(
        [
            {
                "surface": "perplexity",
                "prompt": "flat shoes",
                "answer_text": "Try https://example.com",
                "cited_urls": ["https://example.com"],
                "mentioned_brands": ["Example"],
                "sentiment": "neutral",
            }
        ]
    )
    assert len(rows) == 1
    assert rows[0]["surface"] == "perplexity"
    assert rows[0]["cited_urls"] == ["https://example.com"]


def test_parse_csv_import() -> None:
    csv_content = (
        "surface,prompt,answer_text,cited_urls,mentioned_brands,competitor_mentions,sentiment,run_at\n"
        "chatgpt_search,shoes,answer here,https://a.com|https://b.com,BrandA,,positive,2026-06-14T10:00:00Z\n"
    )
    rows = parse_csv_import(csv_content)
    assert len(rows) == 1
    assert rows[0]["cited_urls"] == ["https://a.com", "https://b.com"]
