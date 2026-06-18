"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { useSiteContext } from "@/lib/hooks";

type TechIssue = {
  id: string;
  issue_type: string;
  severity: string;
  url: string;
  description?: string;
  details?: string;
  status?: string;
  recommended_action?: string;
};

const SEVERITY_ORDER: Record<string, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
};

const SEVERITY_CLASS: Record<string, string> = {
  critical: "badge-critical",
  high: "badge-high",
  medium: "",
  low: "",
};

const SEVERITY_LABEL: Record<string, string> = {
  critical: "Critical",
  high: "High",
  medium: "Medium",
  low: "Low",
};

const ISSUE_TYPE_LABEL: Record<string, string> = {
  broken_link: "失效連結",
  missing_meta: "缺少 Meta",
  slow_page: "頁面速度慢",
  missing_canonical: "缺少 Canonical",
  duplicate_content: "重複內容",
  indexing_blocked: "索引被阻擋",
  gsc_sitemap_unreachable: "GSC Sitemap 無法抓取",
  gsc_sitemap_missing: "GSC 未提交 Sitemap",
  gsc_sitemap_api_error: "GSC Sitemap API 錯誤",
  redirect_chain: "重定向鏈",
  missing_structured_data: "缺少結構化資料",
  core_web_vitals: "Core Web Vitals",
  mobile_usability: "行動裝置可用性",
};

