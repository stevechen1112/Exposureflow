"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { ActionCandidate } from "@exposureflow/shared-types";
import { PageHeader } from "@/components/PageHeader";
import { useSiteContext } from "@/lib/hooks";

const RISK_CLASS: Record<string, string> = {
  critical: "badge-critical",
  high: "badge-high",
  medium: "",
  low: "",
};

const ACTION_LABEL: Record<string, string> = {
  create_content: "新建內容",
  update_content: "更新內容",
  optimize_snippet: "優化摘要",
  build_internal_links: "建立內部連結",
  fix_technical: "修復技術問題",
  claim_serp_slot: "搶佔 SERP 版位",
  add_faq: "新增 FAQ",
  consolidate: "合併頁面",
};

function EvidenceCard({ evidence }: { evidence: Record<string, unknown> }) {
  const entries = Object.entries(evidence).filter(
    ([, v]) => v !== null && v !== undefined && v !== "",
  );
  if (entries.length === 0) return <span style={{ color: "var(--muted)" }}>—</span>;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.2rem" }}>
      {entries.slice(0, 4).map(([k, v]) => (
        <div key={k} style={{ fontSize: "0.78rem" }}>
          <span style={{ color: "var(--muted)" }}>{k.replace(/_/g, " ")}: </span>
          <span>
            {typeof v === "number"
              ? v.toLocaleString()
              : String(v).slice(0, 60)}
          </span>
        </div>
      ))}
      {entries.length > 4 && (
        <div style={{ fontSize: "0.75rem", color: "var(--muted)" }}>
          +{entries.length - 4} 更多欄位
        </div>
      )}
    </div>
  );
}

function extractKeyword(candidate: ActionCandidate): string {
  const payload = candidate.action_payload_json as Record<string, unknown>;
  const ev = candidate.evidence_json as Record<string, unknown>;
  return (
    (payload?.keyword as string) ||
    (payload?.target_keyword as string) ||
    (ev?.keyword as string) ||
    (ev?.target_keyword as string) ||
    "—"
  );
}

function extractRecommendedAction(candidate: ActionCandidate): string {
  const payload = candidate.action_payload_json as Record<string, unknown>;
  return (
    (payload?.recommended_action as string) ||
    (payload?.action_summary as string) ||
    ACTION_LABEL[candidate.action_type] ||
    candidate.action_type
  );
}

type FilterStatus = "pending" | "approved" | "rejected" | "deferred";

