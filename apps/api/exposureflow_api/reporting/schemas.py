"""Pydantic schemas for reporting API."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MonthlyReportCreate(BaseModel):
    site_id: UUID
    period_start: date | None = None
    period_end: date | None = None
    title: str | None = None
    branding_json: dict = Field(default_factory=dict)


class DeliveryReportCreate(BaseModel):
    site_id: UUID
    delivery_mode: str = Field(
        pattern="^(audit|roadmap|monthly_retainer|execution_tracker)$"
    )
    period_start: date | None = None
    period_end: date | None = None
    title: str | None = None
    branding_json: dict = Field(default_factory=dict)


class ReportExportRequest(BaseModel):
    format: str = Field(pattern="^(markdown|pdf|docx)$")


class ReportResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    site_id: UUID | None
    report_type: str
    delivery_mode: str | None
    period_start: date | None
    period_end: date | None
    status: str
    title: str
    content_markdown: str | None
    branding_json: dict
    storage_url: str | None
    created_by: UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ClientApprovalRequest(BaseModel):
    site_id: UUID
    note: str | None = None


class ClientMeetingNoteCreate(BaseModel):
    site_id: UUID
    meeting_date: date
    title: str
    summary: str = ""
    action_items_json: list = Field(default_factory=list)


class ClientMeetingNoteResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    site_id: UUID
    meeting_date: date
    title: str
    summary: str
    action_items_json: list
    created_by: UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DeliveryAnnotationCreate(BaseModel):
    report_id: UUID | None = None
    roadmap_item_id: UUID | None = None
    annotation_type: str = "comment"
    body: str


class DeliveryAnnotationResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    report_id: UUID | None
    roadmap_item_id: UUID | None
    author_user_id: UUID | None
    annotation_type: str
    body: str
    created_at: datetime

    model_config = {"from_attributes": True}
