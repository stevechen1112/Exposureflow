"""Tests for article markdown normalization."""

from exposureflow_api.execution.compiler.content_normalizer import (
    extract_excerpt,
    infer_category,
    normalize_article_markdown,
)


SAMPLE = """# 紗窗破了怎麼辦

紗窗是許多家庭中常見的防護設施，主要用來阻擋昆蟲進入室內，同時保持通風。

紗窗是許多家庭中常見的防護設施，主要用來阻擋昆蟲進入室內，同時保持通風。

## 先了解狀況與常見原因

紗窗是許多家庭中常見的防護設施，主要用來阻擋昆蟲進入室內，同時保持通風。

修理紗窗的方法有多種，依據破損的程度和位置，選擇合適的修復方式至關重要。

## 常見問題 FAQ

**Q：紗窗破了怎麼辦是什麼？**

**A：** 請依破損程度決定修補或更換。
"""


def test_normalize_strips_h1_and_dedupes_paragraphs() -> None:
    result = normalize_article_markdown(
        SAMPLE,
        keyword="紗窗破了怎麼辦",
        title="紗窗破了怎麼辦",
    )
    assert "# 紗窗破了怎麼辦" not in result
    assert result.count("紗窗是許多家庭中常見的防護設施") == 1
    assert "## 先了解狀況與常見原因" in result
    assert "什麼是紗窗破了怎麼辦" not in result


def test_normalize_humanizes_faq_question() -> None:
    result = normalize_article_markdown(
        SAMPLE,
        keyword="紗窗破了怎麼辦",
        title="紗窗破了怎麼辦",
    )
    assert "紗窗破了怎麼辦是什麼" not in result
    assert "**Q：" in result


def test_extract_excerpt_uses_keyword_hook() -> None:
    excerpt = extract_excerpt("## 標題\n\n正文", keyword="紗窗破了怎麼辦")
    assert "紗窗破了怎麼辦" in excerpt
    assert "師傅整理" in excerpt


def test_infer_category_for_price_keyword() -> None:
    assert infer_category("換紗窗價格") == "價格說明"
