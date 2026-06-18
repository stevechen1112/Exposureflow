"""Consultant work queue schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ConsultantInboxSite(BaseModel):
    id: str
    site_name: str
    domain: str
    workspace_id: str | None = None


class ConsultantInboxWorkspace(BaseModel):
    id: str
    name: str
    client_name: str | None = None
    workspace_type: str
    urgent: int = 0
    total: int = 0
    primary_site_id: str | None = None
    primary_site_domain: str | None = None


class ConsultantInboxItem(BaseModel):
    id: str
    category: str
    priority: str
    title: str
    detail: str
    site_id: str
    site_name: str
    site_domain: str
    action_path: str
    source_type: str
    source_id: str
    created_at: str | None = None
    evidence_summary: str | None = None
    action_hint: str | None = None
    workspace_id: str | None = None
    workspace_label: str | None = None


class ConsultantInboxSummary(BaseModel):
    urgent: int = 0
    in_progress: int = 0
    monitoring: int = 0
    total: int = 0


class ConsultantInboxResponse(BaseModel):
    scope: str = "workspace"
    summary: ConsultantInboxSummary
    sites: list[ConsultantInboxSite]
    workspaces: list[ConsultantInboxWorkspace] = Field(default_factory=list)
    urgent: list[ConsultantInboxItem] = Field(default_factory=list)
    in_progress: list[ConsultantInboxItem] = Field(default_factory=list)
    monitoring: list[ConsultantInboxItem] = Field(default_factory=list)
