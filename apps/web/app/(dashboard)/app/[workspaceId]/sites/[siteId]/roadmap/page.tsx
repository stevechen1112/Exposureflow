"use client";

import { useEffect, useMemo, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { useSiteContext } from "@/lib/hooks";

type RoadmapItem = {
  id: string;
  week_number: number;
  title: string;
  description?: string;
  status: string;
  client_approval_status?: string;
  owner_user_id?: string;
};

type Roadmap = {
  id: string;
  title?: string;
  horizon_weeks: number;
  status: string;
  items: RoadmapItem[];
};

type Member = {
  user_id?: string;
  id?: string;
  display_name?: string;
  name?: string;
  email?: string;
};

const STATUS_CLASS: Record<string, string> = {
  completed: "",
  in_progress: "badge-high",
  planned: "",
  cancelled: "badge-critical",
  blocked: "badge-critical",
};

const STATUS_LABEL: Record<string, string> = {
  completed: "已完成",
  in_progress: "進行中",
  planned: "計劃中",
  cancelled: "已取消",
  blocked: "阻塞中",
};

const APPROVAL_CLASS: Record<string, string> = {
  approved: "",
  pending: "badge-high",
  rejected: "badge-critical",
  not_required: "",
};

const APPROVAL_LABEL: Record<string, string> = {
  approved: "客戶已核准",
  pending: "等待客戶核准",
  rejected: "客戶拒絕",
  not_required: "不需審核",
};

function fmtTime(iso: string) {
  return new Date(iso).toLocaleDateString("zh-TW", { month: "2-digit", day: "2-digit" });
}

export default function RoadmapPage() {
  const { siteId, client } = useSiteContext();
  const [roadmaps, setRoadmaps] = useState<Roadmap[]>([]);
  const [members, setMembers] = useState<Member[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      client.listRoadmaps(siteId) as Promise<Roadmap[]>,
      client.listMembers().catch(() => [] as Member[]),
    ])
      .then(([rms, mbs]) => {
        setRoadmaps(rms);
        setMembers(mbs);
        setError(null);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [client, siteId]);

  const memberMap = useMemo(() => {
    const map: Record<string, string> = {};
    for (const m of members) {
      const uid = m.user_id ?? m.id ?? "";
      const label = m.display_name ?? m.name ?? m.email ?? uid.slice(0, 8);
      if (uid) map[uid] = label;
    }
    return map;
  }, [members]);

  function resolveOwner(uid?: string) {
    if (!uid) return "—";
    return memberMap[uid] ?? uid.slice(0, 8) + "…";
  }

  const allItems = roadmaps.flatMap((rm) => rm.items ?? []);
  const completedCount = allItems.filter((i) => i.status === "completed").length;
  const inProgressCount = allItems.filter((i) => i.status === "in_progress").length;
  const pendingApprovalCount = allItems.filter(
    (i) => i.client_approval_status === "pending",
  ).length;

  return (
    <>
      <PageHeader title="Roadmap" subtitle="4 / 8 / 16 週執行路線、項目狀態與客戶核准追蹤" />
      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}

      {!loading && roadmaps.length > 0 && (
        <div className="kpi-grid" style={{ marginBottom: "1.5rem" }}>
          <div className="card">
            <div className="kpi-label">項目總數</div>
            <div className="kpi-value">{allItems.length}</div>
          </div>
          <div className="card">
            <div className="kpi-label">進行中</div>
            <div className="kpi-value" style={{ color: inProgressCount > 0 ? "var(--warning)" : undefined }}>
              {inProgressCount}
            </div>
          </div>
          <div className="card">
            <div className="kpi-label">已完成</div>
            <div className="kpi-value" style={{ color: "var(--success)" }}>
              {completedCount}
            </div>
          </div>
          {pendingApprovalCount > 0 && (
            <div
              className="card"
              style={{ borderColor: "var(--warning)" }}
            >
              <div className="kpi-label">待客戶核准</div>
              <div className="kpi-value" style={{ color: "var(--warning)" }}>
                {pendingApprovalCount}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Filter */}
      <div className="form-row" style={{ marginBottom: "1rem" }}>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="all">全部狀態</option>
          <option value="in_progress">進行中</option>
          <option value="planned">計劃中</option>
          <option value="completed">已完成</option>
          <option value="blocked">阻塞中</option>
        </select>
      </div>

      {loading ? (
        <p style={{ color: "var(--muted)" }}>載入中…</p>
      ) : roadmaps.length === 0 ? (
        <p style={{ color: "var(--muted)" }}>尚無 roadmap，請從 Decision Plane 建立。</p>
      ) : (
        roadmaps.map((rm) => {
          const items = (rm.items ?? []).filter(
            (it) => statusFilter === "all" || it.status === statusFilter,
          );
          return (
            <section key={rm.id} style={{ marginBottom: "2.5rem" }}>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.75rem",
                  marginBottom: "0.75rem",
                }}
              >
                <h2 style={{ fontSize: "1.1rem", margin: 0 }}>
                  {String(rm.title ?? "Roadmap")}
                </h2>
                <span className="badge">{rm.horizon_weeks} 週</span>
                <span className={`badge ${STATUS_CLASS[rm.status] ?? ""}`}>
                  {STATUS_LABEL[rm.status] ?? rm.status}
                </span>
                {items.length > 0 && (
                  <span style={{ fontSize: "0.82rem", color: "var(--muted)", marginLeft: "auto" }}>
                    {items.filter((i) => i.status === "completed").length} / {items.length} 完成
                  </span>
                )}
              </div>

              <div className="table-wrap card" style={{ padding: 0 }}>
                <table>
                  <thead>
                    <tr>
                      <th style={{ width: 56 }}>週次</th>
                      <th>標題</th>
                      <th>說明</th>
                      <th>執行狀態</th>
                      <th>客戶核准</th>
                      <th>負責人</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.length === 0 ? (
                      <tr>
                        <td colSpan={6} style={{ color: "var(--muted)" }}>
                          此狀態下沒有項目
                        </td>
                      </tr>
                    ) : (
                      items.map((item) => (
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
                            <span className={`badge ${STATUS_CLASS[item.status] ?? ""}`}>
                              {STATUS_LABEL[item.status] ?? item.status}
                            </span>
                          </td>
                          <td>
                            {item.client_approval_status ? (
                              <span
                                className={`badge ${APPROVAL_CLASS[item.client_approval_status] ?? ""}`}
                              >
                                {APPROVAL_LABEL[item.client_approval_status] ??
                                  item.client_approval_status}
                              </span>
                            ) : (
                              <span style={{ color: "var(--muted)" }}>—</span>
                            )}
                          </td>
                          <td style={{ fontSize: "0.85rem" }}>
                            {resolveOwner(item.owner_user_id)}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </section>
          );
        })
      )}
    </>
  );
}
