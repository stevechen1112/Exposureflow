"""Pydantic schemas for security API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SecuritySettingsResponse(BaseModel):
    workspace_id: UUID
    require_2fa: bool
    sso_enabled: bool
    saml_entity_id: str | None
    saml_sso_url: str | None
    ip_allowlist: list[str]
    retention_days: int
    deletion_status: str

    model_config = {"from_attributes": True}


class SecuritySettingsUpdate(BaseModel):
    require_2fa: bool | None = None
    ip_allowlist: list[str] | None = None
    retention_days: int | None = Field(default=None, ge=30, le=3650)


class SsoConfigUpdate(BaseModel):
    sso_enabled: bool
    saml_entity_id: str | None = None
    saml_sso_url: str | None = None
    saml_certificate: str | None = None


class SsoLoginRequest(BaseModel):
    email: str


class DataExportResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    status: str
    export_json: dict | None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class SecurityEventResponse(BaseModel):
    id: UUID
    event_type: str
    severity: str
    actor_user_id: UUID | None
    ip_address: str | None
    metadata_json: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogResponse(BaseModel):
    id: UUID
    action: str
    target_type: str
    target_id: str | None
    actor_user_id: UUID | None
    metadata_json: dict
    created_at: datetime

    model_config = {"from_attributes": True}
