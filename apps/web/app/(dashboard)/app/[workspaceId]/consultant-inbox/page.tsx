"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { PageHeader } from "@/components/PageHeader";
import { parseApiError } from "@/components/ForbiddenState";
import { useWorkspaceAuth } from "@/lib/auth-context";
import { getApiClient } from "@/lib/api-client";

type InboxItem = {
  id: string;
  category: string;
  priority: string;
  title: string;
  detail: string;
  site_id: string;
  site_name: string;
  site_domain: string;
  action_path: string;
  source_type: string;
  source_id: string;
  created_at?: string | null;
  evidence_summary?: string | null;
  action_hint?: string | null;
  workspace_id?: string | null;
  workspace_label?: string | null;
};

type InboxSite = {
  id: string;
  site_name: string;
  domain: string;
  workspace_id?: string | null;
};

type InboxWorkspace = {
  id: string;
  name: string;
  client_name: string | null;
  urgent: number;
  total: number;
  primary_site_id: string | null;
};

type InboxPayload = {
  scope?: string;
  summary: { urgent: number; in_progress: number; monitoring: number; total: number };
  sites: InboxSite[];
  workspaces?: InboxWorkspace[];
  urgent: InboxItem[];
  in_progress: InboxItem[];
  monitoring: InboxItem[];
};

const PRIORITY_BADGE: Record<string, string> = {
  critical: "badge-critical",
  high: "badge-high",
  medium: "badge-medium",
};

const CATEGORY_LABEL: Record<string, string> = {
  technical: "技術",
  content: "內容審核",
  decision: "決策",
  strategy: "策略",
  indexability: "索引",
  sync: "同步",
  opportunity: "機會",
  roadmap: "路線圖",
};

