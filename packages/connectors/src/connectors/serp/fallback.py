"""SERP provider with Serper primary and SerpAPI fallback."""

from __future__ import annotations

from typing import Any

from connectors.serp.providers.serpapi import SerpApiProvider
from connectors.serp.providers.serper import SerperProvider


class SerpFallbackClient:
    def __init__(
        self,
        serper_api_key: str | None = None,
        serpapi_api_key: str | None = None,
        serper: SerperProvider | None = None,
        serpapi: SerpApiProvider | None = None,
    ) -> None:
        self._serper = serper or (SerperProvider(serper_api_key) if serper_api_key else None)
        self._serpapi = serpapi or (SerpApiProvider(serpapi_api_key) if serpapi_api_key else None)

    def fetch(
        self,
        keyword: str,
        *,
        country: str = "tw",
        language: str = "zh-TW",
        device: str = "desktop",
    ) -> dict[str, Any]:
        errors: list[str] = []
        if self._serper is not None:
            try:
                return self._serper.fetch(keyword, country=country, language=language, device=device)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"serper: {exc}")
        if self._serpapi is not None:
            try:
                return self._serpapi.fetch(keyword, country=country, language=language, device=device)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"serpapi: {exc}")
        raise RuntimeError("All SERP providers failed: " + "; ".join(errors))
