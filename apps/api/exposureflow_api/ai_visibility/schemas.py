"""Pydantic schemas for AI visibility API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AIProbeSetCreate(BaseModel):
    site_id: UUID
    name: str
    prompts_json: list[str] = Field(default_factory=list)
    surfaces_json: list[str] = Field(default_factory=list)
    topic_cluster_id: UUID | None = None
    schedule: str | None = None
    active: bool = True


class AIProbeSetUpdate(BaseModel):
    name: str | None = None
    prompts_json: list[str] | None = None
    surfaces_json: list[str] | None = None
    topic_cluster_id: UUID | None = None
    schedule: str | None = None
    active: bool | None = None


class AIProbeSetResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    site_id: UUID
    topic_cluster_id: UUID | None
    name: str
    prompts_json: list
    surfaces_json: list
    schedule: str | None
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AssistedProbeRunRequest(BaseModel):
    site_id: UUID
    probe_set_id: UUID | None = None
    surface: str
    prompt: str
    answer_text: str
    cited_urls: list[str] = Field(default_factory=list)
    mentioned_brands: list[str] = Field(default_factory=list)
    competitor_mentions: list[str] = Field(default_factory=list)
    sentiment: str | None = None
    run_at: datetime | None = None


class ManualImportRequest(BaseModel):
    site_id: UUID
    probe_set_id: UUID | None = None
    format: str = "json"
    csv_content: str | None = None
    rows: list[dict] | None = None


class AIProbeRunResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    site_id: UUID
    probe_set_id: UUID | None
    probe_mode: str
    provider: str | None
    model: str | None
    surface: str
    prompt: str
    answer_text: str
    cited_urls_json: list
    mentioned_brands_json: list
    sentiment: str | None
    our_brand_mentioned: bool
    our_url_cited: bool
    external_url_cited: bool
    competitor_mentions_json: list
    run_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class AICitationResponse(BaseModel):
    id: UUID
    site_id: UUID
    ai_probe_run_id: UUID | None
    surface: str
    prompt: str
    cited_url: str
    cited_domain: str | None
    cited_title: str | None
    citation_context: str | None
    is_own_site: bool
    is_third_party_about_brand: bool
    is_competitor: bool
    captured_at: datetime

    model_config = {"from_attributes": True}


class BrandEntityCreate(BaseModel):
    site_id: UUID
    canonical_name: str
    aliases_json: list[str] = Field(default_factory=list)
    description: str | None = None
    official_profiles_json: list[dict] = Field(default_factory=list)


class BrandEntityUpdate(BaseModel):
    canonical_name: str | None = None
    aliases_json: list[str] | None = None
    description: str | None = None
    official_profiles_json: list[dict] | None = None


class BrandEntityResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    site_id: UUID
    canonical_name: str
    aliases_json: list
    description: str | None
    official_profiles_json: list
    entity_consistency_score: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EntityCheckResponse(BaseModel):
    consistency_score: float
    inconsistencies: list[dict]
    recommended_actions: list[str]


class SerpoRecordCreate(BaseModel):
    site_id: UUID
    brand_query: str
    keyword: str | None = None
    surface: str = "google"


class SerpoRecordResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    site_id: UUID
    brand_query: str
    keyword: str | None
    surface: str
    first_page_positive_count: int
    first_page_neutral_count: int
    first_page_negative_count: int
    first_page_wrong_info_count: int
    recommended_actions_json: list
    captured_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class VisibilityScoreResponse(BaseModel):
    visibility_score: float
    total_runs: int
    our_brand_mention_rate: float
    our_url_citation_rate: float
    competitor_mention_rate: float
