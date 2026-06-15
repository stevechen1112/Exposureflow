"""Pydantic schemas for strategy layer API."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class BusinessIntakeCreate(BaseModel):
    site_id: UUID
    company_summary: str | None = None
    market_notes: str | None = None
    customer_segments_json: list = Field(default_factory=list)
    domestic_markets_json: list = Field(default_factory=list)
    export_markets_json: list = Field(default_factory=list)
    sales_regions_json: list = Field(default_factory=list)
    strategic_goals_json: list = Field(default_factory=list)
    constraints_json: list = Field(default_factory=list)
    change_summary: str | None = None


class BusinessIntakeUpdate(BaseModel):
    company_summary: str | None = None
    market_notes: str | None = None
    customer_segments_json: list | None = None
    domestic_markets_json: list | None = None
    export_markets_json: list | None = None
    sales_regions_json: list | None = None
    strategic_goals_json: list | None = None
    constraints_json: list | None = None
    change_summary: str | None = None


class BusinessIntakeResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    site_id: UUID
    status: str
    version_number: int
    parent_intake_id: UUID | None
    is_current: bool
    archived_at: datetime | None
    change_summary: str | None
    company_summary: str | None
    market_notes: str | None
    customer_segments_json: list
    domestic_markets_json: list
    export_markets_json: list
    sales_regions_json: list
    strategic_goals_json: list
    constraints_json: list
    approved_by: UUID | None
    approved_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StrategyImpactPreviewResponse(BaseModel):
    keywords_to_add: list[dict]
    keywords_to_block: list[dict]
    constraint_rules_to_upsert: list[dict] = Field(default_factory=list)
    scopes_to_upsert: list[dict]
    opportunities_affected: int
    opportunity_samples: list[dict]
    changes_summary: dict


class StrategyImpactApplyResponse(BaseModel):
    scope_id: str | None
    keywords_created: int
    keywords_updated: int
    constraint_rules_synced: int = 0
    opportunities_rescored: int


class BusinessIntakeApproveResponse(BaseModel):
    intake: BusinessIntakeResponse
    impact: StrategyImpactApplyResponse


class ProductServiceScopeCreate(BaseModel):
    site_id: UUID
    name: str
    scope_type: str
    description: str | None = None
    target_markets_json: list = Field(default_factory=list)
    target_personas_json: list = Field(default_factory=list)
    priority: int = 3
    status: str = "active"
    source: str = "consultant"


class ProductServiceScopeUpdate(BaseModel):
    name: str | None = None
    scope_type: str | None = None
    description: str | None = None
    target_markets_json: list | None = None
    target_personas_json: list | None = None
    priority: int | None = None
    status: str | None = None


class ProductServiceScopeResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    site_id: UUID
    name: str
    scope_type: str
    description: str | None
    target_markets_json: list
    target_personas_json: list
    priority: int
    status: str
    source: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class KeywordPyramidNodeCreate(BaseModel):
    site_id: UUID
    keyword: str
    node_type: str
    parent_id: UUID | None = None
    product_service_scope_id: UUID | None = None
    intent: str | None = None
    target_market: str | None = None
    language: str | None = None
    keyword_level: str | None = None
    funnel_stage: str | None = None
    is_target: bool = False
    business_fit_status: str = "in_scope"
    priority: int = 3
    created_by: str = "consultant"
    evidence_json: dict = Field(default_factory=dict)


class KeywordPyramidNodeUpdate(BaseModel):
    keyword: str | None = None
    node_type: str | None = None
    parent_id: UUID | None = None
    product_service_scope_id: UUID | None = None
    intent: str | None = None
    target_market: str | None = None
    language: str | None = None
    keyword_level: str | None = None
    funnel_stage: str | None = None
    is_target: bool | None = None
    business_fit_status: str | None = None
    priority: int | None = None
    evidence_json: dict | None = None


class KeywordPyramidNodeResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    site_id: UUID
    parent_id: UUID | None
    product_service_scope_id: UUID | None
    topic_node_id: UUID | None = None
    topic_cluster_id: UUID | None = None
    keyword: str
    node_type: str
    intent: str | None
    target_market: str | None
    language: str | None
    keyword_level: str | None = None
    funnel_stage: str | None = None
    is_target: bool = False
    business_fit_status: str
    priority: int
    created_by: str
    approved_by: UUID | None
    approved_at: datetime | None
    evidence_json: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DeliveryCommitmentCreate(BaseModel):
    site_id: UUID
    period: str = "monthly"
    new_content_target: int = 0
    refresh_target: int = 0
    faq_schema_target: int = 0
    technical_fix_target: int = 0
    report_target: int = 1
    effective_from: date
    effective_to: date | None = None
    notes: str | None = None


class DeliveryCommitmentUpdate(BaseModel):
    period: str | None = None
    new_content_target: int | None = None
    refresh_target: int | None = None
    faq_schema_target: int | None = None
    technical_fix_target: int | None = None
    report_target: int | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    notes: str | None = None


class DeliveryCommitmentResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    site_id: UUID
    period: str
    new_content_target: int
    refresh_target: int
    faq_schema_target: int
    technical_fix_target: int
    report_target: int
    effective_from: date
    effective_to: date | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BusinessFitEvaluateRequest(BaseModel):
    site_id: UUID
    keyword: str


class BusinessFitEvaluateResponse(BaseModel):
    business_fit_score: float
    business_fit_status: str
    blocked: bool
    keyword_pyramid_node_id: UUID | None
    product_service_scope_id: UUID | None
    evidence: dict


class BusinessConstraintRuleResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    site_id: UUID
    source_intake_id: UUID | None
    source_intake_version: int | None
    description: str
    rule_type: str
    match_pattern: str
    action: str
    is_active: bool
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ColdStartResearchRequest(BaseModel):
    site_id: UUID
    market: str | None = None
    language: str | None = None
    seed_keywords: list[str] = Field(default_factory=list)
    include_paa: bool = True
    include_related: bool = True
    max_expansions: int = Field(default=12, ge=1, le=30)
    max_seeds: int = Field(default=5, ge=1, le=10)


class KeywordPyramidBulkImportRow(BaseModel):
    keyword: str
    node_type: str = "pillar"
    parent_keyword: str | None = None
    intent: str | None = None
    target_market: str | None = None
    language: str | None = None
    keyword_level: str | None = None
    funnel_stage: str | None = None
    is_target: bool = False
    business_fit_status: str = "needs_review"
    priority: int = 3
    product_service_scope_id: UUID | None = None


class KeywordPyramidBulkImportRequest(BaseModel):
    site_id: UUID
    rows: list[KeywordPyramidBulkImportRow] = Field(default_factory=list)
    created_by: str = "consultant"


class KeywordPyramidBulkImportResponse(BaseModel):
    created: int
    skipped: int
    errors: list[str] = Field(default_factory=list)


class PyramidTopicBridgeResponse(BaseModel):
    linked: int
    skipped: int
