"""GA4 Data API client for page-level metrics (auxiliary data)."""

from __future__ import annotations

import json
from datetime import date
from typing import Any, Protocol

import httpx

from connectors.types import Ga4PageMetric

GA4_API = "https://analyticsdata.googleapis.com/v1beta"


class Ga4TokenProvider(Protocol):
    def get_access_token(self) -> str: ...


class Ga4ServiceAccountTokenProvider:
    def __init__(self, credentials_json: str) -> None:
        self._credentials_json = credentials_json
        self._token: str | None = None

    def get_access_token(self) -> str:
        if self._token:
            return self._token
        from google.auth.transport.requests import Request
        from google.oauth2 import service_account

        info = json.loads(self._credentials_json)
        creds = service_account.Credentials.from_service_account_info(
            info,
            scopes=["https://www.googleapis.com/auth/analytics.readonly"],
        )
        creds.refresh(Request())
        self._token = creds.token
        if not self._token:
            raise RuntimeError("Failed to obtain GA4 access token")
        return self._token


class GA4Client:
    def __init__(
        self,
        property_id: str,
        token_provider: Ga4TokenProvider,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.property_id = property_id
        self._token_provider = token_provider
        self._http = http_client or httpx.Client(timeout=60.0)

    def fetch_page_metrics(self, start_date: date, end_date: date) -> list[Ga4PageMetric]:
        url = f"{GA4_API}/properties/{self.property_id}:runReport"
        payload: dict[str, Any] = {
            "dateRanges": [{"startDate": start_date.isoformat(), "endDate": end_date.isoformat()}],
            "dimensions": [{"name": "date"}, {"name": "pagePath"}],
            "metrics": [
                {"name": "sessions"},
                {"name": "engagedSessions"},
                {"name": "engagementRate"},
                {"name": "conversions"},
            ],
            "limit": 100000,
        }
        response = self._http.post(
            url,
            headers={"Authorization": f"Bearer {self._token_provider.get_access_token()}"},
            json=payload,
        )
        response.raise_for_status()
        body = response.json()
        metrics: list[Ga4PageMetric] = []
        for row in body.get("rows", []):
            dims = [d.get("value", "") for d in row.get("dimensionValues", [])]
            vals = [v.get("value", "0") for v in row.get("metricValues", [])]
            metrics.append(
                Ga4PageMetric(
                    date=date.fromisoformat(dims[0]),
                    page_path=dims[1],
                    sessions=int(float(vals[0])),
                    engaged_sessions=int(float(vals[1])),
                    engagement_rate=float(vals[2]),
                    conversions=float(vals[3]),
                )
            )
        return metrics