export default function TechnicalIssuesPage() {
  const { siteId, client } = useSiteContext();
  const [issues, setIssues] = useState<TechIssue[]>([]);
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [error, setError] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const rows = await client.listTechnicalIssues(siteId);
      setIssues(
        (rows as TechIssue[]).sort(
          (a, b) =>
            (SEVERITY_ORDER[a.severity] ?? 9) - (SEVERITY_ORDER[b.severity] ?? 9),
        ),
      );
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "載入失敗");
    } finally {
      setLoading(false);
    }
  }, [client, siteId]);

  useEffect(() => {
    load();
  }, [load]);

  async function crawl() {
    setSyncing(true);
    try {
      await client.triggerTechSeoCrawl(siteId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Crawl 失敗");
    } finally {
      setSyncing(false);
    }
  }

  const uniqueTypes = useMemo(
    () => [...new Set(issues.map((i) => i.issue_type))],
    [issues],
  );

  const filtered = useMemo(() => {
    return issues.filter((i) => {
      const sevOk = severityFilter === "all" || i.severity === severityFilter;
      const typeOk = typeFilter === "all" || i.issue_type === typeFilter;
      return sevOk && typeOk;
    });
  }, [issues, severityFilter, typeFilter]);

  const criticalCount = issues.filter((i) => i.severity === "critical").length;
  const highCount = issues.filter((i) => i.severity === "high").length;
  const openCount = issues.filter((i) => !i.status || i.status === "open").length;

  return (
    <>
      <PageHeader title="技術問題" subtitle="Tech SEO 問題清單，依嚴重度分類" />

      {/* Summary cards */}
      {!loading && (
        <div className="kpi-grid" style={{ marginBottom: "1.5rem" }}>
          <div
            className="card"
            style={{ borderColor: criticalCount > 0 ? "var(--danger)" : "var(--border)" }}
          >
            <div className="kpi-label">Critical</div>
            <div
              className="kpi-value"
              style={{ color: criticalCount > 0 ? "var(--danger)" : undefined }}
            >
              {criticalCount}
            </div>
            <div style={{ fontSize: "0.78rem", color: "var(--muted)" }}>需立即處理</div>
          </div>
          <div
            className="card"
            style={{ borderColor: highCount > 0 ? "var(--warning)" : "var(--border)" }}
          >
            <div className="kpi-label">High</div>
            <div
              className="kpi-value"
              style={{ color: highCount > 0 ? "var(--warning)" : undefined }}
            >
              {highCount}
            </div>
            <div style={{ fontSize: "0.78rem", color: "var(--muted)" }}>高優先處理</div>
          </div>
          <div className="card">
            <div className="kpi-label">Open 問題</div>
            <div className="kpi-value">{openCount}</div>
          </div>
          <div className="card">
            <div className="kpi-label">問題類型</div>
            <div className="kpi-value">{uniqueTypes.length}</div>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="form-row" style={{ marginBottom: "1rem" }}>
        <button
          type="button"
          className="btn btn-primary"
          disabled={syncing}
          onClick={crawl}
        >
          {syncing ? "Crawl 中…" : "觸發 Tech SEO Crawl"}
        </button>
        <button type="button" className="btn" onClick={load} disabled={loading}>
          重新整理
        </button>
      </div>

      {error ? <p style={{ color: "var(--danger)", marginBottom: "1rem" }}>{error}</p> : null}

      {/* Filters */}
      <div className="form-row" style={{ marginBottom: "1rem" }}>
        {/* Severity filter tabs */}
        {(["all", "critical", "high", "medium", "low"] as const).map((sev) => {
          const count =
            sev === "all" ? issues.length : issues.filter((i) => i.severity === sev).length;
          return (
            <button
              key={sev}
              type="button"
              onClick={() => setSeverityFilter(sev)}
              style={{
                padding: "0.3rem 0.8rem",
                borderRadius: 999,
                border: "1px solid var(--border)",
                background:
                  severityFilter === sev
                    ? sev === "critical"
                      ? "var(--danger-soft)"
                      : sev === "high"
                        ? "var(--warning-soft)"
                        : "var(--accent)"
                    : "var(--surface-2)",
                color:
                  severityFilter === sev && sev === "critical"
                    ? "var(--danger)"
                    : severityFilter === sev && sev === "high"
                      ? "var(--warning)"
                      : severityFilter === sev
                        ? sev === "all" || sev === "medium" || sev === "low"
                          ? "#ffffff"
                          : "var(--text)"
                        : "var(--text)",
                cursor: "pointer",
                font: "inherit",
                fontSize: "0.82rem",
              }}
            >
              {sev === "all" ? "全部" : SEVERITY_LABEL[sev]}{" "}
              <span style={{ opacity: 0.7 }}>({count})</span>
            </button>
          );
        })}
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          style={{ marginLeft: "auto" }}
        >
          <option value="all">全部問題類型</option>
          {uniqueTypes.map((t) => (
            <option key={t} value={t}>
              {ISSUE_TYPE_LABEL[t] ?? t}
            </option>
          ))}
        </select>
      </div>

      <div className="table-wrap card" style={{ padding: 0 }}>
        <table>
          <thead>
            <tr>
              <th>嚴重度</th>
              <th>問題類型</th>
              <th>URL</th>
              <th>說明</th>
              <th>建議處置</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={5} style={{ color: "var(--muted)" }}>
                  載入中…
                </td>
              </tr>
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ color: "var(--muted)" }}>
                  {issues.length === 0 ? "目前沒有 open 技術問題" : "此篩選條件無符合項目"}
                </td>
              </tr>
            ) : (
              filtered.map((row) => (
                <tr key={row.id}>
                  <td>
                    <span className={`badge ${SEVERITY_CLASS[row.severity] ?? ""}`}>
                      {SEVERITY_LABEL[row.severity] ?? row.severity}
                    </span>
                  </td>
                  <td>{ISSUE_TYPE_LABEL[row.issue_type] ?? row.issue_type}</td>
                  <td
                    style={{
                      maxWidth: 280,
                      wordBreak: "break-all",
                      fontSize: "0.82rem",
                    }}
                  >
                    {row.url ? (
                      <a
                        href={row.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ color: "var(--accent)" }}
                      >
                        {row.url.slice(0, 60)}
                        {row.url.length > 60 ? "…" : ""}
                      </a>
                    ) : "—"}
                  </td>
                  <td style={{ fontSize: "0.85rem" }}>
                    {row.description ?? row.details ?? "—"}
                  </td>
                  <td style={{ fontSize: "0.82rem", color: "var(--accent-text)", maxWidth: 280 }}>
                    {row.recommended_action ?? "—"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
