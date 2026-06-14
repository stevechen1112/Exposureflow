from uuid import UUID

from pydantic import BaseModel, Field


class ExposureAssetResponse(BaseModel):
    id: UUID
    site_id: UUID
    asset_type: str
    url: str
    title: str | None
    primary_keyword: str | None
    status: str
    total_impressions: int
    total_clicks: int

    model_config = {"from_attributes": True}


class MergeAssetsRequest(BaseModel):
    canonical_asset_id: UUID
    duplicate_asset_ids: list[UUID] = Field(min_length=1)


class OpportunityResponse(BaseModel):
    id: UUID
    site_id: UUID
    opportunity_type: str
    keyword: str | None
    current_url: str | None
    total_opportunity_score: float
    priority: str
    status: str
    reason: str
    evidence_json: dict

    model_config = {"from_attributes": True}


class TopicClusterPerformanceItem(BaseModel):
    id: str
    name: str
    total_impressions: int
    coverage_score: float
    ai_visibility_score: float
    status: str


class DashboardResponse(BaseModel):
    total_impressions: int
    impressions_delta_pct: float
    query_coverage_count: int
    indexed_asset_count: int
    top_3_count: int
    top_10_count: int
    top_20_count: int
    serp_slot_count: int
    ai_citation_count: int
    open_opportunity_count: int
    critical_blocker_count: int
    topic_cluster_performance: list[TopicClusterPerformanceItem]


class CompetitorCreate(BaseModel):
    name: str
    domain: str
    aliases: list[str] = Field(default_factory=list)
    notes: str | None = None


class CompetitorResponse(BaseModel):
    id: UUID
    site_id: UUID
    name: str
    domain: str
    active: bool

    model_config = {"from_attributes": True}
