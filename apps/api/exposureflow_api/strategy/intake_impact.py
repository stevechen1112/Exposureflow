"""Apply Strategy Intake changes to keyword pyramid, scopes, and opportunities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.exposure.scorer import ScoreInput, score_opportunity
from exposureflow_api.models.exposure import ExposureOpportunity
from exposureflow_api.models.strategy import (
    BusinessConstraintRule,
    BusinessIntake,
    KeywordPyramidNode,
    ProductServiceScope,
)
from exposureflow_api.strategy.business_fit import (
    evaluate_site_keyword_fit,
    parse_intake_constraint_rules,
)
from exposureflow_api.strategy.keyword_utils import normalize_keyword
from exposureflow_api.strategy.constraint_engine import (
    evaluate_constraint_match,
    parse_constraint_rules,
    rule_to_payload,
)
from exposureflow_api.strategy.keyword_extraction import (
    assign_parent_ids,
    extract_keyword_candidates,
)
from exposureflow_api.strategy.keyword_research import infer_funnel_stage, infer_keyword_level
from exposureflow_api.strategy.pyramid_topic_bridge import sync_site_pyramid_links

INTAKE_SCOPE_NAME = "Strategy Intake Scope"
STALE_INTAKE_REASONS = {"strategic_goal", "constraint", "create_blocked"}


@dataclass
class StrategyImpactPreview:
    keywords_to_add: list[dict[str, Any]] = field(default_factory=list)
    keywords_to_block: list[dict[str, Any]] = field(default_factory=list)
    constraint_rules_to_upsert: list[dict[str, Any]] = field(default_factory=list)
    scopes_to_upsert: list[dict[str, Any]] = field(default_factory=list)
    opportunities_affected: int = 0
    opportunity_samples: list[dict[str, Any]] = field(default_factory=list)
    changes_summary: dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyImpactResult:
    scope_id: str | None
    keywords_created: int
    keywords_updated: int
    constraint_rules_synced: int
    opportunities_rescored: int


def _unique_strings(values: list | None) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in values or []:
        text = str(raw).strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
    return out


def _merged_markets(intake: BusinessIntake) -> list[str]:
    return _unique_strings(
        list(intake.sales_regions_json or [])
        + list(intake.domestic_markets_json or [])
        + list(intake.export_markets_json or [])
    )


async def _load_nodes(
    db: AsyncSession, workspace_id: UUID, site_id: UUID
) -> list[KeywordPyramidNode]:
    result = await db.execute(
        select(KeywordPyramidNode).where(
            KeywordPyramidNode.workspace_id == workspace_id,
            KeywordPyramidNode.site_id == site_id,
        )
    )
    return list(result.scalars().all())


async def _load_intake_scope(
    db: AsyncSession, workspace_id: UUID, site_id: UUID
) -> ProductServiceScope | None:
    result = await db.execute(
        select(ProductServiceScope)
        .where(
            ProductServiceScope.workspace_id == workspace_id,
            ProductServiceScope.site_id == site_id,
            ProductServiceScope.source == "intake",
        )
        .order_by(ProductServiceScope.updated_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


def _scope_payload(intake: BusinessIntake) -> dict[str, Any]:
    markets = _merged_markets(intake)
    personas = _unique_strings(intake.customer_segments_json)
    return {
        "name": INTAKE_SCOPE_NAME,
        "scope_type": "service",
        "description": intake.company_summary,
        "target_markets_json": markets,
        "target_personas_json": personas,
        "priority": 4,
        "status": "active",
        "source": "intake",
    }


def _extract_candidates(intake: BusinessIntake) -> list[dict[str, Any]]:
    return assign_parent_ids(extract_keyword_candidates(intake))


async def _cleanup_stale_intake_nodes(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
) -> int:
    nodes = await _load_nodes(db, workspace_id, site_id)
    removed = 0
    for node in nodes:
        if node.created_by != "intake":
            continue
        if node.approved_at is not None:
            continue
        reason = (node.evidence_json or {}).get("reason")
        if reason in STALE_INTAKE_REASONS:
            await db.delete(node)
            removed += 1
    if removed:
        await db.flush()
    return removed


async def preview_intake_impact(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
    intake: BusinessIntake,
    *,
    previous: BusinessIntake | None = None,
) -> StrategyImpactPreview:
    nodes = await _load_nodes(db, workspace_id, site_id)
    nodes_by_keyword = {normalize_keyword(n.keyword): n for n in nodes if n.keyword}

    constraints = _unique_strings(intake.constraints_json)
    previous_constraints = _unique_strings(previous.constraints_json) if previous else []
    markets = _merged_markets(intake)
    parsed_rules = parse_constraint_rules(constraints)

    preview = StrategyImpactPreview(
        scopes_to_upsert=[_scope_payload(intake)],
        constraint_rules_to_upsert=[rule_to_payload(rule) for rule in parsed_rules],
        changes_summary={
            "candidates_added": [],
            "constraints_added": [c for c in constraints if c not in previous_constraints],
            "constraints_removed": [c for c in previous_constraints if c not in constraints],
            "markets": markets,
        },
    )

    for item in _extract_candidates(intake):
        normalized = normalize_keyword(str(item["keyword"]))
        if normalized in nodes_by_keyword:
            continue
        preview.keywords_to_add.append(item)
        preview.changes_summary["candidates_added"].append(item["keyword"])

    for node in nodes:
        hit = evaluate_constraint_match(node.keyword, parsed_rules)
        if hit and node.business_fit_status not in ("blocked", "out_of_scope"):
            preview.keywords_to_block.append(
                {
                    "keyword": node.keyword,
                    "node_id": str(node.id),
                    "action": "update_blocked",
                    "reason": f"matches_constraint:{hit.match_pattern}",
                }
            )

    seen_blocks: set[str] = set()
    deduped_blocks: list[dict[str, Any]] = []
    for item in preview.keywords_to_block:
        key = item.get("node_id") or normalize_keyword(str(item.get("keyword")))
        if key in seen_blocks:
            continue
        seen_blocks.add(key)
        deduped_blocks.append(item)
    preview.keywords_to_block = deduped_blocks

    opp_result = await db.execute(
        select(ExposureOpportunity).where(
            ExposureOpportunity.workspace_id == workspace_id,
            ExposureOpportunity.site_id == site_id,
            ExposureOpportunity.status == "open",
        )
    )
    opportunities = list(opp_result.scalars().all())
    for opp in opportunities:
        if not opp.keyword:
            continue
        fit = await evaluate_site_keyword_fit(
            db,
            workspace_id,
            site_id,
            opp.keyword,
            constraint_rules=parsed_rules,
        )
        old_score = float(opp.total_opportunity_score or 0)
        inputs = (opp.evidence_json or {}).get("inputs", {})
        new_score_result = score_opportunity(
            ScoreInput(
                query_impressions_28d=int(inputs.get("query_impressions_28d") or opp.current_impressions or 0),
                site_p95_query_impressions=int(inputs.get("site_p95_query_impressions") or 100),
                current_position=inputs.get("current_position", opp.current_position),
                business_fit_score=fit.business_fit_score,
            )
        )
        new_score = new_score_result.total_opportunity_score
        if fit.blocked or abs(new_score - old_score) >= 0.01:
            preview.opportunities_affected += 1
            if len(preview.opportunity_samples) < 5:
                preview.opportunity_samples.append(
                    {
                        "keyword": opp.keyword,
                        "old_score": old_score,
                        "new_score": new_score,
                        "old_fit_status": (opp.evidence_json or {}).get("business_fit", {}).get(
                            "business_fit_status", "unknown"
                        ),
                        "new_fit_status": fit.business_fit_status,
                    }
                )

    return preview


async def _sync_constraint_rules(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
    intake: BusinessIntake,
    constraints: list[str],
) -> int:
    await db.execute(
        update(BusinessConstraintRule)
        .where(
            BusinessConstraintRule.workspace_id == workspace_id,
            BusinessConstraintRule.site_id == site_id,
            BusinessConstraintRule.created_by == "intake",
            BusinessConstraintRule.is_active.is_(True),
        )
        .values(is_active=False)
    )

    parsed_rules = parse_constraint_rules(constraints)
    for rule in parsed_rules:
        db.add(
            BusinessConstraintRule(
                workspace_id=workspace_id,
                site_id=site_id,
                source_intake_id=intake.id,
                source_intake_version=intake.version_number,
                description=rule.description,
                rule_type=rule.rule_type,
                match_pattern=rule.match_pattern,
                action=rule.action,
                is_active=True,
                created_by="intake",
            )
        )
    await db.flush()
    return len(parsed_rules)


async def apply_intake_impact(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
    intake: BusinessIntake,
    *,
    user_id: UUID,
) -> StrategyImpactResult:
    await _cleanup_stale_intake_nodes(db, workspace_id, site_id)

    preview = await preview_intake_impact(db, workspace_id, site_id, intake)
    nodes = await _load_nodes(db, workspace_id, site_id)
    nodes_by_keyword = {normalize_keyword(n.keyword): n for n in nodes if n.keyword}
    nodes_by_id = {str(n.id): n for n in nodes}
    markets = _merged_markets(intake)
    constraints = _unique_strings(intake.constraints_json)
    parsed_rules = parse_intake_constraint_rules(constraints)

    scope = await _load_intake_scope(db, workspace_id, site_id)
    scope_payload = _scope_payload(intake)

    if scope is None:
        scope = ProductServiceScope(workspace_id=workspace_id, site_id=site_id, **scope_payload)
        db.add(scope)
        await db.flush()
    else:
        for key, value in scope_payload.items():
            setattr(scope, key, value)
        await db.flush()

    constraint_rules_synced = await _sync_constraint_rules(
        db, workspace_id, site_id, intake, constraints
    )

    keywords_created = 0
    keywords_updated = 0
    created_nodes: dict[str, KeywordPyramidNode] = {}

    for item in preview.keywords_to_add:
        normalized = normalize_keyword(str(item["keyword"]))
        if normalized in nodes_by_keyword:
            continue
        node_type = str(item.get("node_type") or "cluster")
        intent = item.get("intent")
        node = KeywordPyramidNode(
            workspace_id=workspace_id,
            site_id=site_id,
            keyword=str(item["keyword"]).strip(),
            node_type=node_type,
            intent=intent,
            target_market=markets[0] if markets else None,
            language="zh-TW",
            keyword_level=infer_keyword_level(node_type),
            funnel_stage=infer_funnel_stage(intent, node_type),
            business_fit_status="needs_review",
            priority=4,
            created_by="intake",
            product_service_scope_id=scope.id,
            evidence_json={
                "source": "intake",
                "intake_id": str(intake.id),
                "intake_version": intake.version_number,
                "reason": item.get("reason"),
                "source_text": item.get("source_text"),
                "confidence": item.get("confidence"),
            },
        )
        db.add(node)
        await db.flush()
        nodes_by_keyword[normalized] = node
        created_nodes[normalized] = node
        keywords_created += 1

    for item in preview.keywords_to_add:
        parent_keyword = item.get("parent_keyword")
        if not parent_keyword:
            continue
        child = nodes_by_keyword.get(normalize_keyword(str(item["keyword"])))
        parent = nodes_by_keyword.get(normalize_keyword(str(parent_keyword)))
        if child and parent and child.parent_id is None:
            child.parent_id = parent.id

    for item in preview.keywords_to_block:
        node_id = item.get("node_id")
        if not node_id:
            continue
        node = nodes_by_id.get(str(node_id)) or await db.get(KeywordPyramidNode, UUID(str(node_id)))
        if node is None or node.workspace_id != workspace_id:
            continue
        node.business_fit_status = "blocked"
        node.evidence_json = {
            **(node.evidence_json or {}),
            "source": "intake",
            "intake_id": str(intake.id),
            "intake_version": intake.version_number,
            "reason": item.get("reason"),
        }
        keywords_updated += 1

    await db.flush()

    opp_result = await db.execute(
        select(ExposureOpportunity).where(
            ExposureOpportunity.workspace_id == workspace_id,
            ExposureOpportunity.site_id == site_id,
            ExposureOpportunity.status == "open",
        )
    )
    opportunities_rescored = 0
    for opp in opp_result.scalars().all():
        if not opp.keyword:
            continue
        fit = await evaluate_site_keyword_fit(
            db,
            workspace_id,
            site_id,
            opp.keyword,
            constraint_rules=parsed_rules,
        )
        inputs = (opp.evidence_json or {}).get("inputs", {})
        score = score_opportunity(
            ScoreInput(
                query_impressions_28d=int(inputs.get("query_impressions_28d") or opp.current_impressions or 0),
                site_p95_query_impressions=int(inputs.get("site_p95_query_impressions") or 100),
                current_position=inputs.get("current_position", opp.current_position),
                business_fit_score=fit.business_fit_score,
            )
        )
        old_score = float(opp.total_opportunity_score or 0)
        if abs(score.total_opportunity_score - old_score) < 0.01 and not fit.blocked:
            continue
        if fit.blocked:
            opp.status = "rejected"
            opp.priority = "low"
        opp.total_opportunity_score = score.total_opportunity_score
        opp.priority = score.priority
        opp.ranking_feasibility_score = score.subscores["ranking_feasibility_score"]
        opp.serp_slot_score = score.subscores["serp_slot_score"]
        opp.ai_citation_score = score.subscores["ai_citation_score"]
        opp.topic_contribution_score = score.subscores["topic_contribution_score"]
        opp.zero_click_value_score = score.subscores["zero_click_value_score"]
        evidence = dict(opp.evidence_json or {})
        evidence["intake_rescore"] = {
            "intake_id": str(intake.id),
            "intake_version": intake.version_number,
            "actor_user_id": str(user_id),
            "business_fit": fit.evidence,
        }
        evidence["business_fit"] = fit.evidence
        evidence["subscores"] = score.subscores
        opp.evidence_json = evidence
        opportunities_rescored += 1

    await db.flush()
    await sync_site_pyramid_links(db, workspace_id, site_id)
    return StrategyImpactResult(
        scope_id=str(scope.id),
        keywords_created=keywords_created,
        keywords_updated=keywords_updated,
        constraint_rules_synced=constraint_rules_synced,
        opportunities_rescored=opportunities_rescored,
    )
