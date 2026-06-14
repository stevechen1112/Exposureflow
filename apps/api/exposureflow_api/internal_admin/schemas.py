from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class WorkspaceOverview(BaseModel):
    id: UUID
    name: str
    account_id: UUID
    account_name: str
    workspace_type: str
    status: str
    member_count: int
    site_count: int
    subscription_status: str | None
    plan_code: str | None
    billing_status: str | None
    feature_flags: dict
    created_at: datetime


class AccountOverview(BaseModel):
    id: UUID
    name: str
    account_type: str
    billing_status: str
    workspace_count: int
    subscription_status: str | None
    plan_code: str | None
    created_at: datetime


class UserOverview(BaseModel):
    id: UUID
    email: str
    name: str
    status: str
    memberships: list[dict]
    created_at: datetime


class JobRunOverview(BaseModel):
    id: UUID
    workspace_id: UUID
    site_id: UUID | None
    job_type: str
    status: str
    provider: str | None
    provider_cost_cents: int
    error_code: str | None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None


class SyncStateOverview(BaseModel):
    id: UUID
    workspace_id: UUID
    site_id: UUID
    provider: str
    last_synced_at: datetime | None
    last_success_at: datetime | None
    last_error: str | None


class AuditLogOverview(BaseModel):
    id: UUID
    workspace_id: UUID | None
    account_id: UUID | None
    actor_user_id: UUID | None
    action: str
    target_type: str
    target_id: str | None
    metadata_json: dict
    created_at: datetime


class FeatureFlagsUpdate(BaseModel):
    feature_flags: dict = Field(default_factory=dict)


class ImpersonateRequest(BaseModel):
    target_user_id: UUID
    workspace_id: UUID | None = None
    reason: str = Field(min_length=10, max_length=500)


class ActivationRow(BaseModel):
    workspace_id: UUID
    workspace_name: str
    account_name: str
    activation_score: int
    milestones: dict
    last_activity_at: datetime | None
    churn_risk: str


class OnboardingFunnel(BaseModel):
    total_workspaces: int
    has_site: int
    first_gsc_sync: int
    first_opportunity: int
    first_report: int
    first_approved_decision: int
    fully_activated: int


class IntegrationHealthRow(BaseModel):
    provider: str
    total: int
    healthy: int
    failing: int
    stale: int


class ProviderCostRow(BaseModel):
    provider: str
    job_count: int
    total_cost_cents: int
    failed_jobs: int
