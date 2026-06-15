"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { useSiteContext } from "@/lib/hooks";

type TopicCluster = {
  id: string;
  name: string;
  pillar_keyword: string;
  total_impressions?: number;
  coverage_score?: number;
  authority_score?: number;
  status?: string;
};

type TopicNode = {
  id: string;
  keyword: string;
  keyword_level: string;
  current_best_url?: string | null;
  impressions?: number;
  avg_position?: number | null;
  status?: string;
  topic_cluster_id?: string;
};

const CLUSTER_STATUS_CLASS: Record<string, string> = {
  active: "",
  planned: "",
  building: "badge-high",
  complete: "",
};

const NODE_STATUS_CLASS: Record<string, string> = {
  covered: "",
  gap: "badge-high",
  cannibalized: "badge-critical",
  stale: "badge-high",
  blocked: "badge-critical",
};

const KEYWORD_LEVEL_LABEL: Record<string, string> = {
  head: "核心大字",
  mid_tail: "中階字",
  long_tail: "長尾字",
};

export default function ExposureMapPage() {
  const { siteId, client } = useSiteContext();
  const [clusters, setClusters] = useState<TopicCluster[]>([]);
  const [selectedClusterId, setSelectedClusterId] = useState<string>("");
  const [nodes, setNodes] = useState<TopicNode[]>([]);
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
    return nodes.filter((n) => nodeStatusFilter === "all" || n.status === nodeStatusFilter);
  }, [nodes, nodeStatusFilter]);

  const gapCount = nodes.filter((n) => n.status === "gap").length;
  const totalImpressions = clusters.reduce((sum, c) => sum + (c.total_impressions ?? 0), 0);
  const selectedCluster = clusters.find((c) => c.id === selectedClusterId);

  return (
    <>
      <PageHeader
        title="曝光地圖"
        subtitle="Topic cluster 覆蓋版圖；與 Keyword Pyramid 核准節點透過 sync-topic-bridge 連結"
      />
      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}

      {!loadingClusters && clusters.length > 0 && (
        <div className="kpi-grid" style={{ marginBottom: "1.5rem" }}>
          <div className="card">
            <div className="kpi-label">Topic Clusters</div>
            <div className="kpi-value">{clusters.length}</div>
          </div>
          <div className="card">
            <div className="kpi-label">覆蓋缺口</div>
            <div className="kpi-value">{gapCount}</div>
          </div>
          <div className="card">
            <div className="kpi-label">總曝光（GSC）</div>
            <div className="kpi-value">{totalImpressions.toLocaleString()}</div>
          </div>
        </div>
      )}

      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <label style={{ display: "grid", gap: "0.35rem", maxWidth: 420 }}>
          <span style={{ color: "var(--muted)", fontSize: "0.9rem" }}>Topic Cluster</span>
          <select
            className="input"
            value={selectedClusterId}
            onChange={(e) => setSelectedClusterId(e.target.value)}
          >
            <option value="">全部 clusters</option>
            {clusters.map((cluster) => (
              <option key={cluster.id} value={cluster.id}>
                {cluster.name}（{cluster.pillar_keyword}）
              </option>
            ))}
          </select>
        </label>
        {selectedCluster ? (
          <p style={{ margin: "0.75rem 0 0", color: "var(--muted)", fontSize: "0.88rem" }}>
            Pillar：{selectedCluster.pillar_keyword} · Coverage {selectedCluster.coverage_score ?? 0} ·
            Authority {selectedCluster.authority_score ?? 0}
          </p>
        ) : null}
      </div>

      <div className="card">
        <div style={{ display: "flex", gap: "0.75rem", alignItems: "center", marginBottom: "0.75rem" }}>
          <span style={{ color: "var(--muted)", fontSize: "0.9rem" }}>節點狀態</span>
          <select
            className="input"
            style={{ maxWidth: 180 }}
            value={nodeStatusFilter}
            onChange={(e) => setNodeStatusFilter(e.target.value)}
          >
            <option value="all">全部</option>
            <option value="covered">已覆蓋</option>
            <option value="gap">缺口</option>
            <option value="cannibalized">蠶食</option>
            <option value="stale">過時</option>
          </select>
        </div>

        {loadingNodes ? <p style={{ color: "var(--muted)" }}>載入節點中…</p> : null}
        {!loadingNodes && filteredNodes.length === 0 ? (
          <p style={{ color: "var(--muted)" }}>沒有符合條件的 topic nodes。</p>
        ) : null}

        {!loadingNodes && filteredNodes.length > 0 ? (
          <div className="table-wrap" style={{ padding: 0 }}>
            <table>
              <thead>
                <tr>
                  <th>關鍵字</th>
                  <th>層級</th>
                  <th>狀態</th>
                  <th>曝光</th>
                  <th>平均排名</th>
                  <th>最佳 URL</th>
                </tr>
              </thead>
              <tbody>
                {filteredNodes.map((node) => (
                  <tr key={node.id}>
                    <td>{node.keyword}</td>
                    <td>{KEYWORD_LEVEL_LABEL[node.keyword_level] ?? node.keyword_level}</td>
                    <td>
                      <span className={NODE_STATUS_CLASS[node.status ?? ""] ?? "badge"}>
                        {node.status ?? "—"}
                      </span>
                    </td>
                    <td>{node.impressions?.toLocaleString() ?? 0}</td>
                    <td>{node.avg_position != null ? node.avg_position.toFixed(1) : "—"}</td>
                    <td style={{ maxWidth: 280, overflow: "hidden", textOverflow: "ellipsis" }}>
                      {node.current_best_url ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>
    </>
  );
}
