"""Shared keyword normalization helpers."""

from __future__ import annotations


def normalize_keyword(keyword: str | None) -> str:
    if not keyword:
        return ""
    return " ".join(keyword.strip().lower().split())
