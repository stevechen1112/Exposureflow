"""Pydantic schemas for execution plane API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ExecutionJobResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    site_id: UUID
    decision_id: UUID | None
    opportunity_id: UUID | None
    job_type: str
    executor_type: str
    status: str
    input_json: dict
    output_json: dict
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExecutionJobCreate(BaseModel):
    site_id: UUID
    job_type: str
    decision_id: UUID | None = None
    opportunity_id: UUID | None = None
    executor_type: str = "content_engine"
    input_json: dict = Field(default_factory=dict)
