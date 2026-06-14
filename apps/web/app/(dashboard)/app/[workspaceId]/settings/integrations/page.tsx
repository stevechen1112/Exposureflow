"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import type { Site } from "@exposureflow/shared-types";
import { PageHeader } from "@/components/PageHeader";
import { parseApiError } from "@/components/ForbiddenState";
import { getApiClient } from "@/lib/api-client";
import { useWorkspaceAuth } from "@/lib/auth-context";
import { storageKey } from "@/lib/config";

type SyncState = {
  provider: string;
  site_id: string;
  last_synced_at?: string;
  last_success_at?: string;
  last_error?: string;
  status?: string;
};

const PROVIDER_LABEL: Record<string, string> = {
  gsc: "Google Search Console",
  ga4: "Google Analytics 4",
  wordpress: "WordPress",
  tech_seo: "Tech SEO Crawler",
  serp: "SERP Snapshot",
};

const PROVIDER_DESC: Record<string, string> = {
  gsc: "搜尋效能資料、曝光、點擊率",
  ga4: "流量、轉換、使用者行為",
  wordpress: "內容發布與同步",
  tech_seo: "頁面技術 SEO 問題偵測",
  serp: "關鍵字排名與版位快照",
};

function fmtTime(iso?: string) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString("zh-TW", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function StatusDot({ error, synced }: { error?: string; synced?: string }) {
  if (error) return <span style={{ color: "var(--danger)", fontSize: "0.85rem" }}>● 錯誤</span>;
  if (synced) return <span style={{ color: "var(--success)", fontSize: "0.85rem" }}>● 正常</span>;
  return <span style={{ color: "var(--muted)", fontSize: "0.85rem" }}>○ 未同步</span>;
}

export default function IntegrationsPage() {
  const params = useParams<{ workspaceId: string }>();
  const { can } = useWorkspaceAuth();
  const canTriggerSync = can("integration:write");
  const client = getApiClient(params.workspaceId);
  const [syncStates, setSyncStates] = useState<SyncState[]>([]);
  const [sites, setSites] = useState<Site[]>([]);
  const [siteId, setSiteId] = useState<string>("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState<string | null>(null);

  useEffect(() => {
    const sid = localStorage.getItem(storageKey("siteId")) ?? "";
    setSiteId(sid);
    Promise.all([client.listSites(), client.listSyncStates(sid || undefined)])
      .then(([s, states]) => {
        setSites(s);
        setSyncStates(states as SyncState[]);
      })
      .catch((err: Error) => {
        const parsed = parseApiError(err.message);
        setError(parsed.friendly);
      })
      .finally(() => setLoading(false));
  }, [client]);

  const siteMap = useMemo(() => {
    const map: Record<string, string> = {};
    for (const s of sites) {
      map[s.id] = s.domain ?? s.site_name ?? s.id.slice(0, 8);
    }
    return map;
  }, [sites]);

  const resolvedSite = siteMap[siteId] ?? siteId;

  async function handleSync(provider: "gsc" | "tech_seo") {
    if (!siteId) return;
    setSyncing(provider);
    setMessage(null);
    try {
      if (provider === "gsc") {
        const res = await client.triggerGscSync(siteId);
        setMessage(`GSC sync 已排程（job: ${res.job_run_id.slice(0, 8)}…）`);
      } else {
        const res = await client.triggerTechSeoCrawl(siteId);
        setMessage(`Tech SEO crawl 已排程（job: ${res.job_run_id.slice(0, 8)}…）`);
      }
      const states = await client.listSyncStates(siteId || undefined);
      setSyncStates(states as SyncState[]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "同步失敗");
    } finally {
      setSyncing(null);
    }
  }

  // Group known providers to always show them (even without sync history)
  const knownProviders = ["gsc", "ga4", "wordpress", "tech_seo"];
  const syncMap = useMemo(() => {
    const map: Record<string, SyncState> = {};
    for (const s of syncStates) {
      map[s.provider] = s;
    }
    return map;
  }, [syncStates]);

  return (
    <>
      <PageHeader
        title="整合設定"
        subtitle={
          canTriggerSync
            ? "資料源連接狀態、手動同步觸發與整合管理"
            : "資料源連接狀態（唯讀；同步操作需整合管理權限）"
        }
      />

      {message ? (
        <p style={{ color: "var(--success)", marginBottom: "1rem" }}>{message}</p>
      ) : null}
      {error ? (
        <p style={{ color: "var(--danger)", marginBottom: "1rem" }}>{error}</p>
      ) : null}

      {/* Current site context */}
      {siteId && (
        <div
          className="card"
          style={{ marginBottom: "1.5rem", display: "flex", alignItems: "center", gap: "0.75rem" }}
        >
          <div>
            <div style={{ fontSize: "0.82rem", color: "var(--muted)" }}>目前站點</div>
            <div style={{ fontWeight: 600 }}>{resolvedSite}</div>
          </div>
          <select
            value={siteId}
            onChange={(e) => {
              const newSid = e.target.value;
              setSiteId(newSid);
              localStorage.setItem(storageKey("siteId"), newSid);
            }}
            style={{ marginLeft: "auto" }}
          >
            {sites.map((s) => (
              <option key={s.id} value={s.id}>
                {s.domain ?? s.site_name ?? s.id.slice(0, 12)}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Provider cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
          gap: "1rem",
          marginBottom: "2rem",
        }}
      >
        {knownProviders.map((provider) => {
          const state = syncMap[provider];
          const providerSyncable = provider === "gsc" || provider === "tech_seo";
          return (
            <div key={provider} className="card">
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "flex-start",
                  marginBottom: "0.5rem",
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, marginBottom: "0.15rem" }}>
                    {PROVIDER_LABEL[provider] ?? provider}
                  </div>
                  <div style={{ fontSize: "0.8rem", color: "var(--muted)" }}>
                    {PROVIDER_DESC[provider] ?? ""}
                  </div>
                </div>
                <StatusDot
                  error={state?.last_error}
                  synced={state?.last_success_at}
                />
              </div>
              {state ? (
                <div style={{ fontSize: "0.82rem", color: "var(--muted)", marginTop: "0.5rem" }}>
                  <div>上次同步：{fmtTime(state.last_synced_at)}</div>
                  <div>上次成功：{fmtTime(state.last_success_at)}</div>
                  {state.last_error && (
                    <div style={{ color: "var(--danger)", marginTop: "0.25rem" }}>
                      錯誤：{state.last_error.slice(0, 80)}
                    </div>
                  )}
                </div>
              ) : (
                <div
                  style={{
                    fontSize: "0.82rem",
                    color: "var(--muted)",
                    marginTop: "0.5rem",
                  }}
                >
                  尚未同步
                </div>
              )}
              {canTriggerSync && providerSyncable && (
                <button
                  type="button"
                  className="btn btn-primary"
                  style={{ marginTop: "0.75rem", width: "100%", fontSize: "0.85rem" }}
                  disabled={!siteId || syncing === provider}
                  onClick={() => handleSync(provider as "gsc" | "tech_seo")}
                >
                  {syncing === provider ? "同步中…" : `觸發 ${PROVIDER_LABEL[provider]?.split(" ")[0]} 同步`}
                </button>
              )}
              {!canTriggerSync && providerSyncable && (
                <p style={{ marginTop: "0.75rem", fontSize: "0.82rem", color: "var(--muted)" }}>
                  您的角色無法觸發同步，請聯絡管理員。
                </p>
              )}
              {!providerSyncable && (
                <button
                  type="button"
                  className="btn"
                  style={{ marginTop: "0.75rem", width: "100%", fontSize: "0.85rem" }}
                  disabled
                >
                  設定連線（待實作）
                </button>
              )}
            </div>
          );
        })}
      </div>

      {/* Sync history table */}
      <section>
        <h2 style={{ fontSize: "1rem", marginBottom: "0.75rem" }}>同步歷史記錄</h2>
        <div className="table-wrap card" style={{ padding: 0 }}>
          <table>
            <thead>
              <tr>
                <th>Provider</th>
                <th>站點</th>
                <th>狀態</th>
                <th>上次同步</th>
                <th>上次成功</th>
                <th>最近錯誤</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} style={{ color: "var(--muted)" }}>
                    載入中…
                  </td>
                </tr>
              ) : syncStates.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ color: "var(--muted)" }}>
                    尚無同步記錄
                  </td>
                </tr>
              ) : (
                syncStates.map((s, i) => (
                  <tr key={`${s.provider}-${i}`}>
                    <td style={{ fontWeight: 500 }}>
                      {PROVIDER_LABEL[s.provider] ?? s.provider}
                    </td>
                    <td style={{ fontSize: "0.85rem" }}>
                      {siteMap[s.site_id] ?? s.site_id.slice(0, 12)}
                    </td>
                    <td>
                      <StatusDot
                        error={s.last_error}
                        synced={s.last_success_at}
                      />
                    </td>
                    <td style={{ fontSize: "0.82rem", color: "var(--muted)" }}>
                      {fmtTime(s.last_synced_at)}
                    </td>
                    <td style={{ fontSize: "0.82rem", color: "var(--muted)" }}>
                      {fmtTime(s.last_success_at)}
                    </td>
                    <td
                      style={{
                        color: s.last_error ? "var(--danger)" : "var(--muted)",
                        fontSize: "0.82rem",
                        maxWidth: 240,
                      }}
                    >
                      {s.last_error ? s.last_error.slice(0, 80) : "—"}
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
