"""Serper.dev SERP provider."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx

SERPER_URL = "https://google.serper.dev/search"


class SerperProvider:
    def __init__(self, api_key: str, http_client: httpx.Client | None = None) -> None:
        self._api_key = api_key
        self._http = http_client or httpx.Client(timeout=30.0)

    def fetch(
        self,
        keyword: str,
        *,
        country: str = "tw",
        language: str = "zh-TW",
        device: str = "desktop",
    ) -> dict[str, Any]:
        payload = {
            "q": keyword,
            "gl": country.lower(),
            "hl": language.split("-")[0],
            "device": "mobile" if device == "mobile" else "desktop",
        }
        response = self._http.post(
            SERPER_URL,
            headers={"X-API-KEY": self._api_key, "Content-Type": "application/json"},
            json=payload,
        )
        response.raise_for_status()
        body = response.json()
        body["_provider"] = "serper"
        body["_captured_at"] = datetime.now(UTC).isoformat()
        return body
