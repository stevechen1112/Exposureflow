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
  domain: string;
  site_name: string;
}

export interface Workspace {
  id: string;
  name: string;
  workspace_type: string;
}
