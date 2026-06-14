"""Execution adapter base types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AdapterResult:
    success: bool
    output: dict[str, Any]
    error_message: str | None = None
