"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { PageHeader } from "@/components/PageHeader";
import { getApiClient } from "@/lib/api-client";
import { storageKey } from "@/lib/config";

type PortalDashboard = {
  exposure_summary: {
    total_impressions: number;
    impressions_delta_pct: number;
    open_opportunity_count: number;
  };
  recent_reports: Array<{
    id: string;
    title: string;
    report_type: string;
    created_at: string;
    delivery_mode?: string;
  }>;
  pending_approvals: Array<{
    id: string;
    title: string;
    week_number: number;
    client_approval_status: string;
    description?: string;
  }>;
  completed_actions: Array<{
    id: string;
    action_type?: string;
    outcome_type?: string;
    keyword?: string;
    result_summary?: string;
    impression_delta?: number;
    completed_at?: string;
  }>;
  meeting_notes: Array<{
    id: string;
    title: string;
    meeting_date: string;
    summary: string;
  }>;
};

const APPROVAL_CLASS: Record<string, string> = {
  approved: "",
  pending: "badge-high",
  rejected: "badge-critical",
};
const APPROVAL_LABEL: Record<string, string> = {
  approved: "已核准",
  pending: "待核准",
  rejected: "已拒絕",
};

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString("zh-TW", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
}

async function downloadReport(
  client: ReturnType<typeof getApiClient>,
  reportId: string,
  title: string,
) {
  const blob = await client.exportReport(reportId, "markdown");
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${title.replace(/\s+/g, "_")}.md`;
  a.click();
  URL.revokeObjectURL(url);
}

export default function ClientPortalPage() {
  const params = useParams<{ workspaceId: string }>();
  const [siteId, setSiteId] = useState<string>("");
  const [data, setData] = useState<PortalDashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [downloadBusy, setDownloadBusy] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const client = getApiClient(params.workspaceId);

  async function load(sid: string) {
    const dash = await client.getClientPortalDashboard(sid);
    setData(dash as PortalDashboard);
  }

  useEffect(() => {
    const sid = localStorage.getItem(storageKey("siteId")) ?? "";
    setSiteId(sid);
    if (!sid) return;
    load(sid).catch((err: Error) => setError(err.message));
  }, [params.workspaceId]);

  async function approve(itemId: string, approved: boolean) {
    setBusyId(itemId);
    setSuccess(null);
    try {
      if (approved) await client.approveRoadmapItem(itemId, siteId);
      else await client.rejectRoadmapItem(itemId, siteId);
      setSuccess(approved ? "已核准" : "已拒絕");
      if (siteId) await load(siteId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "操作失敗");
    } finally {
      setBusyId(null);
    }
  }

  async function handleDownload(reportId: string, title: string) {
    setDownloadBusy(reportId);
    try {
      await downloadReport(client, reportId, title);
    } catch (err) {
      setError(err instanceof Error ? err.message : "下載失敗");
    } finally {
      setDownloadBusy(null);
    }
  }

  const delta = data?.exposure_summary.impressions_delta_pct ?? 0;

  return (
    <main className="content" style={{ maxWidth: 1040, margin: "0 auto" }}>
      <PageHeader title="客戶入口" subtitle="月報、Roadmap 待核准、已完成行動與曝光摘要" />

      {error ? (
        <p style={{ color: "var(--danger)", marginBottom: "1rem" }}>{error}</p>
      ) : null}
      {success ? (
        <p style={{ color: "var(--success)", marginBottom: "1rem" }}>{success}</p>
      ) : null}

      {!data ? (
        <p style={{ color: "var(--muted)" }}>載入中…</p>
      ) : (
        <>
          {/* Exposure KPIs */}
          <div className="kpi-grid" style={{ marginBottom: "2rem" }}>
            <div className="card">
              <div className="kpi-label">28 天自然曝光</div>
              <div className="kpi-value">
                {data.exposure_summary.total_impressions.toLocaleString()}
              </div>
              <div className={delta >= 0 ? "delta-up" : "delta-down"} style={{ fontSize: "0.9rem" }}>
                {delta >= 0 ? "▲" : "▼"} {Math.abs(delta)}% MoM
              </div>
              <div style={{ fontSize: "0.78rem", color: "var(--muted)", marginTop: "0.25rem" }}>
                自然搜尋曝光次數（Google Search Console）
              </div>
            </div>
            <div className="card">
              <div className="kpi-label">Open 機會</div>
              <div className="kpi-value">
                {data.exposure_summary.open_opportunity_count}
              </div>
              <div style={{ fontSize: "0.78rem", color: "var(--muted)", marginTop: "0.25rem" }}>
                待執行的建議行動
              </div>
            </div>
            <div className="card">
              <div className="kpi-label">已完成行動</div>
              <div className="kpi-value" style={{ color: "var(--success)" }}>
                {data.completed_actions.length}
              </div>
              <div style={{ fontSize: "0.78rem", color: "var(--muted)", marginTop: "0.25rem" }}>
                本月已執行完成
              </div>
            </div>
            <div className="card">
              <div className="kpi-label">待核准事項</div>
              <div
                className="kpi-value"
                style={{
                  color:
                    data.pending_approvals.length > 0 ? "var(--warning)" : undefined,
                }}
              >
                {data.pending_approvals.length}
              </div>
              <div style={{ fontSize: "0.78rem", color: "var(--muted)", marginTop: "0.25rem" }}>
                需要您核准的 Roadmap 項目
              </div>
            </div>
          </div>

          {/* Pending Approvals */}
          <section style={{ marginBottom: "2rem" }}>
            <h2 style={{ fontSize: "1.1rem", marginBottom: "0.75rem" }}>
              待核准事項
              {data.pending_approvals.length > 0 && (
                <span
                  style={{
                    marginLeft: "0.5rem",
                    fontSize: "0.8rem",
                    background: "var(--warning)",
                    color: "var(--text)",
                    padding: "0.1rem 0.5rem",
                    borderRadius: 999,
                  }}
                >
                  {data.pending_approvals.length}
                </span>
              )}
            </h2>
            <div className="table-wrap card" style={{ padding: 0 }}>
              <table>
                <thead>
                  <tr>
                    <th>週次</th>
                    <th>項目</th>
                    <th>說明</th>
                    <th>核准狀態</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {data.pending_approvals.length === 0 ? (
                    <tr>
                      <td colSpan={5} style={{ color: "var(--muted)" }}>
                        目前沒有待核准項目
                      </td>
                    </tr>
                  ) : (
                    data.pending_approvals.map((item) => (
                      <tr key={item.id}>
                        <td style={{ fontWeight: 600, color: "var(--accent)" }}>
                          W{item.week_number}
                        </td>
                        <td style={{ fontWeight: 500 }}>{item.title}</td>
                        <td
                          style={{
                            fontSize: "0.82rem",
                            color: "var(--muted)",
                            maxWidth: 240,
                          }}
                        >
                          {item.description ?? "—"}
                        </td>
                        <td>
                          <span
                            className={`badge ${APPROVAL_CLASS[item.client_approval_status] ?? ""}`}
                          >
                            {APPROVAL_LABEL[item.client_approval_status] ??
                              item.client_approval_status}
                          </span>
                        </td>
                        <td>
                          {item.client_approval_status === "pending" ? (
                            <div style={{ display: "flex", gap: "0.35rem" }}>
                              <button
                                type="button"
                                className="btn btn-primary"
                                style={{ fontSize: "0.8rem", padding: "0.3rem 0.6rem" }}
                                disabled={busyId === item.id}
                                onClick={() => approve(item.id, true)}
                              >
                                核准
                              </button>
                              <button
                                type="button"
                                className="btn"
                                style={{ fontSize: "0.8rem", padding: "0.3rem 0.6rem" }}
                                disabled={busyId === item.id}
                                onClick={() => approve(item.id, false)}
                              >
                                拒絕
                              </button>
                            </div>
                          ) : (
                            <span style={{ color: "var(--muted)", fontSize: "0.82rem" }}>
                              {APPROVAL_LABEL[item.client_approval_status] ?? "—"}
                            </span>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>

          {/* Completed Actions */}
          <section style={{ marginBottom: "2rem" }}>
            <h2 style={{ fontSize: "1.1rem", marginBottom: "0.75rem" }}>已完成行動</h2>
            {data.completed_actions.length === 0 ? (
              <p style={{ color: "var(--muted)" }}>本期尚無已完成行動</p>
            ) : (
              <div className="table-wrap card" style={{ padding: 0 }}>
                <table>
                  <thead>
                    <tr>
                      <th>行動類型</th>
                      <th>關鍵字</th>
                      <th>成果摘要</th>
                      <th>曝光增量</th>
                      <th>完成時間</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.completed_actions.map((action) => (
                      <tr key={action.id}>
                        <td>
                          <code style={{ fontSize: "0.8rem" }}>
                            {action.action_type ?? action.outcome_type ?? "—"}
                          </code>
                        </td>
                        <td style={{ fontWeight: 500 }}>
                          {action.keyword ?? "—"}
                        </td>
                        <td style={{ fontSize: "0.85rem", maxWidth: 280 }}>
                          {action.result_summary ?? "—"}
                        </td>
                        <td>
                          {action.impression_delta != null ? (
                            <span
                              style={{
                                color:
                                  action.impression_delta >= 0
                                    ? "var(--success)"
                                    : "var(--danger)",
                                fontWeight: 600,
                              }}
                            >
                              {action.impression_delta >= 0 ? "+" : ""}
                              {action.impression_delta.toLocaleString()}
                            </span>
                          ) : (
                            <span style={{ color: "var(--muted)" }}>—</span>
                          )}
                        </td>
                        <td style={{ fontSize: "0.82rem", color: "var(--muted)", whiteSpace: "nowrap" }}>
                          {action.completed_at ? fmtDate(action.completed_at) : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* Recent Reports */}
          <section style={{ marginBottom: "2rem" }}>
            <h2 style={{ fontSize: "1.1rem", marginBottom: "0.75rem" }}>最近月報</h2>
            {data.recent_reports.length === 0 ? (
              <p style={{ color: "var(--muted)" }}>尚無月報</p>
            ) : (
              <div className="table-wrap card" style={{ padding: 0 }}>
                <table>
                  <thead>
                    <tr>
                      <th>報告名稱</th>
                      <th>類型</th>
                      <th>建立日期</th>
                      <th>下載</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.recent_reports.map((r) => (
                      <tr key={r.id}>
                        <td style={{ fontWeight: 500 }}>{r.title}</td>
                        <td>
                          <span className="badge">{r.report_type}</span>
                        </td>
                        <td style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
                          {fmtDate(r.created_at)}
                        </td>
                        <td>
                          <button
                            type="button"
                            className="btn"
                            style={{ fontSize: "0.8rem", padding: "0.3rem 0.6rem" }}
                            disabled={downloadBusy === r.id}
                            onClick={() => handleDownload(r.id, r.title)}
                          >
                            {downloadBusy === r.id ? "下載中…" : "下載 MD"}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* Meeting Notes */}
          {data.meeting_notes.length > 0 && (
            <section>
              <h2 style={{ fontSize: "1.1rem", marginBottom: "0.75rem" }}>月會紀錄</h2>
              {data.meeting_notes.map((m) => (
                <div key={m.id} className="card" style={{ marginBottom: "0.75rem" }}>
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      marginBottom: "0.5rem",
                    }}
                  >
                    <strong>{m.title}</strong>
                    <span style={{ fontSize: "0.82rem", color: "var(--muted)" }}>
                      {m.meeting_date}
                    </span>
                  </div>
                  <p style={{ color: "var(--muted)", margin: 0, fontSize: "0.88rem", lineHeight: 1.6 }}>
                    {m.summary}
                  </p>
                </div>
              ))}
            </section>
          )}
        </>
      )}
    </main>
  );
}
