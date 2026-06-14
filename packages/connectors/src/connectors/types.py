from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass
class GscPerformanceRow:
    date: date
    query: str
    page: str
    country: str | None
    device: str | None
    impressions: int
    clicks: int
    ctr: float
    position: float


@dataclass
class Ga4PageMetric:
    date: date
    page_path: str
    sessions: int
    engaged_sessions: int
    engagement_rate: float
    conversions: float


@dataclass
class BingPerformanceRow:
    date: date
    query: str
    page: str
    country: str | None
    device: str | None
    impressions: int
    clicks: int
    ctr: float
    position: float


@dataclass
class SerpSlotData:
    slot_type: str
    position: int | None = None
    owner_domain: str | None = None
    owner_brand: str | None = None
    url: str | None = None
    title: str | None = None
    snippet: str | None = None
    is_own_site: bool = False
    is_competitor: bool = False
    is_third_party: bool = False


@dataclass
class SerpFetchResult:
    keyword: str
    country: str
    language: str
    device: str
    raw_provider: str
    raw_json: dict[str, Any]
    captured_at: datetime
    slots: list[SerpSlotData] = field(default_factory=list)


@dataclass
class TechnicalIssueData:
    url: str | None
    issue_type: str
    severity: str
    description: str
    recommended_action: str | None
    evidence: dict[str, Any] = field(default_factory=dict)
