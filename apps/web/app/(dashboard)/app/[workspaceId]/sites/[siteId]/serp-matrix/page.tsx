"use client";

import { Fragment, useEffect, useState } from "react";
import type { SerpMatrixResponse } from "@exposureflow/shared-types";
import { PageHeader } from "@/components/PageHeader";
import { useSiteContext } from "@/lib/hooks";

function cellClass(status: string) {
  if (status === "achieved" || status === "owned") return "matrix-owned";
  if (status === "blocked") return "matrix-blocked";
  return "matrix-available";
}

export default function SerpMatrixPage() {
  const { siteId, client } = useSiteContext();
  const [matrix, setMatrix] = useState<SerpMatrixResponse | null>(null);
  const [snapshots, setSnapshots] = useState<Array<Record<string, unknown>>>([]);
  const [keyword, setKeyword] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([client.getSerpMatrix(siteId), client.listSerpSnapshots(siteId)])
      .then(([m, s]) => {
        setMatrix(m);
        setSnapshots(s);
      })
      .catch((err: Error) => setError(err.message));
  }, [client, siteId]);

  async function runSnapshot() {
    if (!keyword.trim()) return;
    try {
      await client.runSerpSnapshot(siteId, keyword.trim());
      const s = await client.listSerpSnapshots(siteId);
      setSnapshots(s);
      setKeyword("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "執行失敗");
    }
  }

  if (error) return <p style={{ color: "var(--danger)" }}>{error}</p>;
  if (!matrix) return <p style={{ color: "var(--muted)" }}>載入 SERP 矩陣…</p>;

  return (
    <>
      <PageHeader title="SERP 矩陣" subtitle="keyword × slot 覆蓋視覺化" />
      <div className="form-row">
        <input
          placeholder="輸入關鍵字執行 snapshot"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
        />
        <button type="button" className="btn btn-primary" onClick={runSnapshot}>
          Run Snapshot
        </button>
      </div>
      <div className="card" style={{ overflowX: "auto" }}>
        <div
          className="matrix-grid"
          style={{
            gridTemplateColumns: `120px repeat(${matrix.slot_types.length}, minmax(72px, 1fr))`,
          }}
        >
          <div />
          {matrix.slot_types.map((slot) => (
            <div key={slot} style={{ fontWeight: 600, textAlign: "center" }}>
              {slot}
            </div>
          ))}
          {matrix.keywords.map((kw) => (
            <Fragment key={kw}>
              <div style={{ fontWeight: 500 }}>{kw}</div>
              {matrix.slot_types.map((slot) => {
                const cell = matrix.cells.find((c) => c.keyword === kw && c.slot_type === slot);
                const status = cell?.status ?? "available";
                return (
                  <div key={`${kw}-${slot}`} className={`matrix-cell ${cellClass(status)}`} title={cell?.owner}>
                    {status}
                  </div>
                );
              })}
            </Fragment>
          ))}
        </div>
      </div>
      <section style={{ marginTop: "2rem" }}>
        <h2 style={{ fontSize: "1.1rem" }}>最近 Snapshots</h2>
        <div className="table-wrap card" style={{ padding: 0 }}>
          <table>
            <thead>
              <tr>
                <th>關鍵字</th>
                <th>裝置</th>
                <th>擷取時間</th>
              </tr>
            </thead>
            <tbody>
              {snapshots.slice(0, 10).map((s) => (
                <tr key={String(s.id)}>
                  <td>{String(s.keyword ?? "")}</td>
                  <td>{String(s.device ?? "")}</td>
                  <td>{String(s.captured_at ?? "")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
