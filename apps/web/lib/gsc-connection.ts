/** GSC consultant-led connection helpers (Path C — agency operates on behalf of client). */

export const GSC_SERVICE_ACCOUNT_EMAIL =
  process.env.NEXT_PUBLIC_GSC_SERVICE_ACCOUNT_EMAIL ??
  "exposureflow-gsc-reader@exposureflow-gsc.iam.gserviceaccount.com";

export type GscCredential = {
  id: string;
  site_id: string | null;
  provider: string;
  credential_name: string;
  credential_type: string;
  status: string;
};

export type GscSyncState = {
  provider: string;
  site_id: string;
  last_synced_at?: string;
  last_success_at?: string;
  last_error?: string | null;
  cursor_json?: { last_synced_date?: string } | null;
};

export type GscDataSummary = {
  total_rows: number;
  distinct_queries: number;
  distinct_pages: number;
  earliest_date: string | null;
  latest_date: string | null;
  top_queries: Array<{
    query: string;
    impressions: number;
    clicks: number;
    position: number;
  }>;
};

export type GscConnectionPhase =
  | "no_site"
  | "needs_client_auth"
  | "needs_credential"
  | "needs_sync"
  | "sync_error"
  | "connected";

export function normalizeDomain(domain: string): string {
  return domain
    .trim()
    .replace(/^https?:\/\//i, "")
    .replace(/\/+$/, "");
}

export function defaultGscProperty(domain: string): string {
  const normalized = normalizeDomain(domain);
  return normalized ? `sc-domain:${normalized}` : "";
}

export function alternateGscProperty(domain: string): string {
  const normalized = normalizeDomain(domain);
  return normalized ? `https://${normalized}/` : "";
}

export function findSiteCredential(
  credentials: GscCredential[],
  siteId: string,
): GscCredential | undefined {
  const siteScoped = credentials.find(
    (c) => c.provider === "gsc" && c.status === "active" && c.site_id === siteId,
  );
  if (siteScoped) return siteScoped;
  return credentials.find(
    (c) => c.provider === "gsc" && c.status === "active" && c.site_id == null,
  );
}

export function findGscSyncState(states: GscSyncState[], siteId: string): GscSyncState | undefined {
  return states.find((s) => s.provider === "gsc" && s.site_id === siteId);
}

export function resolveGscConnectionPhase(input: {
  siteId: string | null;
  credential?: GscCredential;
  syncState?: GscSyncState;
}): GscConnectionPhase {
  if (!input.siteId) return "no_site";
  if (!input.credential) return "needs_credential";
  if (input.syncState?.last_error) return "sync_error";
  if (input.syncState?.last_success_at) return "connected";
  if (input.syncState?.last_synced_at && !input.syncState.last_success_at) return "needs_sync";
  return "needs_client_auth";
}

export function gscPhaseLabel(phase: GscConnectionPhase): string {
  switch (phase) {
    case "no_site":
      return "請先建立站點";
    case "needs_credential":
      return "待上傳平台 Credential";
    case "needs_client_auth":
      return "待客戶 GSC 授權";
    case "needs_sync":
      return "同步進行中";
    case "sync_error":
      return "同步失敗";
    case "connected":
      return "已連線";
  }
}

export function gscPhaseTone(phase: GscConnectionPhase): "success" | "warning" | "danger" | "muted" {
  switch (phase) {
    case "connected":
      return "success";
    case "sync_error":
      return "danger";
    case "no_site":
    case "needs_credential":
    case "needs_client_auth":
    case "needs_sync":
      return "warning";
  }
}

export function diagnoseGscError(error?: string | null): { title: string; actions: string[] } | null {
  if (!error) return null;
  const lower = error.toLowerCase();

  if (lower.includes("credential") || lower.includes("not configured")) {
    return {
      title: "平台尚未設定 GSC Credential",
      actions: [
        "請工程或顧問透過 API 上傳 Service Account JSON（測試階段）",
        "確認 credential 綁定正確 site_id",
      ],
    };
  }

  if (lower.includes("403") || lower.includes("permission") || lower.includes("forbidden")) {
    return {
      title: "GSC 權限不足",
      actions: [
        `請客戶在 Search Console 新增 ${GSC_SERVICE_ACCOUNT_EMAIL}`,
        "權限需為「完整」",
        "確認 property 與站點 domain 一致",
      ],
    };
  }

  if (lower.includes("404") || lower.includes("not found") || lower.includes("site")) {
    return {
      title: "GSC Property 可能不符",
      actions: [
        "向客戶確認 property 是 sc-domain: 還是 https:// 前綴",
        "同步時可指定 input_json.site_url 覆寫預設 property",
      ],
    };
  }

  return {
    title: "同步發生錯誤",
    actions: ["查看下方錯誤訊息", "修正後重新觸發同步", "若持續失敗請聯絡工程"],
  };
}

export function fmtDateTime(iso?: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("zh-TW", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}
