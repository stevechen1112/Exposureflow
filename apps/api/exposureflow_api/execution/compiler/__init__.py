"""Grounded content compiler pipeline."""

from __future__ import annotations

__all__ = ["compile_grounded_draft"]


def __getattr__(name: str):
    if name == "compile_grounded_draft":
        from exposureflow_api.execution.compiler.compiler import compile_grounded_draft as fn

        return fn
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

