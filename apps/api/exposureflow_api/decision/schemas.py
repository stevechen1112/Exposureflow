"""Pydantic schemas for decision plane API."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ActionCandidateResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    site_id: UUID
    opportunity_id: UUID
    action_type: str
    target_asset_id: UUID | None
    action_payload_json: dict
    expected_exposure_impact: float
    risk_level: str
    required_inputs_json: list
    evidence_json: dict
    created_by: str
    decision_status: str
    rank_score: float
    created_at: datetime

    model_config = {"from_attributes": True}


class ActionDecisionResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    candidate_id: UUID
    decision: str
    selected_by: UUID | None
    rationale: str
    confidence: float | None
    scheduled_for: date | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DecisionRequest(BaseModel):
    rationale: str | None = None
    scheduled_for: date | None = None
    confidence: float | None = None


class RoadmapBuildRequest(BaseModel):
    site_id: UUID
    horizon_weeks: int = Field(default=8, description="4, 8, or 16")
    title: str | None = None


class RoadmapItemResponse(BaseModel):
    id: UUID
    roadmap_id: UUID
    decision_id: UUID
    candidate_id: UUID
    action_type: str
    title: str
    week_number: int
    due_date: date | None
    owner_user_id: UUID | None
    status: str
    client_approval_status: str
    risk_level: str
    expected_exposure_impact: float
    dependency_item_ids: list
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class RoadmapResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    site_id: UUID
    horizon_weeks: int
    title: str
    status: str
    created_at: datetime
    updated_at: datetime
    items: list[RoadmapItemResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}
