"""Pydantic schemas for billing API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PlanResponse(BaseModel):
    id: UUID
    name: str
    plan_code: str
    limits_json: dict
    price_monthly_cents: int
    price_yearly_cents: int

    model_config = {"from_attributes": True}


class SubscriptionResponse(BaseModel):
    id: UUID
    account_id: UUID
    plan: PlanResponse
    status: str
    stripe_subscription_id: str | None
    current_period_start: datetime | None
    current_period_end: datetime | None
    trial_end: datetime | None
    custom_limits_json: dict | None


class CheckoutRequest(BaseModel):
    plan_code: str = Field(pattern="^(starter|professional|agency)$")
    billing_interval: str = Field(default="month", pattern="^(month|year)$")


class CheckoutResponse(BaseModel):
    mode: str
    checkout_url: str
    session_id: str


class PortalResponse(BaseModel):
    mode: str
    portal_url: str


class UsageSummaryResponse(BaseModel):
    workspace_id: str
    metrics: dict
    limits: dict


class WorkspaceTransferRequest(BaseModel):
    to_account_id: UUID
    to_organization_id: UUID


class WorkspaceBrandingUpdate(BaseModel):
    organization_name: str
    logo_url: str | None = None
    primary_color: str | None = None
    custom_domain: str | None = None
    report_footer: str | None = None


class WorkspaceBrandingResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    organization_name: str
    logo_url: str | None
    primary_color: str | None
    custom_domain: str | None
    report_footer: str | None

    model_config = {"from_attributes": True}
