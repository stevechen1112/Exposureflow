"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { PageHeader } from "@/components/PageHeader";
import { parseApiError } from "@/components/ForbiddenState";
import { RequirePermission } from "@/components/WorkspaceGuard";
import { getApiClient, resetApiClientCache } from "@/lib/api-client";
import { storageKey } from "@/lib/config";
import { useWorkspaceAuth } from "@/lib/auth-context";

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
  const router = useRouter();
  const { can } = useWorkspaceAuth();
  const client = getApiClient(params.workspaceId);
  const [data, setData] = useState<{
    client_workspaces: ClientRow[];
    workspace_count: number;
    plan_limits: Record<string, unknown>;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [clientName, setClientName] = useState("");
  const [workspaceName, setWorkspaceName] = useState("");

  const load = useCallback(async () => {
    const payload = await client.getAgencyDashboard();
    setData({
      client_workspaces: (payload.client_workspaces as ClientRow[]) ?? [],
      workspace_count: Number(payload.workspace_count ?? 0),
      plan_limits: (payload.plan_limits as Record<string, unknown>) ?? {},
    });
  }, [client]);

  useEffect(() => {
    load().catch((err: Error) => setError(parseApiError(err.message).friendly));
  }, [load]);

  async function createClientWorkspace(e: React.FormEvent) {
    e.preventDefault();
    if (!can("workspace:write")) return;
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      const ws = await client.createWorkspace({
        name: workspaceName.trim(),
        workspace_type: "client",
        client_name: clientName.trim() || workspaceName.trim(),
        default_locale: "zh-TW",
      });
      resetApiClientCache();
      localStorage.setItem(storageKey("workspaceId"), ws.id);
      localStorage.removeItem(storageKey("siteId"));
      setSuccess(`已建立客戶工作區「${ws.name}」。請接著在站點管理新增 domain。`);
      setClientName("");
      setWorkspaceName("");
      router.push(`/app/${ws.id}/settings/sites`);
    } catch (err) {
      setError(parseApiError(err instanceof Error ? err.message : "建立失敗").friendly);
    } finally {
      setBusy(false);
    }
  }

  return (
    <RequirePermission permission="agency:read" workspaceId={params.workspaceId}>
      <PageHeader
        title="Agency 總覽"
        subtitle="跨客戶工作區曝光、報告與 SERP 用量摘要"
      />
      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}
      {success ? <p style={{ color: "var(--success)" }}>{success}</p> : null}

      {can("workspace:write") ? (
        <form className="card" onSubmit={createClientWorkspace} style={{ marginBottom: "1.5rem" }}>
          <h2 style={{ fontSize: "1rem", marginTop: 0 }}>建立客戶工作區</h2>
          <p style={{ fontSize: "0.85rem", color: "var(--muted)", marginTop: 0 }}>
            簽約後在此建立 client workspace，再到該工作區的「站點管理」新增 ezfix.com.tw 等 domain。
          </p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem", alignItems: "flex-end" }}>
            <label style={{ flex: "1 1 200px" }}>
              <span style={{ display: "block", fontSize: "0.82rem", color: "var(--muted)", marginBottom: "0.25rem" }}>
                工作區名稱 *
              </span>
              <input
                required
                value={workspaceName}
                onChange={(e) => setWorkspaceName(e.target.value)}
                placeholder="恆惠修理紗窗"
                style={{ width: "100%" }}
              />
            </label>
            <label style={{ flex: "1 1 200px" }}>
              <span style={{ display: "block", fontSize: "0.82rem", color: "var(--muted)", marginBottom: "0.25rem" }}>
                客戶顯示名稱
              </span>
              <input
                value={clientName}
                onChange={(e) => setClientName(e.target.value)}
                placeholder="恆惠修理紗窗"
                style={{ width: "100%" }}
              />
            </label>
            <button type="submit" className="btn btn-primary" disabled={busy}>
              {busy ? "建立中…" : "建立並前往站點管理"}
            </button>
          </div>
        </form>
      ) : null}

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
                      <Link href={`/app/${row.workspace_id}/settings/sites`}>站點</Link>
                      {" · "}
                      <Link href={`/app/${row.workspace_id}/onboarding`}>Onboarding</Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : null}
    </RequirePermission>
  );
}
