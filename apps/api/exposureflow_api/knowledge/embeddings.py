"""Deterministic local text embeddings (v1 — no external API required)."""

from __future__ import annotations

import hashlib
import math
import struct


def embed_text(text: str, *, dimensions: int = 384) -> list[float]:
    """Produce a normalized deterministic vector from text."""
    if not text:
        return [0.0] * dimensions
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values: list[float] = []
    while len(values) < dimensions:
        for i in range(0, len(digest) - 3, 4):
            chunk = digest[i : i + 4]
            values.append(struct.unpack("!I", chunk)[0] / 2**32)
            if len(values) >= dimensions:
                break
        digest = hashlib.sha256(digest).digest()
    norm = math.sqrt(sum(v * v for v in values)) or 1.0
    return [round(v / norm, 8) for v in values]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)
