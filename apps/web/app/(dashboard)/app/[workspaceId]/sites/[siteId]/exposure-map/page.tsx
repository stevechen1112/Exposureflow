"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { useSiteContext } from "@/lib/hooks";

type TopicCluster = {
  id: string;
  name: string;
  total_impressions?: number;
  coverage_score?: number;
  ai_visibility_score?: number;
  status?: string;
  cluster_type?: string;
};

type TopicNode = {
  id: string;
  label?: string;
  primary_keyword?: string;
  canonical_url?: string;
  query?: string;
  impressions?: number;
  status?: string;
  node_type?: string;
  coverage_gap?: boolean;
};

const CLUSTER_STATUS_CLASS: Record<string, string> = {
  active: "",
  gap: "badge-high",
  cannibalized: "badge-critical",
  planned: "",
};

const NODE_TYPE_CLASS: Record<string, string> = {
  pillar: "badge",
  spoke: "badge",
  gap: "badge-high",
  cannibalization: "badge-critical",
};

const NODE_TYPE_LABEL: Record<string, string> = {
  pillar: "核心主題",
  spoke: "子主題",
  gap: "覆蓋缺口",
  cannibalization: "搶量競爭",
};

function ScoreBar({ value, max = 100 }: { value: number; max?: number }) {
  const pct = Math.min(100, (value / max) * 100);
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "0.4rem",
      }}
    >
      <div
        style={{
          flex: 1,
          height: 6,
          background: "var(--surface-2)",
          borderRadius: 999,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${pct}%`,
            height: "100%",
            background: pct > 60 ? "var(--success)" : pct > 30 ? "var(--warning)" : "var(--danger)",
            borderRadius: 999,
          }}
        />
      </div>
      <span style={{ fontSize: "0.78rem", width: 36, textAlign: "right", color: "var(--muted)" }}>
        {value.toFixed(1)}
      </span>
    </div>
  );
}

export default function ExposureMapPage() {
  const { siteId, client } = useSiteContext();
  const [clusters, setClusters] = useState<TopicCluster[]>([]);
  const [selectedClusterId, setSelectedClusterId] = useState<string>("");
  const [nodes, setNodes] = useState<TopicNode[]>([]);
  const [nodeTypeFilter, setNodeTypeFilter] = useState<string>("all");
  const [nodeStatusFilter, setNodeStatusFilter] = useState<string>("all");
  const [error, setError] = useState<string | null>(null);
  const [loadingClusters, setLoadingClusters] = useState(true);
  const [loadingNodes, setLoadingNodes] = useState(false);

  const loadClusters = useCallback(async () => {
    setLoadingClusters(true);
    try {
      const rows = await client.listTopicClusters(siteId);
      setClusters(rows as TopicCluster[]);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "載入失敗");
    } finally {
      setLoadingClusters(false);
    }
  }, [client, siteId]);

  const loadNodes = useCallback(async () => {
    setLoadingNodes(true);
    try {
      const rows = await client.listTopicNodes(siteId, selectedClusterId || undefined);
      setNodes(rows as TopicNode[]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "載入節點失敗");
    } finally {
      setLoadingNodes(false);
    }
  }, [client, siteId, selectedClusterId]);

  useEffect(() => {
    loadClusters();
  }, [loadClusters]);

  useEffect(() => {
    loadNodes();
  }, [loadNodes]);

  const filteredNodes = useMemo(() => {
    return nodes.filter((n) => {
      const typeOk = nodeTypeFilter === "all" || n.node_type === nodeTypeFilter;
      const statusOk = nodeStatusFilter === "all" || n.status === nodeStatusFilter;
      return typeOk && statusOk;
    });
  }, [nodes, nodeTypeFilter, nodeStatusFilter]);

  const gapCount = nodes.filter((n) => n.node_type === "gap" || n.coverage_gap).length;
  const totalImpressions = clusters.reduce((sum, c) => sum + (c.total_impressions ?? 0), 0);

  const selectedCluster = clusters.find((c) => c.id === selectedClusterId);

  return (
    <>
      <PageHeader title="曝光地圖" subtitle="Topic cluster 覆蓋版圖、節點類型與缺口分析" />
      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}

      {/* Summary KPIs */}
      {!loadingClusters && clusters.length > 0 && (
        <div className="kpi-grid" style={{ marginBottom: "1.5rem" }}>
          <div className="card">
            <div className="kpi-label">Topic Clusters</div>
            <div className="kpi-value">{clusters.length}</div>
          </div>
          <div className="card">
            <div className="kpi-label">總曝光</div>
            <div className="kpi-value">{totalImpressions.toLocaleString()}</div>
          </div>
          <div className="card">
            <div className="kpi-label">節點數</div>
            <div className="kpi-value">{nodes.length}</div>
          </div>
          {gapCount > 0 && (
            <div className="card" style={{ borderColor: "var(--warning)" }}>
              <div className="kpi-label">覆蓋缺口</div>
              <div className="kpi-value" style={{ color: "var(--warning)" }}>
                {gapCount}
              </div>
              <div style={{ fontSize: "0.78rem", color: "var(--muted)" }}>待補充主題</div>
            </div>
          )}
        </div>
      )}

      {/* Cluster list — all with scrollable grid */}
      <section style={{ marginBottom: "1.5rem" }}>
        <h2 style={{ fontSize: "1rem", marginBottom: "0.75rem" }}>
          Topic Clusters
          <span style={{ fontSize: "0.82rem", color: "var(--muted)", marginLeft: "0.5rem" }}>
            點選篩選節點
          </span>
        </h2>
        {loadingClusters ? (
          <p style={{ color: "var(--muted)" }}>載入中…</p>
        ) : (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
              gap: "0.75rem",
            }}
          >
            <div
              className="card"
              style={{
                cursor: "pointer",
                borderColor: selectedClusterId === "" ? "var(--accent)" : "var(--border)",
                transition: "border-color 0.15s",
              }}
              onClick={() => setSelectedClusterId("")}
            >
              <div className="kpi-label">全部節點</div>
              <div style={{ fontWeight: 600, fontSize: "1.1rem" }}>{nodes.length} 個</div>
            </div>
            {clusters.map((c) => (
              <div
                key={c.id}
                className="card"
                style={{
                  cursor: "pointer",
                  borderColor:
                    selectedClusterId === c.id ? "var(--accent)" : "var(--border)",
                  transition: "border-color 0.15s",
                }}
                onClick={() => setSelectedClusterId(c.id)}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                    marginBottom: "0.4rem",
                  }}
                >
                  <div className="kpi-label" style={{ maxWidth: "80%" }}>
                    {c.name}
                  </div>
                  <span className={`badge ${CLUSTER_STATUS_CLASS[c.status ?? ""] ?? ""}`}>
                    {c.status ?? "—"}
                  </span>
                </div>
                <div style={{ fontWeight: 600, fontSize: "1rem" }}>
                  {(c.total_impressions ?? 0).toLocaleString()}
                  <span style={{ fontSize: "0.75rem", color: "var(--muted)", marginLeft: "0.25rem" }}>
                    曝光
                  </span>
                </div>
                <div style={{ marginTop: "0.4rem" }}>
                  <div style={{ fontSize: "0.75rem", color: "var(--muted)", marginBottom: "0.15rem" }}>
                    覆蓋
                  </div>
                  <ScoreBar value={c.coverage_score ?? 0} />
                </div>
                <div style={{ marginTop: "0.35rem" }}>
                  <div style={{ fontSize: "0.75rem", color: "var(--muted)", marginBottom: "0.15rem" }}>
                    AI 能見度
                  </div>
                  <ScoreBar value={c.ai_visibility_score ?? 0} />
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Node table */}
      <section>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.75rem",
            marginBottom: "0.75rem",
            flexWrap: "wrap",
          }}
        >
          <h2 style={{ fontSize: "1rem", margin: 0 }}>
            節點列表
            {selectedCluster && (
              <span style={{ color: "var(--accent)", marginLeft: "0.5rem" }}>
                — {selectedCluster.name}
              </span>
            )}
          </h2>
          <select
            value={nodeTypeFilter}
            onChange={(e) => setNodeTypeFilter(e.target.value)}
          >
            <option value="all">全部類型</option>
            <option value="pillar">核心主題</option>
            <option value="spoke">子主題</option>
            <option value="gap">覆蓋缺口</option>
            <option value="cannibalization">搶量競爭</option>
          </select>
          <select
            value={nodeStatusFilter}
            onChange={(e) => setNodeStatusFilter(e.target.value)}
          >
            <option value="all">全部狀態</option>
            <option value="active">Active</option>
            <option value="planned">Planned</option>
            <option value="gap">Gap</option>
          </select>
          <span style={{ fontSize: "0.82rem", color: "var(--muted)", marginLeft: "auto" }}>
            顯示 {filteredNodes.length} / {nodes.length} 個節點
          </span>
        </div>
        <div className="table-wrap card" style={{ padding: 0 }}>
          <table>
            <thead>
              <tr>
                <th>節點 / 關鍵字</th>
                <th>類型</th>
                <th>URL</th>
                <th>曝光</th>
                <th>狀態</th>
              </tr>
            </thead>
            <tbody>
              {loadingNodes ? (
                <tr>
                  <td colSpan={5} style={{ color: "var(--muted)" }}>
                    載入中…
                  </td>
                </tr>
              ) : filteredNodes.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ color: "var(--muted)" }}>
                    此篩選條件下無節點
                  </td>
                </tr>
              ) : (
                filteredNodes.map((n) => (
                  <tr key={n.id}>
                    <td style={{ fontWeight: 500 }}>
                      {n.label ?? n.primary_keyword ?? "—"}
                    </td>
                    <td>
                      {n.node_type ? (
                        <span className={NODE_TYPE_CLASS[n.node_type] ?? "badge"}>
                          {NODE_TYPE_LABEL[n.node_type] ?? n.node_type}
                        </span>
                      ) : (
                        <span style={{ color: "var(--muted)" }}>—</span>
                      )}
                    </td>
                    <td
                      style={{
                        maxWidth: 280,
                        wordBreak: "break-all",
                        fontSize: "0.8rem",
                        color: "var(--muted)",
                      }}
                    >
                      {n.canonical_url ?? n.query ?? "—"}
                    </td>
                    <td>{(n.impressions ?? 0).toLocaleString()}</td>
                    <td>
                      <span className="badge">{n.status ?? "—"}</span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
