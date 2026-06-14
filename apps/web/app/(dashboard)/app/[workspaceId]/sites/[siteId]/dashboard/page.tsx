"use client";

import { useEffect, useState } from "react";
import type { ExposureDashboardMetrics } from "@exposureflow/shared-types";
import { KpiCard } from "@/components/KpiCard";
import { PageHeader } from "@/components/PageHeader";
import { useSiteContext } from "@/lib/hooks";

export default function DashboardPage() {
  const { siteId, client } = useSiteContext();
  const [data, setData] = useState<ExposureDashboardMetrics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    client
      .getDashboard(siteId)
      .then(setData)
      .catch((err: Error) => setError(err.message));
  }, [client, siteId]);

  if (error) return <p style={{ color: "var(--danger)" }}>{error}</p>;
  if (!data) return <p style={{ color: "var(--muted)" }}>載入儀表板…</p>;

  return (
    <>
      <PageHeader
        title="曝光儀表板"
        subtitle="一覽自然曝光版圖、版位與待處理機會"
      />
      <div className="kpi-grid">
        <KpiCard label="28 天自然曝光" value={data.total_impressions.toLocaleString()} delta={data.impressions_delta_pct} />
        <KpiCard label="查詢覆蓋" value={data.query_coverage_count} />
        <KpiCard label="已索引資產" value={data.indexed_asset_count} />
        <KpiCard label="Top 3 查詢" value={data.top_3_count} />
        <KpiCard label="Top 10 查詢" value={data.top_10_count} />
        <KpiCard label="Top 20 查詢" value={data.top_20_count} />
        <KpiCard label="SERP 版位達成" value={data.serp_slot_count} />
        <KpiCard label="AI 引用" value={data.ai_citation_count} />
        <KpiCard label="Open 機會" value={data.open_opportunity_count} />
        <KpiCard label="Critical 技術阻擋" value={data.critical_blocker_count} />
      </div>

      <section style={{ marginTop: "2rem" }}>
        <h2 style={{ fontSize: "1.1rem", marginBottom: "0.75rem" }}>Topic Cluster 表現</h2>
        <div className="table-wrap card" style={{ padding: 0 }}>
          <table>
            <thead>
              <tr>
                <th>主題群</th>
                <th>曝光</th>
                <th>覆蓋分數</th>
                <th>AI 能見度</th>
                <th>狀態</th>
              </tr>
            </thead>
            <tbody>
              {data.topic_cluster_performance.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ color: "var(--muted)" }}>
                    尚無 topic cluster 資料
                  </td>
                </tr>
              ) : (
                data.topic_cluster_performance.map((row) => (
                  <tr key={row.id}>
                    <td>{row.name}</td>
                    <td>{row.total_impressions.toLocaleString()}</td>
                    <td>{row.coverage_score.toFixed(1)}</td>
                    <td>{row.ai_visibility_score.toFixed(1)}</td>
                    <td>
                      <span className="badge">{row.status}</span>
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
