"""Bing Webmaster Tools query stats client."""

from __future__ import annotations

from datetime import date
from typing import Protocol

import httpx

from connectors.types import BingPerformanceRow

BING_API = "https://ssl.bing.com/webmaster/api.svc/json"


class BingTokenProvider(Protocol):
    def get_access_token(self) -> str: ...


class BingApiKeyProvider:
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def get_access_token(self) -> str:
        return self._api_key


class BingWebmasterClient:
    def __init__(
        self,
        site_url: str,
        token_provider: BingTokenProvider,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.site_url = site_url
        self._token_provider = token_provider
        self._http = http_client or httpx.Client(timeout=60.0)

    def fetch_query_stats(self, start_date: date, end_date: date) -> list[BingPerformanceRow]:
        url = f"{BING_API}/GetQueryStats"
        params = {
            "siteUrl": self.site_url,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "apikey": self._token_provider.get_access_token(),
        }
        response = self._http.get(url, params=params)
        response.raise_for_status()
        body = response.json()
        rows: list[BingPerformanceRow] = []
        for item in body.get("d", []):
            rows.append(
                BingPerformanceRow(
                    date=date.fromisoformat(item.get("Date", start_date.isoformat())[:10]),
                    query=item.get("Query", ""),
                    page=item.get("Url", ""),
                    country=item.get("Country"),
                    device=item.get("Device"),
                    impressions=int(item.get("Impressions", 0)),
                    clicks=int(item.get("Clicks", 0)),
                    ctr=float(item.get("Ctr", 0.0)),
                    position=float(item.get("AvgImpressionPosition", 0.0)),
                )
            )
        return rows
