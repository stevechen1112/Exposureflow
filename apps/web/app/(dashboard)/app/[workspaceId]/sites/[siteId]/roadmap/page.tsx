"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
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
  const [busyId, setBusyId] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [building, setBuilding] = useState(false);

  async function approveItem(itemId: string) {
    setBusyId(itemId);
    setSuccess(null);
    try {
      await client.approveRoadmapItem(itemId, siteId);
      setSuccess("已核准該項目");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "核准失敗");
    } finally {
      setBusyId(null);
    }
  }

  async function rejectItem(itemId: string) {
    setBusyId(itemId);
    setSuccess(null);
    try {
      await client.rejectRoadmapItem(itemId, siteId);
      setSuccess("已退回該項目");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "操作失敗");
    } finally {
      setBusyId(null);
    }
  }

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [rms, mbs] = await Promise.all([
        client.listRoadmaps(siteId) as Promise<Roadmap[]>,
        client.listMembers().catch(() => [] as Member[]),
      ]);
      setRoadmaps(rms);
      setMembers(mbs);
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

  async function buildRoadmap() {
    setBuilding(true);
    setError(null);
    try {
      await client.buildRoadmap(siteId, {
        name: "8-week exposure roadmap",
        description: "從已核准的 Decision 自動排程 4/8/16 週執行路線",
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "建立 Roadmap 失敗");
    } finally {
      setBuilding(false);
    }
  }

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
      {success ? <p style={{ color: "var(--success)", marginBottom: "1rem" }}>{success}</p> : null}

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

      {/* Filter + Build */}
      <div className="form-row" style={{ marginBottom: "1rem" }}>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="all">全部狀態</option>
          <option value="in_progress">進行中</option>
          <option value="planned">計劃中</option>
          <option value="completed">已完成</option>
          <option value="blocked">阻塞中</option>
        </select>
        <button
          type="button"
          className="btn btn-primary"
          disabled={building}
          onClick={buildRoadmap}
          style={{ marginLeft: "auto" }}
        >
          {building ? "建立中…" : "從 Decision 建立 Roadmap"}
        </button>
      </div>

      {loading ? (
        <p style={{ color: "var(--muted)" }}>載入中…</p>
      ) : roadmaps.length === 0 ? (
        <div className="card" style={{ textAlign: "center", padding: "2rem" }}>
          <p style={{ color: "var(--muted)", marginBottom: "1rem" }}>
            尚無 roadmap。請先在「機會佇列」核准 Decision，再點擊下方按鈕自動排程。
          </p>
          <button
            type="button"
            className="btn btn-primary"
            disabled={building}
            onClick={buildRoadmap}
          >
            {building ? "建立中…" : "建立 Roadmap"}
          </button>
        </div>
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
                      <th>操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.length === 0 ? (
                      <tr>
                        <td colSpan={7} style={{ color: "var(--muted)" }}>
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
                          <td style={{ whiteSpace: "nowrap" }}>
                            {item.client_approval_status === "pending" && (
                              <>
                                <button
                                  type="button"
                                  className="btn btn-primary"
                                  style={{ fontSize: "0.78rem", padding: "0.25rem 0.5rem" }}
                                  disabled={busyId === item.id}
                                  onClick={() => approveItem(item.id)}
                                >
                                  核准
                                </button>
                                <button
                                  type="button"
                                  className="btn btn-ghost"
                                  style={{ fontSize: "0.78rem", padding: "0.25rem 0.5rem", marginLeft: "0.3rem", color: "var(--danger)" }}
                                  disabled={busyId === item.id}
                                  onClick={() => rejectItem(item.id)}
                                >
                                  退回
                                </button>
                              </>
                            )}
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
