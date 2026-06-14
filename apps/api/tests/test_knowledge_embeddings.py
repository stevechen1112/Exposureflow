"""Unit tests for knowledge embeddings."""

import pytest

from exposureflow_api.knowledge.embeddings import cosine_similarity, embed_text


def test_embed_text_deterministic() -> None:
    a = embed_text("industrial pump")
    b = embed_text("industrial pump")
    assert a == b
    assert len(a) == 384


def test_cosine_similarity_identical() -> None:
    v = embed_text("test")
    assert cosine_similarity(v, v) == pytest.approx(1.0)
