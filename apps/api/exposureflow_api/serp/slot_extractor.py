"""Re-export slot extractor from connectors package for API layer."""

from connectors.serp.slot_extractor import build_fetch_result, extract_slots

__all__ = ["extract_slots", "build_fetch_result"]
