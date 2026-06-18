"""Pydantic schemas for content execution API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SourcePackBuildRequest(BaseModel):
    site_id: UUID
    opportunity_id: UUID | None = None
    execution_job_id: UUID | None = None
    market: str | None = None
    language: str | None = None
    brief_type: str | None = None


class SourcePackResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    site_id: UUID
    opportunity_id: UUID | None
    execution_job_id: UUID | None
    market: str | None
    language: str | None
    required_coverage_json: dict
    source_refs_json: list
    coverage_score: float
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BriefBuildRequest(BaseModel):
    site_id: UUID
    opportunity_id: UUID
    source_pack_id: UUID
    decision_id: UUID | None = None


class ContentBriefResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    site_id: UUID
    opportunity_id: UUID
    decision_id: UUID | None
    source_pack_id: UUID | None
    brief_type: str
    market: str | None
    language: str | None
    target_persona: str | None
    buyer_stage: str | None
    required_evidence_slots_json: list
    forbidden_claims_json: list
    brief_json: dict
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GenerationRunCreate(BaseModel):
    site_id: UUID
    execution_job_id: UUID
    content_brief_id: UUID
    generation_mode: str = "grounded_llm"
    review_level: str = "editor_review"
    auto_compile: bool = False


class ReviewActionRequest(BaseModel):
    rationale: str | None = None
    override: bool = False


class RequestChangesRequest(BaseModel):
    notes: str


class PublishGenerationRunRequest(BaseModel):
    site_status: str = "draft"


class GenerationRunResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    site_id: UUID
    execution_job_id: UUID
    content_brief_id: UUID
    generation_mode: str
    review_level: str
    provider: str | None
    model: str | None
    input_hash: str
    output_markdown: str | None
    evidence_map_json: dict
    unsupported_claims_json: list
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GateResultResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    site_id: UUID
    execution_job_id: UUID
    content_generation_run_id: UUID | None
    gate_type: str
    status: str
    findings_json: list
    checked_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class ContentClaimResponse(BaseModel):
    id: UUID
    claim_text: str
    claim_type: str
    verification_status: str
    severity: str
    source_refs_json: list
    finding_json: dict

    model_config = {"from_attributes": True}
