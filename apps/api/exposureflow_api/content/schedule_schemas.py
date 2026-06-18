"""Pydantic schemas for content schedule API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ContentScheduleCreate(BaseModel):
    enabled: bool = False
    articles_per_week: int = Field(default=2, ge=1, le=20)
    priority_filter: str = "P1"
    schedule_days_json: list[str] = ["mon", "thu"]
    auto_approve_threshold: int | None = None


class ContentScheduleUpdate(BaseModel):
    enabled: bool | None = None
    articles_per_week: int | None = None
    priority_filter: str | None = None
    schedule_days_json: list[str] | None = None
    auto_approve_threshold: int | None = None


class ContentScheduleResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    site_id: UUID
    enabled: bool
    articles_per_week: int
    priority_filter: str
    schedule_days_json: list
    auto_approve_threshold: int | None
    last_run_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BatchGenerateRequest(BaseModel):
    site_id: UUID
    count: int = Field(default=2, ge=1, le=10)
    priority_filter: str = "P1"


class BatchGenerateResponse(BaseModel):
    triggered: int
    skipped: int
    run_ids: list[UUID]
    message: str
