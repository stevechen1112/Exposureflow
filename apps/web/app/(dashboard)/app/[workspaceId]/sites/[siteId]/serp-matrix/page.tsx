"use client";

import { Fragment, useCallback, useEffect, useState } from "react";
import type { SerpMatrixResponse } from "@exposureflow/shared-types";
import { PageHeader } from "@/components/PageHeader";
import { useSiteContext } from "@/lib/hooks";

const STATUS_ICON: Record<string, string> = {
  achieved: "✓",
  owned: "✓",
  blocked: "✕",
  available: "◯",
};

const STATUS_COLOR: Record<string, string> = {
  achieved: "var(--success)",
  owned: "var(--success)",
  blocked: "var(--danger)",
  available: "var(--muted)",
};

function cellClass(status: string) {
  if (status === "achieved" || status === "owned") return "matrix-owned";
  if (status === "blocked") return "matrix-blocked";
  return "matrix-available";
}

function fmtTime(iso?: string) {
  if (!iso) return "—";
  return new Date(iso as string).toLocaleString("zh-TW", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

type Snapshot = {
  id: string;
  keyword?: string;
  device?: string;
  captured_at?: string;
  serp_json?: Record<string, unknown>;
};

export default function SerpMatrixPage() {
  const { siteId, client } = useSiteContext();
  const [matrix, setMatrix] = useState<SerpMatrixResponse | null>(null);
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [keyword, setKeyword] = useState("");
  const [runningKeyword, setRunningKeyword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [tooltip, setTooltip] = useState<{ kw: string; slot: string; owner?: string } | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [m, s] = await Promise.all([
        client.getSerpMatrix(siteId),
        client.listSerpSnapshots(siteId),
      ]);
      setMatrix(m);
      setSnapshots(s as Snapshot[]);
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

  async function runSnapshot() {
    if (!keyword.trim()) return;
    setRunningKeyword(true);
    setSuccess(null);
    try {
      const res = await client.runSerpSnapshot(siteId, keyword.trim());
      setSuccess(`Snapshot 排程完成（job: ${res.job_run_id.slice(0, 8)}…）`);
      setKeyword("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "執行失敗");
    } finally {
      setRunningKeyword(false);
    }
  }

  if (!matrix && loading) return <p style={{ color: "var(--muted)" }}>載入 SERP 矩陣…</p>;
  if (!matrix) return <p style={{ color: "var(--danger)" }}>{error ?? "無法載入矩陣"}</p>;

  // Summary stats
  const totalCells = matrix.keywords.length * matrix.slot_types.length;
  const ownedCells = matrix.cells.filter(
    (c) => c.status === "achieved" || c.status === "owned",
  ).length;
  const blockedCells = matrix.cells.filter((c) => c.status === "blocked").length;
  const coveragePct = totalCells > 0 ? Math.round((ownedCells / totalCells) * 100) : 0;

  return (
    <>
      <PageHeader title="SERP 矩陣" subtitle="keyword × slot 版位覆蓋視覺化分析" />

      {error ? <p style={{ color: "var(--danger)", marginBottom: "1rem" }}>{error}</p> : null}
      {success ? <p style={{ color: "var(--success)", marginBottom: "1rem" }}>{success}</p> : null}

      {/* Summary KPIs */}
      <div className="kpi-grid" style={{ marginBottom: "1.5rem" }}>
        <div className="card">
          <div className="kpi-label">追蹤關鍵字</div>
          <div className="kpi-value">{matrix.keywords.length}</div>
        </div>
        <div className="card">
          <div className="kpi-label">追蹤版位類型</div>
          <div className="kpi-value">{matrix.slot_types.length}</div>
        </div>
        <div className="card">
          <div className="kpi-label">版位覆蓋率</div>
          <div
            className="kpi-value"
            style={{
              color:
                coveragePct >= 60
                  ? "var(--success)"
                  : coveragePct >= 30
                    ? "var(--warning)"
                    : "var(--danger)",
            }}
          >
            {coveragePct}%
          </div>
          <div style={{ fontSize: "0.78rem", color: "var(--muted)" }}>
            {ownedCells} / {totalCells} 版位
          </div>
        </div>
        {blockedCells > 0 && (
          <div className="card" style={{ borderColor: "var(--danger)" }}>
            <div className="kpi-label">被競品佔領</div>
            <div className="kpi-value" style={{ color: "var(--danger)" }}>
              {blockedCells}
            </div>
          </div>
        )}
      </div>

      {/* Run new snapshot */}
      <div className="form-row" style={{ marginBottom: "1.5rem" }}>
        <input
          placeholder="輸入關鍵字執行 snapshot"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && runSnapshot()}
          style={{ flex: 1, maxWidth: 360 }}
        />
        <button
          type="button"
          className="btn btn-primary"
          disabled={runningKeyword || !keyword.trim()}
          onClick={runSnapshot}
        >
          {runningKeyword ? "排程中…" : "Run Snapshot"}
        </button>
        <button type="button" className="btn" disabled={loading} onClick={load}>
          重新整理
        </button>
      </div>

      {/* Legend */}
      <div style={{ display: "flex", gap: "1rem", marginBottom: "0.75rem", fontSize: "0.82rem" }}>
        <span>
          <span style={{ color: "var(--success)" }}>✓</span> 已覆蓋
        </span>
        <span>
          <span style={{ color: "var(--muted)" }}>◯</span> 可取得
        </span>
        <span>
          <span style={{ color: "var(--danger)" }}>✕</span> 競品佔領
        </span>
      </div>

      {/* Matrix */}
      <div className="card" style={{ overflowX: "auto", marginBottom: "2rem", padding: "1rem" }}>
        <div
          className="matrix-grid"
          style={{
            gridTemplateColumns: `180px repeat(${matrix.slot_types.length}, minmax(80px, 1fr))`,
          }}
        >
          {/* Header row */}
          <div />
          {matrix.slot_types.map((slot) => (
            <div
              key={slot}
              style={{
                fontWeight: 600,
                textAlign: "center",
                fontSize: "0.78rem",
                color: "var(--muted)",
                padding: "0.35rem 0.25rem",
              }}
            >
              {slot}
            </div>
          ))}

          {/* Data rows */}
          {matrix.keywords.map((kw) => (
            <Fragment key={kw}>
              <div
                style={{
                  fontWeight: 500,
                  fontSize: "0.85rem",
                  padding: "0.35rem 0.25rem",
                  display: "flex",
                  alignItems: "center",
                }}
              >
                {kw}
              </div>
              {matrix.slot_types.map((slot) => {
                const cell = matrix.cells.find(
                  (c) => c.keyword === kw && c.slot_type === slot,
                );
                const status = cell?.status ?? "available";
                const isActive = tooltip?.kw === kw && tooltip?.slot === slot;
                return (
                  <div
                    key={`${kw}-${slot}`}
                    className={`matrix-cell ${cellClass(status)}`}
                    style={{ cursor: cell?.owner ? "pointer" : "default", position: "relative" }}
                    onMouseEnter={() => {
                      if (cell?.owner)
                        setTooltip({ kw, slot, owner: cell.owner });
                    }}
                    onMouseLeave={() => setTooltip(null)}
                  >
                    <span
                      style={{
                        fontSize: "1rem",
                        color: STATUS_COLOR[status] ?? "var(--muted)",
                      }}
                    >
                      {STATUS_ICON[status] ?? "—"}
                    </span>
                    {/* Owner tooltip */}
                    {isActive && cell?.owner && (
                      <div
                        style={{
                          position: "absolute",
                          top: "100%",
                          left: "50%",
                          transform: "translateX(-50%)",
                          zIndex: 10,
                          background: "var(--surface)",
                          border: "1px solid var(--border)",
                          borderRadius: 6,
                          padding: "0.3rem 0.6rem",
                          fontSize: "0.75rem",
                          whiteSpace: "nowrap",
                          boxShadow: "0 2px 8px rgba(0,0,0,0.4)",
                          marginTop: 2,
                        }}
                      >
                        <span style={{ color: "var(--muted)" }}>Owner: </span>
                        {cell.owner}
                      </div>
                    )}
                  </div>
                );
              })}
            </Fragment>
          ))}
        </div>
      </div>

      {/* Recent Snapshots */}
      <section>
        <h2 style={{ fontSize: "1rem", marginBottom: "0.75rem" }}>最近 Snapshots</h2>
        <div className="table-wrap card" style={{ padding: 0 }}>
          <table>
            <thead>
              <tr>
                <th>關鍵字</th>
                <th>裝置</th>
                <th>Top 結果</th>
                <th>擷取時間</th>
              </tr>
            </thead>
            <tbody>
              {snapshots.length === 0 ? (
                <tr>
                  <td colSpan={4} style={{ color: "var(--muted)" }}>
                    尚無 snapshot 紀錄
                  </td>
                </tr>
              ) : (
                snapshots.slice(0, 15).map((s) => {
                  const topResults = Array.isArray(s.serp_json?.results)
                    ? (s.serp_json.results as Array<{ url?: string; position?: number }>)
                        .slice(0, 3)
                        .map((r) => `#${r.position ?? "?"} ${(r.url ?? "").slice(0, 40)}`)
                        .join(" · ")
                    : "—";
                  return (
                    <tr key={s.id}>
                      <td style={{ fontWeight: 500 }}>{s.keyword ?? "—"}</td>
                      <td>{s.device ?? "—"}</td>
                      <td style={{ fontSize: "0.78rem", color: "var(--muted)", maxWidth: 320 }}>
                        {topResults}
                      </td>
                      <td
                        style={{
                          fontSize: "0.82rem",
                          color: "var(--muted)",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {fmtTime(s.captured_at)}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
