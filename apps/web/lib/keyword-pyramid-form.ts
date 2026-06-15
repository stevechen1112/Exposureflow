export type KeywordPyramidNodeType =
  | "pillar"
  | "cluster"
  | "long_tail"
  | "core"
  | "comparison"
  | "solution"
  | "faq";

export type BusinessFitStatus = "in_scope" | "needs_review" | "out_of_scope" | "blocked";

export type KeywordPyramidFormValues = {
  keyword: string;
  node_type: KeywordPyramidNodeType;
  intent: string;
  target_market: string;
  language: string;
  priority: number;
  parent_id: string;
  product_service_scope_id: string;
  keyword_level: string;
  funnel_stage: string;
  is_target: boolean;
  business_fit_status: BusinessFitStatus;
};

export const EMPTY_KEYWORD_PYRAMID_FORM: KeywordPyramidFormValues = {
  keyword: "",
  node_type: "pillar",
  intent: "",
  target_market: "TW",
  language: "zh-TW",
  priority: 3,
  parent_id: "",
  product_service_scope_id: "",
  keyword_level: "",
  funnel_stage: "",
  is_target: false,
  business_fit_status: "needs_review",
};

export const NODE_TYPE_OPTIONS: Array<{ value: KeywordPyramidNodeType; label: string }> = [
  { value: "pillar", label: "Pillar（主題柱）" },
  { value: "cluster", label: "Cluster（群集）" },
  { value: "long_tail", label: "Long-tail（長尾）" },
  { value: "core", label: "Core（核心）" },
  { value: "comparison", label: "Comparison（比較）" },
  { value: "solution", label: "Solution（解法）" },
  { value: "faq", label: "FAQ" },
];

export const FUNNEL_OPTIONS = [
  { value: "", label: "未指定" },
  { value: "tofu", label: "TOFU（認知）" },
  { value: "mofu", label: "MOFU（考慮）" },
  { value: "bofu", label: "BOFU（決策）" },
];

export const KEYWORD_LEVEL_OPTIONS = [
  { value: "", label: "自動" },
  { value: "head", label: "Head（核心大字）" },
  { value: "mid_tail", label: "Mid-tail（中階）" },
  { value: "long_tail", label: "Long-tail（長尾）" },
];

export const INTENT_OPTIONS = [
  { value: "", label: "未指定" },
  { value: "informational", label: "資訊型" },
  { value: "commercial", label: "商業調查" },
  { value: "transactional", label: "交易型" },
  { value: "navigational", label: "導航型" },
];

export const BUSINESS_FIT_OPTIONS: Array<{ value: BusinessFitStatus; label: string }> = [
  { value: "needs_review", label: "待審（候選）" },
  { value: "in_scope", label: "正式納入（in_scope）" },
  { value: "out_of_scope", label: "排除（out_of_scope）" },
  { value: "blocked", label: "封鎖（blocked）" },
];

export function nodeTypeLabel(nodeType: string): string {
  return NODE_TYPE_OPTIONS.find((o) => o.value === nodeType)?.label ?? nodeType;
}

export function businessFitLabel(status: string): string {
  switch (status) {
    case "in_scope":
      return "正式";
    case "needs_review":
      return "待審";
    case "out_of_scope":
      return "排除";
    case "blocked":
      return "封鎖";
    default:
      return status;
  }
}

export function createdByLabel(source: string): string {
  switch (source) {
    case "intake":
      return "Intake 推演";
    case "consultant":
      return "顧問";
    case "system":
      return "系統";
    default:
      return source;
  }
}

export function isActiveNode(node: Record<string, unknown>): boolean {
  return String(node.business_fit_status ?? "") === "in_scope";
}

export function isOfficialNode(node: Record<string, unknown>): boolean {
  return (
    isActiveNode(node) &&
    Boolean(node.approved_at) &&
    ["pillar", "cluster", "long_tail"].includes(String(node.node_type ?? ""))
  );
}

export function isApprovedOfficialNode(node: Record<string, unknown>): boolean {
  return isOfficialNode(node);
}

/** in_scope 但尚未按核准（例如直接新增正式關鍵字） */
export function isPendingApprovalNode(node: Record<string, unknown>): boolean {
  return isActiveNode(node) && !node.approved_at;
}

export type InclusionStatus = "approved" | "pending_approval" | "candidate" | "excluded" | "blocked";

export function inclusionStatus(node: Record<string, unknown>): InclusionStatus {
  const fit = String(node.business_fit_status ?? "");
  if (fit === "blocked") return "blocked";
  if (fit === "out_of_scope") return "excluded";
  if (fit === "needs_review") return "candidate";
  if (fit === "in_scope" && node.approved_at) return "approved";
  if (isPendingApprovalNode(node)) return "pending_approval";
  return "candidate";
}

export function inclusionStatusLabel(node: Record<string, unknown>): string {
  switch (inclusionStatus(node)) {
    case "approved":
      return "已正式納入";
    case "pending_approval":
      return "待按核准";
    case "candidate":
      return "待審候選";
    case "excluded":
      return "已排除";
    case "blocked":
      return "已封鎖";
    default:
      return "—";
  }
}

