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
  recent_reports: Array<{ id: string; title: string; report_type: string; created_at: string }>;
  pending_approvals: Array<{ id: string; title: string; week_number: number; client_approval_status: string }>;
  completed_actions: Array<Record<string, unknown>>;
  meeting_notes: Array<{ id: string; title: string; meeting_date: string; summary: string }>;
};

export default function ClientPortalPage() {
  const params = useParams<{ workspaceId: string }>();
  const [siteId, setSiteId] = useState<string>("");
  const [data, setData] = useState<PortalDashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

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
    try {
      if (approved) await client.approveRoadmapItem(itemId, siteId);
      else await client.rejectRoadmapItem(itemId, siteId);
      if (siteId) await load(siteId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "操作失敗");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <main className="content" style={{ maxWidth: 960, margin: "0 auto" }}>
      <PageHeader title="客戶入口" subtitle="月報、Roadmap 待核准與曝光趨勢" />
      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}
      {!data ? (
        <p style={{ color: "var(--muted)" }}>載入中…</p>
      ) : (
        <>
          <div className="kpi-grid">
            <div className="card">
              <div className="kpi-label">28 天曝光</div>
              <div className="kpi-value">{data.exposure_summary.total_impressions.toLocaleString()}</div>
              <div className={data.exposure_summary.impressions_delta_pct >= 0 ? "delta-up" : "delta-down"}>
                {data.exposure_summary.impressions_delta_pct >= 0 ? "+" : ""}
                {data.exposure_summary.impressions_delta_pct}% MoM
              </div>
            </div>
            <div className="card">
              <div className="kpi-label">Open 機會</div>
              <div className="kpi-value">{data.exposure_summary.open_opportunity_count}</div>
            </div>
          </div>

          <section style={{ marginTop: "2rem" }}>
            <h2 style={{ fontSize: "1.1rem" }}>待核准事項</h2>
            <div className="table-wrap card" style={{ padding: 0 }}>
              <table>
                <thead>
                  <tr>
                    <th>項目</th>
                    <th>週次</th>
                    <th>狀態</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {data.pending_approvals.length === 0 ? (
                    <tr>
                      <td colSpan={4} style={{ color: "var(--muted)" }}>
                        目前沒有待核准項目
                      </td>
                    </tr>
                  ) : (
                    data.pending_approvals.map((item) => (
                      <tr key={item.id}>
                        <td>{item.title}</td>
                        <td>W{item.week_number}</td>
                        <td>{item.client_approval_status}</td>
                        <td>
                          <button type="button" className="btn btn-primary" disabled={busyId === item.id} onClick={() => approve(item.id, true)}>
                            核准
                          </button>{" "}
                          <button type="button" className="btn" disabled={busyId === item.id} onClick={() => approve(item.id, false)}>
                            拒絕
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>

          <section style={{ marginTop: "2rem" }}>
            <h2 style={{ fontSize: "1.1rem" }}>最近月報</h2>
            <ul>
              {data.recent_reports.map((r) => (
                <li key={r.id}>
                  {r.title} · {r.report_type} · {r.created_at.slice(0, 10)}
                </li>
              ))}
            </ul>
          </section>

          <section style={{ marginTop: "2rem" }}>
            <h2 style={{ fontSize: "1.1rem" }}>月會紀錄</h2>
            {data.meeting_notes.map((m) => (
              <div key={m.id} className="card" style={{ marginBottom: "0.75rem" }}>
                <strong>{m.title}</strong> · {m.meeting_date}
                <p style={{ color: "var(--muted)", margin: "0.5rem 0 0" }}>{m.summary}</p>
              </div>
            ))}
          </section>
        </>
      )}
    </main>
  );
}
