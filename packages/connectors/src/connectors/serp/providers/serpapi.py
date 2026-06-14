"""SerpAPI SERP provider."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx

SERPAPI_URL = "https://serpapi.com/search.json"


class SerpApiProvider:
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
        params = {
            "engine": "google",
            "q": keyword,
            "gl": country.lower(),
            "hl": language.split("-")[0],
            "device": "mobile" if device == "mobile" else "desktop",
            "api_key": self._api_key,
        }
        response = self._http.get(SERPAPI_URL, params=params)
        response.raise_for_status()
        body = response.json()
        body["_provider"] = "serpapi"
        body["_captured_at"] = datetime.now(UTC).isoformat()
        return body
