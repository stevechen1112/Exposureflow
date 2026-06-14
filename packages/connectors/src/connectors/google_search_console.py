"""Google Search Console Search Analytics client."""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any, Protocol
from urllib.parse import quote

import httpx

from connectors.types import GscPerformanceRow

GSC_API_BASE = "https://www.googleapis.com/webmasters/v3"
MAX_MONTHS = 16
GSC_DATA_LAG_DAYS = 3


class TokenProvider(Protocol):
    def get_access_token(self) -> str: ...


class ServiceAccountTokenProvider:
    """Service account credentials JSON with webmasters.readonly scope."""

    def __init__(self, credentials_json: str) -> None:
        self._credentials_json = credentials_json
        self._token: str | None = None

    def get_access_token(self) -> str:
        if self._token:
            return self._token
        try:
            from google.oauth2 import service_account
            from google.auth.transport.requests import Request
        except ImportError as exc:
            raise RuntimeError("google-auth is required for GSC service account auth") from exc

        info = json.loads(self._credentials_json)
        creds = service_account.Credentials.from_service_account_info(
            info,
            scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
        )
        creds.refresh(Request())
        self._token = creds.token
        if not self._token:
            raise RuntimeError("Failed to obtain GSC access token")
        return self._token


class OAuthTokenProvider:
    def __init__(self, access_token: str) -> None:
        self._access_token = access_token

    def get_access_token(self) -> str:
        return self._access_token


class GSCClient:
    def __init__(
        self,
        site_url: str,
        token_provider: TokenProvider,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.site_url = site_url
        self._token_provider = token_provider
        self._http = http_client or httpx.Client(timeout=60.0)

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token_provider.get_access_token()}"}

    def fetch_search_analytics(
        self,
        start_date: date,
        end_date: date,
        *,
        dimensions: list[str] | None = None,
        row_limit: int = 25000,
        start_row: int = 0,
    ) -> list[GscPerformanceRow]:
        dims = dimensions or ["date", "query", "page", "country", "device"]
        encoded_site = quote(self.site_url, safe="")
        url = f"{GSC_API_BASE}/sites/{encoded_site}/searchAnalytics/query"
        payload: dict[str, Any] = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "dimensions": dims,
            "rowLimit": row_limit,
            "startRow": start_row,
            "dataState": "all",
        }
        response = self._http.post(url, headers=self._headers(), json=payload)
        response.raise_for_status()
        body = response.json()
        rows: list[GscPerformanceRow] = []
        for row in body.get("rows", []):
            keys = row.get("keys", [])
            key_map = dict(zip(dims, keys, strict=False))
            row_date = date.fromisoformat(key_map.get("date", start_date.isoformat()))
            rows.append(
                GscPerformanceRow(
                    date=row_date,
                    query=key_map.get("query", ""),
                    page=key_map.get("page", ""),
                    country=key_map.get("country"),
                    device=key_map.get("device"),
                    impressions=int(row.get("impressions", 0)),
                    clicks=int(row.get("clicks", 0)),
                    ctr=float(row.get("ctr", 0.0)),
                    position=float(row.get("position", 0.0)),
                )
            )
        return rows

    def fetch_incremental(
        self,
        last_synced_date: date | None,
        *,
        max_months: int = MAX_MONTHS,
    ) -> list[GscPerformanceRow]:
        end = date.today() - timedelta(days=GSC_DATA_LAG_DAYS)
        if last_synced_date is None:
            start = end - timedelta(days=30 * max_months)
        else:
            start = last_synced_date + timedelta(days=1)
        if start > end:
            return []

        all_rows: list[GscPerformanceRow] = []
        start_row = 0
        while True:
            batch = self.fetch_search_analytics(start, end, start_row=start_row)
            if not batch:
                break
            all_rows.extend(batch)
            if len(batch) < 25000:
                break
            start_row += len(batch)
        return all_rows
