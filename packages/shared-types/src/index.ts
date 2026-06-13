/** Shared TypeScript types aligned with ExposureFlow API contracts. */

export type WorkspaceRole =
  | "owner"
  | "admin"
  | "strategist"
  | "editor"
  | "analyst"
  | "client_viewer"
  | "billing_admin";

export type OpportunityStatus =
  | "open"
  | "planned"
  | "executing"
  | "completed"
  | "rejected"
  | "monitoring";

export type OpportunityPriority = "low" | "medium" | "high" | "critical";

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
}
