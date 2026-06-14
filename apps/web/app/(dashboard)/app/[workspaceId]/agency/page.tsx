"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { PageHeader } from "@/components/PageHeader";
import { getApiClient } from "@/lib/api-client";

type ClientRow = {
  workspace_id: string;
  name: string;
  client_name: string | null;
  total_impressions: number;
  impressions_delta_pct: number;
  open_opportunities: number;
  ready_reports: number;
  serp_snapshots_used: number;
};

export default function AgencyDashboardPage() {
  const params = useParams<{ workspaceId: string }>();
  const client = getApiClient(params.workspaceId);
  const [data, setData] = useState<{
    client_workspaces: ClientRow[];
    workspace_count: number;
    plan_limits: Record<string, unknown>;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    client
      .getAgencyDashboard()
      .then((payload) =>
        setData({
          client_workspaces: (payload.client_workspaces as ClientRow[]) ?? [],
          workspace_count: Number(payload.workspace_count ?? 0),
          plan_limits: (payload.plan_limits as Record<string, unknown>) ?? {},
        })
      )
      .catch((err: Error) => setError(err.message));
  }, [client]);

  return (
    <>
      <PageHeader
        title="Agency 總覽"
        subtitle="跨客戶工作區曝光、報告與 SERP 用量摘要"
      />
      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}
      {data ? (
        <>
          <p style={{ marginBottom: "1rem" }}>
            帳戶工作區 {data.workspace_count} · 白標{" "}
            {data.plan_limits.white_label_enabled ? "已啟用" : "未啟用"}
          </p>
          <div className="table-wrap card" style={{ padding: 0 }}>
            <table>
              <thead>
                <tr>
                  <th>客戶工作區</th>
                  <th>曝光</th>
                  <th>成長 %</th>
                  <th>開放機會</th>
                  <th>報告</th>
                  <th>SERP 用量</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {data.client_workspaces.map((row) => (
                  <tr key={row.workspace_id}>
                    <td>
                      {row.client_name || row.name}
                      <div style={{ fontSize: "0.8rem", color: "var(--muted)" }}>{row.name}</div>
                    </td>
                    <td>{row.total_impressions.toLocaleString()}</td>
                    <td>{row.impressions_delta_pct.toFixed(1)}%</td>
                    <td>{row.open_opportunities}</td>
                    <td>{row.ready_reports}</td>
                    <td>{row.serp_snapshots_used}</td>
                    <td>
                      <Link href={`/app/${row.workspace_id}/settings`}>開啟</Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : null}
    </>
  );
}