export function inclusionStatusHint(node: Record<string, unknown>): string {
  switch (inclusionStatus(node)) {
    case "approved":
      return "顧問已核准，會連結曝光地圖";
    case "pending_approval":
      return "已在 scope，但尚未核准";
    case "candidate":
      return "Intake / 研究草稿，需編輯後核准";
    case "excluded":
      return "不納入本專案";
    case "blocked":
      return "限制規則封鎖";
    default:
      return "";
  }
}

export function isCandidateNode(node: Record<string, unknown>): boolean {
  return String(node.business_fit_status ?? "") === "needs_review";
}

export function isExcludedNode(node: Record<string, unknown>): boolean {
  const status = String(node.business_fit_status ?? "");
  return status === "blocked" || status === "out_of_scope";
}

export function isBlockedNode(node: Record<string, unknown>): boolean {
  return isExcludedNode(node);
}

export function formValuesToPayload(
  siteId: string,
  values: KeywordPyramidFormValues,
  options?: { createdBy?: string },
) {
  return {
    site_id: siteId,
    keyword: values.keyword.trim(),
    node_type: values.node_type,
    parent_id: values.parent_id.trim() || null,
    intent: values.intent || null,
    target_market: values.target_market.trim() || null,
    language: values.language.trim() || null,
    product_service_scope_id: values.product_service_scope_id.trim() || null,
    keyword_level: values.keyword_level.trim() || null,
    funnel_stage: values.funnel_stage.trim() || null,
    is_target: values.is_target,
    priority: values.priority,
    business_fit_status: values.business_fit_status,
    created_by: options?.createdBy ?? "consultant",
  };
}

export function nodeToFormValues(node: Record<string, unknown>): KeywordPyramidFormValues {
  return {
    keyword: String(node.keyword ?? ""),
    node_type: (String(node.node_type ?? "pillar") as KeywordPyramidNodeType),
    intent: String(node.intent ?? ""),
    target_market: String(node.target_market ?? "TW"),
    language: String(node.language ?? "zh-TW"),
    priority: Number(node.priority ?? 3),
    parent_id: String(node.parent_id ?? ""),
    product_service_scope_id: String(node.product_service_scope_id ?? ""),
    keyword_level: String(node.keyword_level ?? ""),
    funnel_stage: String(node.funnel_stage ?? ""),
    is_target: Boolean(node.is_target),
    business_fit_status: (String(node.business_fit_status ?? "needs_review") as BusinessFitStatus),
  };
}

export function enrichmentSummary(node: Record<string, unknown>): string {
  const enrichment = (node.evidence_json as Record<string, unknown> | undefined)?.enrichment as
    | Record<string, unknown>
    | undefined;
  if (!enrichment) return "—";
  const slots = enrichment.targetable_slot_count;
  const features = Array.isArray(enrichment.serp_features) ? enrichment.serp_features.length : 0;
  if (slots != null) return `${slots} 版位 / ${features} 特徵`;
  return features > 0 ? `${features} SERP 特徵` : "—";
}

export type PyramidTreeNode = {
  node: Record<string, unknown>;
  children: PyramidTreeNode[];
};

export function buildPyramidTree(nodes: Array<Record<string, unknown>>): PyramidTreeNode[] {
  const byId = new Map(nodes.map((node) => [String(node.id), node]));
  const childrenByParent = new Map<string, Array<Record<string, unknown>>>();
  for (const node of nodes) {
    const parentId = String(node.parent_id ?? "");
    const key = parentId && byId.has(parentId) ? parentId : "__root__";
    const bucket = childrenByParent.get(key) ?? [];
    bucket.push(node);
    childrenByParent.set(key, bucket);
  }

  function build(parentKey: string): PyramidTreeNode[] {
    return (childrenByParent.get(parentKey) ?? [])
      .sort((a, b) => Number(b.priority ?? 0) - Number(a.priority ?? 0))
      .map((node) => ({
        node,
        children: build(String(node.id)),
      }));
  }

  return build("__root__");
}

export function parentLabel(
  node: Record<string, unknown>,
  nodesById: Map<string, Record<string, unknown>>,
): string {
  const parentId = String(node.parent_id ?? "");
  if (!parentId) return "—";
  const parent = nodesById.get(parentId);
  return parent ? String(parent.keyword ?? parentId) : parentId.slice(0, 8);
}

/** 批次匯入：每行「層級,關鍵字」或僅關鍵字（預設 pillar） */
export function parseBatchKeywords(text: string): Array<{ keyword: string; node_type: KeywordPyramidNodeType }> {
  const rows: Array<{ keyword: string; node_type: KeywordPyramidNodeType }> = [];
  const validTypes = new Set(NODE_TYPE_OPTIONS.map((o) => o.value));

  for (const line of text.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;

    const comma = trimmed.indexOf(",");
    const tab = trimmed.indexOf("\t");
    const sep = comma >= 0 ? comma : tab;

    if (sep >= 0) {
      const typeRaw = trimmed.slice(0, sep).trim().toLowerCase();
      const keyword = trimmed.slice(sep + 1).trim();
      if (!keyword) continue;
      const node_type = (validTypes.has(typeRaw as KeywordPyramidNodeType)
        ? typeRaw
        : "pillar") as KeywordPyramidNodeType;
      rows.push({ keyword, node_type });
    } else {
      rows.push({ keyword: trimmed, node_type: "pillar" });
    }
  }
  return rows;
}
