import type { ActionCandidate } from "@exposureflow/shared-types";

/** Action types eligible for content generation pipeline. */
export const CONTENT_GENERATION_ACTION_TYPES = new Set([
  "create_page",
  "solution_page",
  "enrich",
  "add_faq",
  "schema_enhancement",
  "comparison",
  "case_study",
]);

export function extractKeyword(candidate: ActionCandidate): string {
  const payload = (candidate.action_payload_json ?? {}) as Record<string, unknown>;
  const ev = (candidate.evidence_json ?? {}) as Record<string, unknown>;
  return (
    (payload.keyword as string) ||
    (payload.target_keyword as string) ||
    (ev.keyword as string) ||
    (ev.target_keyword as string) ||
    ""
  );
}

export function extractTargetUrl(candidate: ActionCandidate): string {
  const payload = (candidate.action_payload_json ?? {}) as Record<string, unknown>;
  const ev = (candidate.evidence_json ?? {}) as Record<string, unknown>;
  return (
    (payload.target_url as string) ||
    (payload.current_url as string) ||
    (ev.target_url as string) ||
    (ev.current_url as string) ||
    ""
  );
}

export function formatCandidateLabel(candidate: ActionCandidate): string {
  const keyword = extractKeyword(candidate);
  const url = extractTargetUrl(candidate);
  const parts: string[] = [];
  if (keyword) parts.push(keyword);
  parts.push(candidate.action_type);
  if (url) {
    const short = url.replace(/^https?:\/\//, "");
    parts.push(short.length > 48 ? `${short.slice(0, 45)}…` : short);
  } else if (candidate.opportunity_id) {
    parts.push(`${candidate.opportunity_id.slice(0, 8)}…`);
  }
  return parts.join(" · ");
}

export function isContentGenerationCandidate(candidate: ActionCandidate): boolean {
  return CONTENT_GENERATION_ACTION_TYPES.has(candidate.action_type);
}
