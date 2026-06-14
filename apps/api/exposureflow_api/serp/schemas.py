from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SerpSnapshotListItem(BaseModel):
    id: UUID
    keyword: str
    country: str
    language: str
    device: str
    raw_provider: str
    captured_at: datetime

    model_config = {"from_attributes": True}


class SerpSlotTargetResponse(BaseModel):
    id: UUID
    site_id: UUID
    keyword: str
    slot_type: str
    target_status: str
    current_owner: str | None
    current_owner_url: str | None
    recommended_action: str | None
    evidence_json: dict

    model_config = {"from_attributes": True}


class SerpSlotTargetUpdate(BaseModel):
    target_status: str | None = None


class SerpSnapshotRunRequest(BaseModel):
    site_id: UUID
    keyword: str
    country: str = "tw"
    language: str | None = None
    device: str = "desktop"
