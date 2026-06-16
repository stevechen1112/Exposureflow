"""Pydantic schemas for knowledge base API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, computed_field, model_validator


class BrandProfileUpdate(BaseModel):
    site_id: UUID | None = None
    canonical_brand_name: str
    brand_voice_json: dict = Field(default_factory=dict)
    positioning_json: dict = Field(default_factory=dict)
    target_markets_json: list = Field(default_factory=list)
    buyer_personas_json: list = Field(default_factory=list)
    compliance_policy_json: dict = Field(default_factory=dict)
    default_review_policy: str = "editor_review"


class BrandProfileResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    site_id: UUID | None
    canonical_brand_name: str
    brand_voice_json: dict
    positioning_json: dict
    target_markets_json: list
    buyer_personas_json: list
    compliance_policy_json: dict
    default_review_policy: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeSourceCreate(BaseModel):
    site_id: UUID | None = None
    source_type: str
    source_uri: str | None = None
    source_url: str | None = None  # frontend alias
    title: str
    market: str | None = None
    language: str | None = None
    content_text: str | None = None  # optional initial fact text
    metadata_json: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def normalize_uri(self):
        if self.source_url and not self.source_uri:
            self.source_uri = self.source_url
        return self


class KnowledgeSourceUpdate(BaseModel):
    title: str | None = None
    source_uri: str | None = None
    market: str | None = None
    language: str | None = None
    status: str | None = None
    metadata_json: dict | None = None


class KnowledgeSourceResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    site_id: UUID | None
    source_type: str
    source_uri: str | None
    title: str
    market: str | None
    language: str | None
    owner_user_id: UUID | None
    status: str
    version: int
    checksum: str | None
    metadata_json: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    # Frontend compatibility aliases
    @computed_field
    @property
    def approval_status(self) -> str:
        return self.status

    @computed_field
    @property
    def source_url(self) -> str | None:
        return self.source_uri

    @computed_field
    @property
    def fact_count(self) -> int:
        # populated by service layer eager loading when needed
        return getattr(self, "_fact_count", 0)


class KnowledgeFactCreate(BaseModel):
    site_id: UUID | None = None
    knowledge_source_id: UUID
    fact_type: str
    subject: str
    fact_text: str
    market: str | None = None
    language: str | None = None
    confidence: float = 1.0
    metadata_json: dict = Field(default_factory=dict)


class KnowledgeFactUpdate(BaseModel):
    fact_type: str | None = None
    subject: str | None = None
    fact_text: str | None = None
    market: str | None = None
    language: str | None = None
    confidence: float | None = None
    status: str | None = None
    metadata_json: dict | None = None


class KnowledgeFactResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    site_id: UUID | None
    knowledge_source_id: UUID
    fact_type: str
    subject: str
    fact_text: str
    market: str | None
    language: str | None
    confidence: float
    status: str
    expires_at: datetime | None
    metadata_json: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
