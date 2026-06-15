/** Shared TypeScript types aligned with ExposureFlow API contracts. */

export type WorkspaceRole =
  | "owner"
  | "admin"
  | "strategist"
  | "editor"
  | "analyst"
  | "client_viewer"
  | "billing_admin"
  | "support_admin";

export type OpportunityStatus =
  | "open"
  | "planned"
  | "executing"
  | "completed"
  | "rejected"
  | "monitoring";

export type OpportunityPriority = "low" | "medium" | "high" | "critical";

export interface TopicClusterPerformanceItem {
  id: string;
  name: string;
  total_impressions: number;
  coverage_score: number;
  ai_visibility_score: number;
  status: string;
}

export interface ExposureDashboardMetrics {
  total_impressions: number;
  impressions_delta_pct: number;
  query_coverage_count: number;
  indexed_asset_count: number;
  top_3_count: number;
  top_10_count: number;
  top_20_count: number;
  serp_slot_count: number;
  ai_citation_count: number;
  open_opportunity_count: number;
  critical_blocker_count: number;
  topic_cluster_performance: TopicClusterPerformanceItem[];
}

export interface Opportunity {
  id: string;
  site_id: string;
  opportunity_type: string;
  keyword: string | null;
  current_url: string | null;
  total_opportunity_score: number;
  priority: string;
  status: string;
  reason: string;
  evidence_json: Record<string, unknown>;
}

export interface ActionCandidate {
  id: string;
  opportunity_id: string;
  action_type: string;
  rank_score: number;
  risk_level: string;
  decision_status: string;
  evidence_json: Record<string, unknown>;
  action_payload_json: Record<string, unknown>;
}

export interface SerpMatrixResponse {
  keywords: string[];
  slot_types: string[];
  cells: Array<{
    keyword: string;
    slot_type: string;
    status: string;
    owner?: string;
  }>;
}

export interface AiVisibilityDashboard {
  probe_set_count: number;
  probe_run_count: number;
  citation_count: number;
  brand_mention_count: number;
  competitor_mention_count: number;
  serpo_summary: Record<string, number>;
  recent_citations: Array<Record<string, unknown>>;
}

export interface Site {
  id: string;
  workspace_id?: string;
  domain: string;
  site_name: string;
  primary_locale?: string;
  target_countries?: string[];
  target_languages?: string[];
  industry?: string | null;
  business_model?: string | null;
  status?: string;
}

export type SiteCreateInput = {
  domain: string;
  site_name: string;
  primary_locale?: string;
  target_countries?: string[];
  target_languages?: string[];
  industry?: string | null;
  business_model?: string | null;
};

export type SiteUpdateInput = Partial<SiteCreateInput>;

export type WorkspaceCreateInput = {
  name: string;
  workspace_type: "agency_internal" | "client" | "enterprise";
  client_name?: string | null;
  default_locale?: string;
};

export interface Workspace {
  id: string;
  name: string;
  workspace_type: string;
  client_name?: string | null;
  plan_limits?: Record<string, number>;
}

export interface BusinessIntake {
  id: string;
  workspace_id: string;
  site_id: string;
  status: string;
  version_number: number;
  parent_intake_id: string | null;
  is_current: boolean;
  archived_at: string | null;
  change_summary: string | null;
  company_summary: string | null;
  market_notes: string | null;
  customer_segments_json: string[];
  domestic_markets_json: string[];
  export_markets_json: string[];
  sales_regions_json: string[];
  strategic_goals_json: string[];
  constraints_json: string[];
  approved_by: string | null;
  approved_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface StrategyImpactPreview {
  keywords_to_add: Array<Record<string, unknown>>;
  keywords_to_block: Array<Record<string, unknown>>;
  constraint_rules_to_upsert: Array<Record<string, unknown>>;
  scopes_to_upsert: Array<Record<string, unknown>>;
  opportunities_affected: number;
  opportunity_samples: Array<Record<string, unknown>>;
  changes_summary: Record<string, unknown>;
}

export interface StrategyImpactApply {
  scope_id: string | null;
  keywords_created: number;
  keywords_updated: number;
  constraint_rules_synced: number;
  opportunities_rescored: number;
}

export type KeywordPyramidNodeType =
  | "pillar"
  | "cluster"
  | "long_tail"
  | "core"
  | "comparison"
  | "solution"
  | "faq";

export type BusinessFitStatus = "in_scope" | "needs_review" | "out_of_scope" | "blocked";

export interface KeywordPyramidNode {
  id: string;
  workspace_id: string;
  site_id: string;
  parent_id: string | null;
  product_service_scope_id: string | null;
  topic_node_id?: string | null;
  topic_cluster_id?: string | null;
  keyword: string;
  node_type: KeywordPyramidNodeType;
  intent: string | null;
  target_market: string | null;
  language: string | null;
  keyword_level?: string | null;
  funnel_stage?: string | null;
  is_target?: boolean;
  business_fit_status: BusinessFitStatus;
  priority: number;
  created_by: string;
  approved_by: string | null;
  approved_at: string | null;
  evidence_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface BusinessConstraintRule {
  id: string;
  workspace_id: string;
  site_id: string;
  source_intake_id: string | null;
  source_intake_version: number | null;
  description: string;
  rule_type: string;
  match_pattern: string;
  action: string;
  is_active: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;
}