export default function OpportunitiesPage() {
  const { siteId, client } = useSiteContext();
  const [candidates, setCandidates] = useState<ActionCandidate[]>([]);
  const [filterStatus, setFilterStatus] = useState<FilterStatus>("pending");
  const [filterRisk, setFilterRisk] = useState<string>("all");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rationale, setRationale] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const rows = await client.listCandidates(siteId, filterStatus);
      setCandidates(rows);
      setSelected(new Set());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "載入失敗");
    } finally {
      setLoading(false);
    }
  }, [client, siteId, filterStatus]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    setSelected(new Set());
  }, [filterRisk, filterStatus]);

  const filtered = useMemo(() => {
    if (filterRisk === "all") return candidates;
    return candidates.filter((c) => c.risk_level === filterRisk);
  }, [candidates, filterRisk]);

  const allSelected = useMemo(
    () => filtered.length > 0 && selected.size === filtered.length,
    [filtered.length, selected.size],
  );

  function toggle(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function toggleAll() {
    if (allSelected) setSelected(new Set());
    else setSelected(new Set(filtered.map((c) => c.id)));
  }

  async function act(action: "approve" | "reject" | "defer", ids: string[]) {
    setBusy(true);
    try {
      for (const id of ids) {
        if (action === "approve") await client.approveCandidate(id, rationale || undefined);
        else if (action === "reject") await client.rejectCandidate(id, rationale || undefined);
        else await client.deferCandidate(id, rationale || undefined);
      }
      setSelected(new Set());
      setRationale("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "操作失敗");
    } finally {
      setBusy(false);
    }
  }

  const statusTabs: FilterStatus[] = ["pending", "approved", "deferred", "rejected"];
  const tabLabel: Record<FilterStatus, string> = {
    pending: "待審核",
    approved: "已核准",
    deferred: "已延期",
    rejected: "已拒絕",
  };

  return (
    <>
      <PageHeader
        title="機會佇列"
        subtitle="審核建議行動，批次 approve / reject / defer"
      />
      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}

      {/* Status tabs */}
      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem", flexWrap: "wrap" }}>
        {statusTabs.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => setFilterStatus(s)}
            style={{
              padding: "0.35rem 0.9rem",
              borderRadius: 999,
              border: "1px solid var(--border)",
              background: filterStatus === s ? "var(--accent)" : "var(--surface-2)",
              color: filterStatus === s ? "#ffffff" : "var(--text)",
              cursor: "pointer",
              font: "inherit",
              fontSize: "0.85rem",
            }}
          >
            {tabLabel[s]}
          </button>
        ))}
        <select
          value={filterRisk}
          onChange={(e) => setFilterRisk(e.target.value)}
          style={{ marginLeft: "auto" }}
        >
          <option value="all">全部風險</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      {/* Batch actions bar */}
      {filterStatus === "pending" && (
        <div className="form-row" style={{ alignItems: "center" }}>
          <button
            type="button"
            className="btn btn-primary"
            disabled={busy || selected.size === 0}
            onClick={() => act("approve", [...selected])}
          >
            批次 Approve ({selected.size})
          </button>
          <button
            type="button"
            className="btn"
            disabled={busy || selected.size === 0}
            onClick={() => act("defer", [...selected])}
          >
            批次 Defer
          </button>
          <button
            type="button"
            className="btn"
            disabled={busy || selected.size === 0}
            onClick={() => act("reject", [...selected])}
          >
            批次 Reject
          </button>
          <input
            placeholder="決策說明（選填）"
            value={rationale}
            onChange={(e) => setRationale(e.target.value)}
            style={{ flex: 1, minWidth: 160 }}
          />
          <button type="button" className="btn" disabled={loading} onClick={load}>
            重新整理
          </button>
        </div>
      )}

      <div className="table-wrap card" style={{ padding: 0 }}>
        <table>
          <thead>
            <tr>
              {filterStatus === "pending" && (
                <th style={{ width: 32 }}>
                  <input
                    type="checkbox"
                    checked={allSelected}
                    onChange={toggleAll}
                    aria-label="全選"
                  />
                </th>
              )}
              <th>關鍵字</th>
              <th>行動類型</th>
              <th>建議行動</th>
              <th style={{ width: 64 }}>分數</th>
              <th>風險</th>
              <th>狀態</th>
              <th>Evidence 摘要</th>
              {filterStatus === "pending" && <th style={{ width: 160 }}>操作</th>}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td
                  colSpan={filterStatus === "pending" ? 9 : 7}
                  style={{ color: "var(--muted)" }}
                >
                  載入中…
                </td>
              </tr>
            ) : filtered.length === 0 ? (
              <tr>
                <td
                  colSpan={filterStatus === "pending" ? 9 : 7}
                  style={{ color: "var(--muted)" }}
                >
                  此狀態下沒有候選行動
                </td>
              </tr>
            ) : (
              filtered.map((row) => (
                <tr key={row.id}>
                  {filterStatus === "pending" && (
                    <td>
                      <input
                        type="checkbox"
                        checked={selected.has(row.id)}
                        onChange={() => toggle(row.id)}
                      />
                    </td>
                  )}
                  <td style={{ fontWeight: 500 }}>{extractKeyword(row)}</td>
                  <td>
                    <code style={{ fontSize: "0.8rem", background: "var(--surface-2)", padding: "0.1rem 0.4rem", borderRadius: 4 }}>
                      {row.action_type}
                    </code>
                  </td>
                  <td style={{ maxWidth: 200 }}>{extractRecommendedAction(row)}</td>
                  <td>
                    <span style={{ fontWeight: 600 }}>{row.rank_score.toFixed(1)}</span>
                  </td>
                  <td>
                    <span className={`badge ${RISK_CLASS[row.risk_level] ?? ""}`}>
                      {row.risk_level}
                    </span>
                  </td>
                  <td>
                    <span className="badge">{row.decision_status}</span>
                  </td>
                  <td>
                    <EvidenceCard evidence={row.evidence_json} />
                  </td>
                  {filterStatus === "pending" && (
                    <td>
                      <div style={{ display: "flex", gap: "0.3rem", flexWrap: "wrap" }}>
                        <button
                          type="button"
                          className="btn btn-primary"
                          style={{ fontSize: "0.8rem", padding: "0.3rem 0.6rem" }}
                          disabled={busy}
                          onClick={() => act("approve", [row.id])}
                        >
                          Approve
                        </button>
                        <button
                          type="button"
                          className="btn"
                          style={{ fontSize: "0.8rem", padding: "0.3rem 0.6rem" }}
                          disabled={busy}
                          onClick={() => act("defer", [row.id])}
                        >
                          Defer
                        </button>
                        <button
                          type="button"
                          className="btn"
                          style={{ fontSize: "0.8rem", padding: "0.3rem 0.6rem" }}
                          disabled={busy}
                          onClick={() => act("reject", [row.id])}
                        >
                          Reject
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
