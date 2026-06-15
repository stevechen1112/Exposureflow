from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class GscRowResponse(BaseModel):
    date: date
    query: str
    page: str
    country: str | None
    device: str | None
    impressions: int
    clicks: int
    ctr: float
    position: float

    model_config = {"from_attributes": True}


class GscQueryParams(BaseModel):
    site_id: UUID
    query: str | None = None
    page: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    limit: int = Field(default=100, le=1000)


class Ga4PageMetricResponse(BaseModel):
    date: date
    page_path: str
    sessions: int
    engaged_sessions: int
    engagement_rate: float
    conversions: float
    auxiliary: bool = True

    model_config = {"from_attributes": True}


class SerpSnapshotRequest(BaseModel):
    site_id: UUID
    keyword: str = Field(min_length=1)
    country: str = "tw"
    language: str = "zh-TW"
    device: str = "desktop"


class SerpSlotResponse(BaseModel):
    id: UUID
    slot_type: str
    position: int | None
    owner_domain: str | None
    url: str | None
    title: str | None
    is_own_site: bool
    is_competitor: bool
    is_third_party: bool

    model_config = {"from_attributes": True}


class SerpSnapshotResponse(BaseModel):
    id: UUID
    keyword: str
    country: str
    language: str
    device: str
    raw_provider: str
    slots: list[SerpSlotResponse]


class TechnicalIssueResponse(BaseModel):
    id: UUID
    site_id: UUID
    url: str | None
    issue_type: str
    severity: str
    status: str
    description: str
    recommended_action: str | None

    model_config = {"from_attributes": True}


class SyncTriggerRequest(BaseModel):
    site_id: UUID
    input_json: dict = Field(default_factory=dict)


class SyncStateResponse(BaseModel):
    provider: str
    site_id: UUID
    last_synced_at: str | None
    last_success_at: str | None
    last_error: str | None
    cursor_json: dict

    model_config = {"from_attributes": True}


class GscTopQuerySummary(BaseModel):
    query: str
    impressions: int
    clicks: int
    position: float


class GscDataSummaryResponse(BaseModel):
    total_rows: int
    distinct_queries: int
    distinct_pages: int
    earliest_date: date | None
    latest_date: date | None
    top_queries: list[GscTopQuerySummary]
