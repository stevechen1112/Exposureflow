from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TopicClusterResponse(BaseModel):
    id: UUID
    site_id: UUID
    exposure_theme_id: UUID
    name: str
    pillar_keyword: str
    pillar_url: str | None
    coverage_score: float
    authority_score: float
    total_impressions: int
    status: str
    last_analyzed_at: datetime | None

    model_config = {"from_attributes": True}


class TopicNodeResponse(BaseModel):
    id: UUID
    site_id: UUID
    topic_cluster_id: UUID
    keyword: str
    keyword_level: str
    current_best_url: str | None
    status: str
    impressions: int
    clicks: int
    avg_position: float | None
    cluster_assignment_locked: bool
    evidence_json: dict

    model_config = {"from_attributes": True}


class TopicNodeAssignRequest(BaseModel):
    topic_cluster_id: UUID
    lock_assignment: bool = True


class RebuildRequest(BaseModel):
    site_id: UUID


class CannibalizationResponse(BaseModel):
    id: UUID
    keyword: str
    recommendation: str
    competing_urls: list
    status: str
    evidence_json: dict

    model_config = {"from_attributes": True}


class InternalLinkResponse(BaseModel):
    id: UUID
    topic_cluster_id: UUID
    source_url: str
    target_url: str
    anchor_text: str
    anchor_relevance_score: float
    approval_status: str
    evidence_json: dict

    model_config = {"from_attributes": True}


class InternalLinkApprovalRequest(BaseModel):
    approved: bool = True
