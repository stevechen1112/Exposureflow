"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { ActionCandidate } from "@exposureflow/shared-types";
import { PageHeader } from "@/components/PageHeader";
import { useSiteContext } from "@/lib/hooks";

export default function OpportunitiesPage() {
  const { siteId, client } = useSiteContext();
  const [candidates, setCandidates] = useState<ActionCandidate[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const rows = await client.listCandidates(siteId, "pending");
      setCandidates(rows);
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

  const allSelected = useMemo(
    () => candidates.length > 0 && selected.size === candidates.length,
    [candidates.length, selected.size],
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
    else setSelected(new Set(candidates.map((c) => c.id)));
  }

  async function act(action: "approve" | "reject" | "defer", ids: string[]) {
    setBusy(true);
    try {
      for (const id of ids) {
        if (action === "approve") await client.approveCandidate(id);
        else if (action === "reject") await client.rejectCandidate(id);
        else await client.deferCandidate(id);
      }
      setSelected(new Set());
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "操作失敗");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHeader
        title="機會佇列"
        subtitle="審核建議行動：approve / reject / defer，支援批次操作"
      />
      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}
      <div className="form-row">
        <button type="button" className="btn btn-primary" disabled={busy || selected.size === 0} onClick={() => act("approve", [...selected])}>
          批次 Approve ({selected.size})
        </button>
        <button type="button" className="btn" disabled={busy || selected.size === 0} onClick={() => act("defer", [...selected])}>
          批次 Defer
        </button>
        <button type="button" className="btn" disabled={busy || selected.size === 0} onClick={() => act("reject", [...selected])}>
          批次 Reject
        </button>
        <button type="button" className="btn" disabled={loading} onClick={load}>
          重新整理
        </button>
      </div>
      <div className="table-wrap card" style={{ padding: 0 }}>
        <table>
          <thead>
            <tr>
              <th>
                <input type="checkbox" checked={allSelected} onChange={toggleAll} aria-label="全選" />
              </th>
              <th>類型</th>
              <th>分數</th>
              <th>風險</th>
              <th>狀態</th>
              <th>Evidence</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} style={{ color: "var(--muted)" }}>
                  載入中…
                </td>
              </tr>
            ) : candidates.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ color: "var(--muted)" }}>
                  目前沒有待審核候選行動
                </td>
              </tr>
            ) : (
              candidates.map((row) => (
                <tr key={row.id}>
                  <td>
                    <input type="checkbox" checked={selected.has(row.id)} onChange={() => toggle(row.id)} />
                  </td>
                  <td>{row.action_type}</td>
                  <td>{row.rank_score.toFixed(1)}</td>
                  <td>
                    <span className={`badge ${row.risk_level === "high" ? "badge-high" : ""}`}>{row.risk_level}</span>
                  </td>
                  <td>{row.decision_status}</td>
                  <td style={{ maxWidth: 280, fontSize: "0.8rem" }}>
                    <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>{JSON.stringify(row.evidence_json, null, 0)}</pre>
                  </td>
                  <td>
                    <div style={{ display: "flex", gap: "0.35rem", flexWrap: "wrap" }}>
                      <button type="button" className="btn btn-primary" disabled={busy} onClick={() => act("approve", [row.id])}>
                        Approve
                      </button>
                      <button type="button" className="btn" disabled={busy} onClick={() => act("defer", [row.id])}>
                        Defer
                      </button>
                      <button type="button" className="btn" disabled={busy} onClick={() => act("reject", [row.id])}>
                        Reject
                      </button>
                    </div>
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