function formatDate(iso?: string | null) {
  if (!iso) return "";
  return new Date(iso).toLocaleString("zh-TW", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

function filterItems(items: InboxItem[], workspaceFilter: string, siteFilter: string) {
  return items.filter((item) => {
    if (workspaceFilter && item.workspace_id !== workspaceFilter) return false;
    if (siteFilter && item.site_id !== siteFilter) return false;
    return true;
  });
}

function InboxSection({
  title,
  subtitle,
  items,
  emptyText,
  showWorkspace,
}: {
  title: string;
  subtitle?: string;
  items: InboxItem[];
  emptyText: string;
  showWorkspace: boolean;
}) {
  return (
    <div className="today-section">
      <h2>
        {title}{" "}
        <span style={{ fontSize: "0.82rem", color: "var(--muted)", fontWeight: 400 }}>（{items.length} 項）</span>
      </h2>
      {subtitle ? (
        <p style={{ fontSize: "0.88rem", color: "var(--muted)", margin: "0 0 0.75rem" }}>{subtitle}</p>
      ) : null}
      <div className="card">
        {items.length === 0 ? (
          <div className="empty-state">
            <p>{emptyText}</p>
          </div>
        ) : (
          items.map((item) => (
            <div key={item.id} className="today-item">
              <span className="today-dot" />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.25rem" }}>
                  <span className={PRIORITY_BADGE[item.priority] ?? "badge-medium"}>{item.priority}</span>
                  <span className="badge-muted">{CATEGORY_LABEL[item.category] ?? item.category}</span>
                  {showWorkspace && item.workspace_label ? (
                    <span className="badge-medium">{item.workspace_label}</span>
                  ) : null}
                  <span style={{ fontSize: "0.8rem", color: "var(--muted)" }}>
                    {item.site_name} · {item.site_domain}
                  </span>
                </div>
                <Link href={item.action_path} className="today-link">
                  {item.title}
                </Link>
                <p style={{ margin: "0.2rem 0 0", fontSize: "0.88rem", color: "var(--muted)" }}>{item.detail}</p>
                {item.action_hint ? (
                  <p className="inbox-action-hint">
                    <strong>顧問怎麼做：</strong>{item.action_hint}
                  </p>
                ) : null}
                {item.evidence_summary ? (
                  <p style={{ margin: "0.25rem 0 0", fontSize: "0.82rem", color: "var(--accent-text)" }}>
                    診斷：{item.evidence_summary}
                  </p>
                ) : null}
              </div>
              {item.created_at ? <span className="today-meta">{formatDate(item.created_at)}</span> : null}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default function ConsultantInboxPage() {
  const params = useParams<{ workspaceId: string }>();
  const searchParams = useSearchParams();
  const { workspaces, can } = useWorkspaceAuth();
  const client = getApiClient(params.workspaceId);
  const [data, setData] = useState<InboxPayload | null>(null);
  const [inboxScope, setInboxScope] = useState<"workspace" | "account">("workspace");
  const [workspaceFilter, setWorkspaceFilter] = useState("");
  const [siteFilter, setSiteFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const clientWorkspaceCount = useMemo(
    () => workspaces.filter((w) => w.workspace_type !== "agency_internal").length,
    [workspaces],
  );
  const allowAccountScope = clientWorkspaceCount > 1 || can("agency:read");

  useEffect(() => {
    if (!allowAccountScope) {
      setInboxScope("workspace");
      return;
    }
    if (searchParams.get("scope") === "workspace") {
      setInboxScope("workspace");
    } else {
      setInboxScope("account");
    }
  }, [allowAccountScope, searchParams]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const scope = allowAccountScope && inboxScope === "account" ? "account" : "workspace";
      const payload = (await client.getConsultantInbox({
        scope,
        siteId: scope === "workspace" && siteFilter ? siteFilter : undefined,
      })) as InboxPayload;
      setData(payload);
    } catch (err) {
      setError(parseApiError(err instanceof Error ? err.message : "載入失敗").friendly);
    } finally {
      setLoading(false);
    }
  }, [allowAccountScope, client, inboxScope, siteFilter]);

  useEffect(() => {
    load();
  }, [load]);

  const showWorkspace = allowAccountScope && inboxScope === "account";
  const filteredUrgent = useMemo(
    () => filterItems(data?.urgent ?? [], workspaceFilter, siteFilter),
    [data?.urgent, workspaceFilter, siteFilter],
  );
  const filteredProgress = useMemo(
    () => filterItems(data?.in_progress ?? [], workspaceFilter, siteFilter),
    [data?.in_progress, workspaceFilter, siteFilter],
  );
  const filteredMonitoring = useMemo(
    () => filterItems(data?.monitoring ?? [], workspaceFilter, siteFilter),
    [data?.monitoring, workspaceFilter, siteFilter],
  );
  const displaySummary = useMemo(
    () => ({
      urgent: filteredUrgent.length,
      in_progress: filteredProgress.length,
      monitoring: filteredMonitoring.length,
      total: filteredUrgent.length + filteredProgress.length + filteredMonitoring.length,
    }),
    [filteredUrgent.length, filteredProgress.length, filteredMonitoring.length],
  );

  const siteOptions = useMemo(() => {
    const sites = data?.sites ?? [];
    if (!workspaceFilter) return sites;
    return sites.filter((s) => s.workspace_id === workspaceFilter);
  }, [data?.sites, workspaceFilter]);

  if (loading && !data) {
    return <p style={{ color: "var(--muted)" }}>載入顧問工作台…</p>;
  }

  return (
    <>
      <PageHeader
        title="顧問工作台"
        subtitle="高優先且會阻擋曝光、發布或同步的項目 — 每項下方有「顧問怎麼做」指引"
      />
      {error ? <p style={{ color: "var(--danger)", marginBottom: "1rem" }}>{error}</p> : null}

      {allowAccountScope ? (
        <div className="scope-tabs">
          <button
            type="button"
            className={`scope-tab${inboxScope === "workspace" ? " active" : ""}`}
            onClick={() => { setInboxScope("workspace"); setWorkspaceFilter(""); }}
          >
            本工作區
          </button>
          <button
            type="button"
            className={`scope-tab${inboxScope === "account" ? " active" : ""}`}
            onClick={() => setInboxScope("account")}
          >
            全部客戶
          </button>
        </div>
      ) : null}

      <div className="kpi-grid" style={{ marginBottom: "1.25rem" }}>
        <div className="kpi-card">
          <span className="kpi-label">待處理（需立即行動）</span>
          <span className="kpi-value" style={{ color: "var(--danger)" }}>{displaySummary.urgent}</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">進行中（已立案）</span>
          <span className="kpi-value" style={{ color: "var(--warning)" }}>{displaySummary.in_progress}</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">策略待辦</span>
          <span className="kpi-value">{displaySummary.monitoring}</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">總計</span>
          <span className="kpi-value">{displaySummary.total}</span>
        </div>
      </div>

      {showWorkspace && (data?.workspaces?.length ?? 0) > 0 ? (
        <div className="card" style={{ marginBottom: "1rem" }}>
          <h3 style={{ marginTop: 0, fontSize: "0.95rem" }}>各客戶待辦摘要</h3>
          <div className="table-wrap" style={{ padding: 0 }}>
            <table>
              <thead>
                <tr>
                  <th>客戶</th>
                  <th>待處理</th>
                  <th>總計</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {(data?.workspaces ?? []).map((w) => (
                  <tr key={w.id}>
                    <td>{w.client_name || w.name}</td>
                    <td style={{ color: w.urgent > 0 ? "var(--danger)" : undefined, fontWeight: w.urgent > 0 ? 600 : 400 }}>
                      {w.urgent}
                    </td>
                    <td>{w.total}</td>
                    <td style={{ whiteSpace: "nowrap" }}>
                      <Link href={`/app/${w.id}/consultant-inbox`}>工作台</Link>
                      {w.primary_site_id ? (
                        <>
                          {" · "}
                          <Link href={`/app/${w.id}/sites/${w.primary_site_id}/dashboard`}>儀表板</Link>
                        </>
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}

      <div className="card" style={{ marginBottom: "1.25rem", display: "flex", gap: "1rem", flexWrap: "wrap", alignItems: "center" }}>
        {showWorkspace ? (
          <label style={{ display: "flex", gap: "0.5rem", alignItems: "center", fontSize: "0.9rem" }}>
            篩選客戶
            <select
              value={workspaceFilter}
              onChange={(e) => { setWorkspaceFilter(e.target.value); setSiteFilter(""); }}
              className="context-switcher-select"
              style={{ width: "auto", minWidth: 160 }}
            >
              <option value="">全部客戶</option>
              {(data?.workspaces ?? []).map((w) => (
                <option key={w.id} value={w.id}>{w.client_name || w.name}</option>
              ))}
            </select>
          </label>
        ) : null}
        <label style={{ display: "flex", gap: "0.5rem", alignItems: "center", fontSize: "0.9rem" }}>
          篩選站點
          <select
            value={siteFilter}
            onChange={(e) => setSiteFilter(e.target.value)}
            className="context-switcher-select"
            style={{ width: "auto", minWidth: 180 }}
          >
            <option value="">全部站點</option>
            {siteOptions.map((s) => (
              <option key={`${s.workspace_id ?? ""}-${s.id}`} value={s.id}>
                {showWorkspace && s.workspace_id
                  ? `${(data?.workspaces ?? []).find((w) => w.id === s.workspace_id)?.client_name || ""} · `
                  : ""}
                {s.site_name} ({s.domain})
              </option>
            ))}
          </select>
        </label>
        <button type="button" className="btn-secondary" onClick={() => load()} disabled={loading}>
          {loading ? "重新整理中…" : "重新整理"}
        </button>
      </div>

      <InboxSection
        title="🔴 待處理"
        subtitle="技術問題、內容審核、同步失敗、索引修復、待決策 — 請依「顧問怎麼做」完成後系統會自動重檢或移出此區"
        items={filteredUrgent}
        emptyText="目前沒有待處理項目"
        showWorkspace={showWorkspace}
      />
      <InboxSection
        title="🟡 進行中"
        subtitle="路線圖上已啟動的項目 — 請更新進度或標記完成"
        items={filteredProgress}
        emptyText="沒有進行中路線圖項目"
        showWorkspace={showWorkspace}
      />
      <InboxSection
        title="🔵 策略待辦"
        subtitle="關鍵字核准、覆蓋缺口、曝光機會等排程規劃 — 非緊急，但需納入內容策略"
        items={filteredMonitoring}
        emptyText="沒有策略待辦項目"
        showWorkspace={showWorkspace}
      />
    </>
  );
}
