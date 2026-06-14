from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    name: str
    status: str
    last_login_at: datetime | None

    model_config = {"from_attributes": True}


class MeResponse(BaseModel):
    user: UserResponse
    workspaces: list["WorkspaceSummary"]


class WorkspaceSummary(BaseModel):
    id: UUID
    name: str
    workspace_type: str
    role: str
    status: str

    model_config = {"from_attributes": True}


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    workspace_type: str = Field(pattern="^(agency_internal|client|enterprise)$")
    client_name: str | None = None
    default_locale: str = "zh-TW"


class WorkspaceResponse(BaseModel):
    id: UUID
    account_id: UUID
    organization_id: UUID
    name: str
    workspace_type: str
    client_name: str | None
    status: str
    default_locale: str
    feature_flags: dict
    plan_limits: dict
    usage_limits: dict

    model_config = {"from_attributes": True}


class SiteCreate(BaseModel):
    domain: str = Field(min_length=3, max_length=255)
    site_name: str = Field(min_length=1, max_length=255)
    primary_locale: str = "zh-TW"
    target_countries: list[str] = Field(default_factory=list)
    target_languages: list[str] = Field(default_factory=list)
    industry: str | None = None
    business_model: str | None = None


class SiteResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    domain: str
    site_name: str
    primary_locale: str
    status: str

    model_config = {"from_attributes": True}


class MemberResponse(BaseModel):
    user_id: UUID
    email: EmailStr
    name: str
    role: str
    status: str


class MemberRoleUpdate(BaseModel):
    role: str = Field(
        pattern="^(owner|admin|strategist|editor|analyst|client_viewer|billing_admin)$"
    )


class InvitationCreate(BaseModel):
    email: EmailStr
    role: str = Field(pattern="^(admin|strategist|editor|analyst|client_viewer|billing_admin)$")


class InvitationResponse(BaseModel):
    id: UUID
    email: EmailStr
    role: str
    status: str
    expires_at: datetime
    invite_token: str | None = None


class InvitationAccept(BaseModel):
    token: str


class IntegrationCredentialCreate(BaseModel):
    provider: str = Field(min_length=2, max_length=64)
    credential_type: str = Field(pattern="^(oauth|service_account|api_key)$")
    payload: str = Field(min_length=1)
    site_id: UUID | None = None
    credential_name: str = "default"


class IntegrationCredentialResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    site_id: UUID | None
    provider: str
    credential_name: str
    credential_type: str
    status: str

    model_config = {"from_attributes": True}


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    scopes: list[str] = Field(default_factory=lambda: ["site:read"])


class ApiKeyResponse(BaseModel):
    id: UUID
    name: str
    key_prefix: str
    scopes: list[str]
    status: str
    raw_key: str | None = None

    model_config = {"from_attributes": True}


class JobRunResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    job_type: str
    status: str

    model_config = {"from_attributes": True}


class DevTokenRequest(BaseModel):
    email: EmailStr
    name: str = "Dev User"
    role: str | None = None


class DevTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
