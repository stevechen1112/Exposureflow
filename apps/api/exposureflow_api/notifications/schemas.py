from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    user_id: UUID | None
    notification_type: str
    title: str
    body: str
    severity: str
    status: str
    link_url: str | None
    metadata_json: dict
    email_sent_at: datetime | None
    read_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SupportTicketCreate(BaseModel):
    subject: str
    description: str
    priority: str = "normal"


class SupportTicketResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    created_by_user_id: UUID
    assigned_to_user_id: UUID | None
    subject: str
    description: str
    status: str
    priority: str
    external_ref: str | None
    metadata_json: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StatusIncidentCreate(BaseModel):
    title: str
    summary: str
    status: str = "investigating"
    severity: str = "minor"
    affected_components: list[str] = []
    is_public: bool = False


class StatusIncidentUpdate(BaseModel):
    status: str | None = None
    summary: str | None = None
    severity: str | None = None
    is_public: bool | None = None
    resolved: bool | None = None


class StatusIncidentResponse(BaseModel):
    id: UUID
    title: str
    summary: str
    status: str
    severity: str
    affected_components_json: list
    is_public: bool
    started_at: datetime
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
