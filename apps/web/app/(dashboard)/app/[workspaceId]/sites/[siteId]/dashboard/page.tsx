"use client";

import { useEffect, useState } from "react";
import type { ExposureDashboardMetrics } from "@exposureflow/shared-types";
import { KpiCard } from "@/components/KpiCard";
import { PageHeader } from "@/components/PageHeader";
import { useSiteContext } from "@/lib/hooks";

const RANGE_OPTIONS = [
  { label: "7 天", days: 7 },
  { label: "28 天", days: 28 },
  { label: "90 天", days: 90 },
];

type TopicRow = {
  id: string;
  name: string;
  total_impressions: number;
  coverage_score: number;
  ai_visibility_score: number;
  status: string;
};

const CLUSTER_STATUS_CLASS: Record<string, string> = {
  active: "",
  gap: "badge-high",
  cannibalized: "badge-critical",
  planned: "",
};

function HealthBadge({ value, label }: { value: number; label: string }) {
  const color =
    value === 0 ? "var(--success)" : value <= 2 ? "var(--warning)" : "var(--danger)";
  return (
    <div className="card" style={{ borderColor: value > 0 ? color : "var(--border)" }}>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value" style={{ color: value > 0 ? color : undefined }}>
        {value}
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { siteId, client } = useSiteContext();
  const [data, setData] = useState<ExposureDashboardMetrics | null>(null);
  const [range, setRange] = useState(28);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    client
      .getDashboard(siteId, range)
      .then((d) => {
        setData(d);
        setError(null);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [client, siteId, range]);

  if (error) return <p style={{ color: "var(--danger)" }}>{error}</p>;
  if (!data && loading) return <p style={{ color: "var(--muted)" }}>載入儀表板…</p>;
  if (!data) return null;

  const delta = data.impressions_delta_pct;

  return (
    <>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          flexWrap: "wrap",
          gap: "1rem",
          marginBottom: "1.5rem",
        }}
      >
        <PageHeader
          title="曝光儀表板"
          subtitle="自然曝光版圖、SERP 版位、AI 引用與待處理機會"
        />
        <div style={{ display: "flex", gap: "0.4rem", alignItems: "center", marginTop: "0.5rem" }}>
          <span style={{ fontSize: "0.82rem", color: "var(--muted)" }}>時間範圍</span>
          {RANGE_OPTIONS.map((opt) => (
            <button
              key={opt.days}
              type="button"
              onClick={() => setRange(opt.days)}
              style={{
                padding: "0.3rem 0.7rem",
                borderRadius: 999,
                border: "1px solid var(--border)",
                background: range === opt.days ? "var(--accent)" : "var(--surface-2)",
                color: "var(--text)",
                cursor: "pointer",
                font: "inherit",
                fontSize: "0.82rem",
              }}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Primary metrics */}
      <div className="kpi-grid" style={{ marginBottom: "1.5rem" }}>
        <div className="card">
          <div className="kpi-label">{range} 天自然曝光</div>
          <div className="kpi-value">{data.total_impressions.toLocaleString()}</div>
          <div
            className={delta >= 0 ? "delta-up" : "delta-down"}
            style={{ fontSize: "0.9rem", marginTop: "0.25rem" }}
          >
            {delta >= 0 ? "▲" : "▼"} {Math.abs(delta)}% MoM
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--muted)", marginTop: "0.3rem" }}>
            來源：Google Search Console
          </div>
        </div>

        <KpiCard
          label="查詢覆蓋"
          value={data.query_coverage_count}
          note={`本站出現在 ${data.query_coverage_count.toLocaleString()} 個不同搜尋詞`}
        />
        <KpiCard
          label="已索引資產"
          value={data.indexed_asset_count}
          note="Google 已索引的頁面數"
        />
      </div>

      {/* SERP ranking breakdown */}
      <div style={{ marginBottom: "1.5rem" }}>
        <h2 style={{ fontSize: "1rem", marginBottom: "0.75rem", color: "var(--muted)" }}>
          排名分佈
        </h2>
        <div className="kpi-grid">
          <div className="card">
            <div className="kpi-label">Top 3 查詢</div>
            <div className="kpi-value" style={{ color: "var(--success)" }}>
              {data.top_3_count.toLocaleString()}
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--muted)" }}>排名 1–3（高點擊率）</div>
          </div>
          <div className="card">
            <div className="kpi-label">Top 10 查詢</div>
            <div className="kpi-value">{data.top_10_count.toLocaleString()}</div>
            <div style={{ fontSize: "0.75rem", color: "var(--muted)" }}>排名 4–10（首頁）</div>
          </div>
          <div className="card">
            <div className="kpi-label">Top 20 查詢</div>
            <div className="kpi-value" style={{ color: "var(--muted)" }}>
              {data.top_20_count.toLocaleString()}
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--muted)" }}>排名 11–20（第二頁）</div>
          </div>
          <div className="card">
            <div className="kpi-label">SERP 版位達成</div>
            <div className="kpi-value" style={{ color: "var(--accent)" }}>
              {data.serp_slot_count.toLocaleString()}
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--muted)" }}>已確認取得的特殊版位</div>
          </div>
          <div className="card">
            <div className="kpi-label">AI 引用</div>
            <div className="kpi-value" style={{ color: "var(--accent)" }}>
              {data.ai_citation_count.toLocaleString()}
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--muted)" }}>AI 平台上提及本站 URL</div>
          </div>
        </div>
      </div>

      {/* Action items */}
      <div style={{ marginBottom: "1.5rem" }}>
        <h2 style={{ fontSize: "1rem", marginBottom: "0.75rem", color: "var(--muted)" }}>
          待處理事項
        </h2>
        <div className="kpi-grid">
          <HealthBadge value={data.open_opportunity_count} label="Open 機會" />
          <HealthBadge value={data.critical_blocker_count} label="Critical 技術阻擋" />
        </div>
      </div>

      {/* Topic Cluster Performance */}
      <section>
        <h2 style={{ fontSize: "1rem", marginBottom: "0.75rem" }}>
          Topic Cluster 表現
          <span style={{ fontSize: "0.82rem", color: "var(--muted)", marginLeft: "0.5rem" }}>
            （覆蓋分數 0–100，AI 能見度 0–100）
          </span>
        </h2>
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
                    尚無 topic cluster 資料，請完成 GSC sync 後刷新
                  </td>
                </tr>
              ) : (
                (data.topic_cluster_performance as TopicRow[])
                  .sort((a, b) => b.total_impressions - a.total_impressions)
                  .map((row) => (
                    <tr key={row.id}>
                      <td style={{ fontWeight: 500 }}>{row.name}</td>
                      <td>{row.total_impressions.toLocaleString()}</td>
                      <td>
                        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                          <div
                            style={{
                              width: 60,
                              height: 6,
                              background: "var(--surface-2)",
                              borderRadius: 999,
                              overflow: "hidden",
                            }}
                          >
                            <div
                              style={{
                                width: `${Math.min(100, row.coverage_score)}%`,
                                height: "100%",
                                background:
                                  row.coverage_score > 60
                                    ? "var(--success)"
                                    : row.coverage_score > 30
                                      ? "var(--warning)"
                                      : "var(--danger)",
                                borderRadius: 999,
                              }}
                            />
                          </div>
                          <span style={{ fontSize: "0.82rem" }}>
                            {row.coverage_score.toFixed(1)}
                          </span>
                        </div>
                      </td>
                      <td>
                        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                          <div
                            style={{
                              width: 60,
                              height: 6,
                              background: "var(--surface-2)",
                              borderRadius: 999,
                              overflow: "hidden",
                            }}
                          >
                            <div
                              style={{
                                width: `${Math.min(100, row.ai_visibility_score)}%`,
                                height: "100%",
                                background: "var(--accent)",
                                borderRadius: 999,
                              }}
                            />
                          </div>
                          <span style={{ fontSize: "0.82rem" }}>
                            {row.ai_visibility_score.toFixed(1)}
                          </span>
                        </div>
                      </td>
                      <td>
                        <span className={`badge ${CLUSTER_STATUS_CLASS[row.status] ?? ""}`}>
                          {row.status}
                        </span>
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
