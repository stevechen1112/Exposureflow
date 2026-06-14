"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { PageHeader } from "@/components/PageHeader";
import { getApiClient } from "@/lib/api-client";
import { storageKey } from "@/lib/config";

export default function IntegrationsPage() {
  const params = useParams<{ workspaceId: string }>();
  const client = getApiClient(params.workspaceId);
  const [syncStates, setSyncStates] = useState<Array<Record<string, unknown>>>([]);
  const [siteId, setSiteId] = useState<string>("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const sid = localStorage.getItem(storageKey("siteId")) ?? "";
    setSiteId(sid);
    client.listSyncStates(sid || undefined).then(setSyncStates).catch((err: Error) => setError(err.message));
  }, [client]);

  async function syncGsc() {
    if (!siteId) return;
    try {
      const res = await client.triggerGscSync(siteId);
      setMessage(`GSC sync 已排程：${res.job_run_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "同步失敗");
    }
  }

  async function crawlTech() {
    if (!siteId) return;
    try {
      const res = await client.triggerTechSeoCrawl(siteId);
      setMessage(`Tech SEO crawl 已排程：${res.job_run_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Crawl 失敗");
    }
  }

  return (
    <>
      <PageHeader title="整合" subtitle="資料源同步狀態與手動觸發" />
      {message ? <p style={{ color: "var(--success)" }}>{message}</p> : null}
      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}
      <div className="form-row">
        <button type="button" className="btn btn-primary" onClick={syncGsc} disabled={!siteId}>
          觸發 GSC Sync
        </button>
        <button type="button" className="btn" onClick={crawlTech} disabled={!siteId}>
          觸發 Tech SEO Crawl
        </button>
      </div>
      <div className="table-wrap card" style={{ padding: 0 }}>
        <table>
          <thead>
            <tr>
              <th>Provider</th>
              <th>Site</th>
              <th>上次同步</th>
              <th>上次成功</th>
              <th>錯誤</th>
            </tr>
          </thead>
          <tbody>
            {syncStates.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ color: "var(--muted)" }}>
                  尚無 sync state
                </td>
              </tr>
            ) : (
              syncStates.map((s, i) => (
                <tr key={`${String(s.provider)}-${i}`}>
                  <td>{String(s.provider ?? "")}</td>
                  <td>{String(s.site_id ?? "")}</td>
                  <td>{String(s.last_synced_at ?? "—")}</td>
                  <td>{String(s.last_success_at ?? "—")}</td>
                  <td style={{ color: "var(--danger)" }}>{String(s.last_error ?? "—")}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
