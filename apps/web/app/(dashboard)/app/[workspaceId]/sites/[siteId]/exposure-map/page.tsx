"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { useSiteContext } from "@/lib/hooks";

export default function ExposureMapPage() {
  const { siteId, client } = useSiteContext();
  const [clusters, setClusters] = useState<Array<Record<string, unknown>>>([]);
  const [selectedCluster, setSelectedCluster] = useState<string>("");
  const [nodes, setNodes] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    client
      .listTopicClusters(siteId)
      .then(setClusters)
      .catch((err: Error) => setError(err.message));
  }, [client, siteId]);

  useEffect(() => {
    client
      .listTopicNodes(siteId, selectedCluster || undefined)
      .then(setNodes)
      .catch((err: Error) => setError(err.message));
  }, [client, siteId, selectedCluster]);

  return (
    <>
      <PageHeader title="曝光地圖" subtitle="Topic cluster 與節點覆蓋一覽" />
      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}
      <div className="form-row">
        <select value={selectedCluster} onChange={(e) => setSelectedCluster(e.target.value)}>
          <option value="">全部 cluster</option>
          {clusters.map((c) => (
            <option key={String(c.id)} value={String(c.id)}>
              {String(c.name)}
            </option>
          ))}
        </select>
      </div>
      <div className="kpi-grid" style={{ marginBottom: "1.5rem" }}>
        {clusters.slice(0, 6).map((c) => (
          <div key={String(c.id)} className="card">
            <div className="kpi-label">{String(c.name)}</div>
            <div className="kpi-value">{Number(c.total_impressions ?? 0).toLocaleString()}</div>
            <div style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
              覆蓋 {Number(c.coverage_score ?? 0).toFixed(1)} · AI {Number(c.ai_visibility_score ?? 0).toFixed(1)}
            </div>
          </div>
        ))}
      </div>
      <div className="table-wrap card" style={{ padding: 0 }}>
        <table>
          <thead>
            <tr>
              <th>節點</th>
              <th>URL / Query</th>
              <th>曝光</th>
              <th>狀態</th>
            </tr>
          </thead>
          <tbody>
            {nodes.length === 0 ? (
              <tr>
                <td colSpan={4} style={{ color: "var(--muted)" }}>
                  尚無 topic node
                </td>
              </tr>
            ) : (
              nodes.map((n) => (
                <tr key={String(n.id)}>
                  <td>{String(n.label ?? n.primary_keyword ?? "")}</td>
                  <td style={{ maxWidth: 320, wordBreak: "break-all" }}>{String(n.canonical_url ?? n.query ?? "")}</td>
                  <td>{Number(n.impressions ?? 0).toLocaleString()}</td>
                  <td>
                    <span className="badge">{String(n.status ?? "")}</span>
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
