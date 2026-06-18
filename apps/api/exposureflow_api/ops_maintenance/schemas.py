from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class OpsHealthSignalOut(BaseModel):
    id: UUID
    severity: str
    category: str
    check_id: str
    title: str
    message: str
    recommended_action: str
    action_type: str | None = None
    workspace_id: UUID | None = None
    site_id: UUID | None = None
    evidence_json: dict = Field(default_factory=dict)


class OpsHealthRunOut(BaseModel):
    id: UUID
    status: str
    trigger: str
    started_at: datetime
    completed_at: datetime | None
    summary_title: str | None
    summary_markdown: str | None
    llm_provider: str | None = None
    llm_model: str | None = None


class OpsMaintenanceLatestResponse(BaseModel):
    run: OpsHealthRunOut | None
    signals: list[OpsHealthSignalOut]


class OpsMaintenanceRunRequest(BaseModel):
    use_llm_summary: bool = True


class OpsMaintenanceRunResponse(BaseModel):
    run: OpsHealthRunOut
    signals: list[OpsHealthSignalOut]
