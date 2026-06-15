"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import type { Site } from "@exposureflow/shared-types";
import { PageHeader } from "@/components/PageHeader";
import { parseApiError } from "@/components/ForbiddenState";
import { getApiClient } from "@/lib/api-client";
import { useWorkspaceAuth } from "@/lib/auth-context";
import { storageKey } from "@/lib/config";
import {
  alternateGscProperty,
  defaultGscProperty,
  diagnoseGscError,
  findGscSyncState,
  findSiteCredential,
  fmtDateTime,
  GSC_SERVICE_ACCOUNT_EMAIL,
  gscPhaseLabel,
  gscPhaseTone,
  resolveGscConnectionPhase,
  type GscCredential,
  type GscSyncState,
} from "@/lib/gsc-connection";

type StepStatus = "done" | "current" | "pending" | "error";

function StepBadge({ status }: { status: StepStatus }) {
  const styles: Record<StepStatus, { bg: string; color: string; label: string }> = {
    done: { bg: "var(--success-soft)", color: "var(--success)", label: "完成" },
    current: { bg: "var(--accent-soft)", color: "var(--accent-text)", label: "進行中" },
    pending: { bg: "var(--surface-2)", color: "var(--muted)", label: "待處理" },
    error: { bg: "var(--danger-soft)", color: "var(--danger)", label: "需修正" },
  };
  const s = styles[status];
  return (
    <span
      style={{
        fontSize: "0.72rem",
        fontWeight: 600,
        padding: "0.15rem 0.5rem",
        borderRadius: 999,
        background: s.bg,
        color: s.color,
        flexShrink: 0,
      }}
    >
      {s.label}
    </span>
  );
}

function toneColor(tone: ReturnType<typeof gscPhaseTone>): string {
  if (tone === "success") return "var(--success)";
  if (tone === "danger") return "var(--danger)";
  if (tone === "warning") return "var(--warning)";
  return "var(--muted)";
}

export default function IntegrationsPage() {
  const params = useParams<{ workspaceId: string }>();
  const { can } = useWorkspaceAuth();
  const canManage = can("integration:write");
  const client = getApiClient(params.workspaceId);

  const [sites, setSites] = useState<Site[]>([]);
  const [siteId, setSiteId] = useState("");
  const [credentials, setCredentials] = useState<GscCredential[]>([]);
  const [syncState, setSyncState] = useState<GscSyncState | undefined>();
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [polling, setPolling] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const activeSite = useMemo(
    () => sites.find((s) => s.id === siteId),
    [sites, siteId],
  );

  const credential = useMemo(
    () => (siteId ? findSiteCredential(credentials, siteId) : undefined),
    [credentials, siteId],
  );

  const phase = resolveGscConnectionPhase({ siteId: siteId || null, credential, syncState });
  const propertyUrl = activeSite?.domain ? defaultGscProperty(activeSite.domain) : "";
  const propertyAlt = activeSite?.domain ? alternateGscProperty(activeSite.domain) : "";
  const diagnosis = diagnoseGscError(syncState?.last_error);

  const loadSiteData = useCallback(
    async (sid: string) => {
      const [creds, states] = await Promise.all([
        client.listIntegrationCredentials(),
        client.listSyncStates(sid),
      ]);
      setCredentials(creds as GscCredential[]);
      setSyncState(findGscSyncState(states as GscSyncState[], sid));
    },
    [client],
  );

  useEffect(() => {
    const stored = localStorage.getItem(storageKey("siteId")) ?? "";
    client
      .listSites()
      .then(async (s) => {
        setSites(s);
        const sid = stored && s.some((x) => x.id === stored) ? stored : (s[0]?.id ?? "");
        setSiteId(sid);
        if (sid) await loadSiteData(sid);
      })
      .catch((err: Error) => setError(parseApiError(err.message).friendly))
      .finally(() => setLoading(false));
  }, [client, loadSiteData]);

  async function handleSiteChange(nextSiteId: string) {
    setSiteId(nextSiteId);
    localStorage.setItem(storageKey("siteId"), nextSiteId);
    setMessage(null);
    setError(null);
    setLoading(true);
    try {
      await loadSiteData(nextSiteId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "載入失敗");
    } finally {
      setLoading(false);
    }
  }

  async function pollSyncResult(sid: string, attempts = 12): Promise<GscSyncState | undefined> {
    setPolling(true);
    let latest: GscSyncState | undefined;
    for (let i = 0; i < attempts; i += 1) {
      await new Promise((r) => setTimeout(r, 5000));
      const states = (await client.listSyncStates(sid)) as GscSyncState[];
      latest = findGscSyncState(states, sid);
      setSyncState(latest);
      if (latest?.last_success_at || latest?.last_error) break;
    }
    setPolling(false);
    return latest;
  }

  async function handleSync() {
    if (!siteId || !activeSite?.domain) return;
    setSyncing(true);
    setMessage(null);
    setError(null);
    try {
      const res = await client.triggerGscSync(siteId, {
        site_url: defaultGscProperty(activeSite.domain),
      });
      setMessage(`已排程 GSC 同步（job ${res.job_run_id.slice(0, 8)}…）`);
      const result = await pollSyncResult(siteId);
      if (result?.last_success_at) {
        setMessage("GSC 同步成功，連線已就緒。");
      } else if (result?.last_error) {
        setError(result.last_error);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "同步失敗");
    } finally {
      setSyncing(false);
    }
  }

  async function copyServiceAccountEmail() {
    try {
      await navigator.clipboard.writeText(GSC_SERVICE_ACCOUNT_EMAIL);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setError("無法複製到剪貼簿，請手動選取 email。");
    }
  }

  const authError = diagnosis?.title.includes("權限") ?? false;

  const step1: StepStatus =
    authError && phase === "sync_error"
      ? "error"
      : syncState?.last_success_at
        ? "done"
        : credential
          ? "current"
          : "pending";

  const step2: StepStatus = credential
    ? "done"
    : phase === "needs_credential"
      ? "current"
      : "pending";

  const step3: StepStatus = syncState?.last_success_at
    ? "done"
    : phase === "sync_error"
      ? "error"
      : credential
        ? "current"
        : "pending";

  const phaseTone = gscPhaseTone(phase);
  const allStepsDone = step1 === "done" && step2 === "done" && step3 === "done";

  return (
    <>
      <PageHeader
        title="Google Search Console 連線"
        subtitle="設定 GSC 授權、credential 與同步——資料分析請至曝光儀表板"
      />

      {message ? (
        <p style={{ color: "var(--success)", marginBottom: "1rem" }}>{message}</p>
      ) : null}
      {error ? (
        <p style={{ color: "var(--danger)", marginBottom: "1rem" }}>{error}</p>
      ) : null}

      <div
        className="card"
        style={{
          marginBottom: "1.25rem",
          display: "flex",
          flexWrap: "wrap",
          gap: "1rem",
          alignItems: "center",
        }}
      >
        <div style={{ flex: "1 1 200px" }}>
          <div style={{ fontSize: "0.82rem", color: "var(--muted)" }}>目前站點</div>
          <div style={{ fontWeight: 600 }}>
            {activeSite?.domain ?? activeSite?.site_name ?? (siteId ? siteId.slice(0, 8) : "—")}
          </div>
        </div>
        <select
          value={siteId}
          onChange={(e) => handleSiteChange(e.target.value)}
          disabled={sites.length === 0 || loading}
          style={{ minWidth: 220 }}
        >
          {sites.length === 0 ? (
            <option value="">尚無站點</option>
          ) : (
            sites.map((s) => (
              <option key={s.id} value={s.id}>
                {s.domain ?? s.site_name ?? s.id.slice(0, 12)}
              </option>
            ))
          )}
        </select>
        {sites.length === 0 ? (
          <Link
            href={`/app/${params.workspaceId}/settings/sites`}
            className="btn btn-primary"
            style={{ fontSize: "0.85rem" }}
          >
            建立站點
          </Link>
        ) : null}
      </div>

      <div
        className="card"
        style={{
          marginBottom: "1.5rem",
          borderColor: toneColor(phaseTone),
          background:
            phase === "connected"
              ? "var(--success-soft)"
              : phase === "sync_error"
                ? "var(--danger-soft)"
                : "var(--surface)",
        }}
      >
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "space-between",
            gap: "1rem",
            alignItems: "flex-start",
          }}
        >
          <div>
            <div style={{ fontSize: "0.82rem", color: "var(--muted)", marginBottom: "0.25rem" }}>
              連線狀態
            </div>
            <div style={{ fontSize: "1.35rem", fontWeight: 700, color: toneColor(phaseTone) }}>
              {loading ? "載入中…" : gscPhaseLabel(phase)}
            </div>
            <p style={{ margin: "0.5rem 0 0", fontSize: "0.88rem", color: "var(--muted)", maxWidth: 520 }}>
              {phase === "connected"
                ? "GSC 串接已完成。曝光、查詢詞等分析請至「曝光儀表板」。"
                : phase === "needs_credential"
                  ? "客戶 GSC 授權完成後，仍需在平台設定 Service Account credential。"
                  : phase === "needs_client_auth"
                    ? "請客戶在 Search Console 加入 Service Account 後再同步。"
                    : phase === "sync_error"
                      ? "最近一次同步失敗，請依下方指引修正。"
                      : "依下方三步驟完成 GSC 連線。"}
            </p>
            {phase === "connected" && siteId ? (
              <Link
                href={`/app/${params.workspaceId}/sites/${siteId}/dashboard`}
                className="btn btn-primary"
                style={{ marginTop: "0.75rem", fontSize: "0.85rem" }}
              >
                前往曝光儀表板
              </Link>
            ) : null}
          </div>
          {propertyUrl ? (
            <div style={{ fontSize: "0.82rem", color: "var(--muted)" }}>
              <div>
                預設 Property：<code style={{ fontSize: "0.8rem" }}>{propertyUrl}</code>
              </div>
              <div style={{ marginTop: "0.25rem" }}>
                備用：<code style={{ fontSize: "0.8rem" }}>{propertyAlt}</code>
              </div>
            </div>
          ) : null}
        </div>

        {syncState ? (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))",
              gap: "0.75rem",
              marginTop: "1rem",
              paddingTop: "1rem",
              borderTop: "1px solid var(--border)",
            }}
          >
            <div>
              <div style={{ fontSize: "0.75rem", color: "var(--muted)" }}>上次成功同步</div>
              <div style={{ fontWeight: 600, fontSize: "0.9rem" }}>
                {fmtDateTime(syncState.last_success_at)}
              </div>
            </div>
            <div>
              <div style={{ fontSize: "0.75rem", color: "var(--muted)" }}>上次嘗試</div>
              <div style={{ fontWeight: 600, fontSize: "0.9rem" }}>
                {fmtDateTime(syncState.last_synced_at)}
              </div>
            </div>
            <div>
              <div style={{ fontSize: "0.75rem", color: "var(--muted)" }}>增量游標</div>
              <div style={{ fontWeight: 600, fontSize: "0.9rem" }}>
                {syncState.cursor_json?.last_synced_date ?? "—"}
              </div>
            </div>
          </div>
        ) : null}
      </div>

      <section style={{ marginBottom: "1.5rem" }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: "0.75rem",
            marginBottom: "0.75rem",
            flexWrap: "wrap",
          }}
        >
          <h2 style={{ fontSize: "1rem", margin: 0 }}>連線三步驟</h2>
          {allStepsDone ? (
            <span style={{ fontSize: "0.82rem", color: "var(--success)", fontWeight: 600 }}>
              全部完成
            </span>
          ) : null}
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          <div className="card">
            <div style={{ display: "flex", gap: "0.75rem", alignItems: "flex-start" }}>
              <div
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: "50%",
                  background: "var(--accent-soft)",
                  color: "var(--accent-text)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontWeight: 700,
                  fontSize: "0.85rem",
                  flexShrink: 0,
                }}
              >
                1
              </div>
              <div style={{ flex: 1 }}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    gap: "0.5rem",
                    flexWrap: "wrap",
                    marginBottom: "0.35rem",
                  }}
                >
                  <div style={{ fontWeight: 600 }}>客戶 GSC 授權</div>
                  <StepBadge status={step1} />
                </div>
                <p style={{ margin: "0 0 0.75rem", fontSize: "0.88rem", color: "var(--muted)" }}>
                  Search Console → 設定 → 使用者與權限 → 新增使用者，權限選「完整」。
                </p>
                <div
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    gap: "0.5rem",
                    alignItems: "center",
                    padding: "0.65rem 0.75rem",
                    background: "var(--surface-2)",
                    borderRadius: 8,
                    fontSize: "0.85rem",
                  }}
                >
                  <code style={{ wordBreak: "break-all" }}>{GSC_SERVICE_ACCOUNT_EMAIL}</code>
                  <button type="button" className="btn" style={{ fontSize: "0.8rem" }} onClick={copyServiceAccountEmail}>
                    {copied ? "已複製" : "複製 Email"}
                  </button>
                  <a
                    href="https://search.google.com/search-console"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn"
                    style={{ fontSize: "0.8rem" }}
                  >
                    開啟 Search Console
                  </a>
                </div>
              </div>
            </div>
          </div>

          <div className="card">
            <div style={{ display: "flex", gap: "0.75rem", alignItems: "flex-start" }}>
              <div
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: "50%",
                  background: "var(--accent-soft)",
                  color: "var(--accent-text)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontWeight: 700,
                  fontSize: "0.85rem",
                  flexShrink: 0,
                }}
              >
                2
              </div>
              <div style={{ flex: 1 }}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    gap: "0.5rem",
                    flexWrap: "wrap",
                    marginBottom: "0.35rem",
                  }}
                >
                  <div style={{ fontWeight: 600 }}>平台 Credential</div>
                  <StepBadge status={step2} />
                </div>
                {credential ? (
                  <div style={{ fontSize: "0.85rem" }}>
                    <span className="badge" style={{ marginRight: "0.5rem" }}>
                      {credential.status}
                    </span>
                    <span style={{ color: "var(--muted)" }}>
                      {credential.credential_type} · {credential.credential_name}
                    </span>
                  </div>
                ) : (
                  <p style={{ margin: 0, fontSize: "0.85rem", color: "var(--warning)" }}>
                    尚未設定。測試階段由工程上傳 Service Account JSON。
                  </p>
                )}
              </div>
            </div>
          </div>

          <div className="card">
            <div style={{ display: "flex", gap: "0.75rem", alignItems: "flex-start" }}>
              <div
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: "50%",
                  background: "var(--accent-soft)",
                  color: "var(--accent-text)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontWeight: 700,
                  fontSize: "0.85rem",
                  flexShrink: 0,
                }}
              >
                3
              </div>
              <div style={{ flex: 1 }}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    gap: "0.5rem",
                    flexWrap: "wrap",
                    marginBottom: "0.35rem",
                  }}
                >
                  <div style={{ fontWeight: 600 }}>觸發 GSC 同步</div>
                  <StepBadge status={step3} />
                </div>
                <p style={{ margin: "0 0 0.75rem", fontSize: "0.88rem", color: "var(--muted)" }}>
                  同步 job 成功即代表串接完成；不需在此頁檢視曝光數據。
                </p>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
                  {canManage ? (
                    <button
                      type="button"
                      className="btn btn-primary"
                      disabled={!siteId || !credential || syncing || polling || loading}
                      onClick={handleSync}
                    >
                      {syncing || polling ? "同步中…" : "立即同步"}
                    </button>
                  ) : (
                    <p style={{ margin: 0, fontSize: "0.85rem", color: "var(--muted)" }}>
                      您的角色無法觸發同步。
                    </p>
                  )}
                  <Link
                    href={`/app/${params.workspaceId}/onboarding`}
                    className="btn"
                    style={{ fontSize: "0.85rem" }}
                  >
                    Onboarding
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {(phase === "sync_error" || syncState?.last_error) && diagnosis ? (
        <section style={{ marginBottom: "1.5rem" }}>
          <h2 style={{ fontSize: "1rem", marginBottom: "0.75rem" }}>疑難排解</h2>
          <div className="card" style={{ borderColor: "var(--danger)" }}>
            <div style={{ fontWeight: 600, marginBottom: "0.5rem", color: "var(--danger)" }}>
              {diagnosis.title}
            </div>
            <ul style={{ margin: "0 0 0.75rem", paddingLeft: "1.25rem", fontSize: "0.88rem" }}>
              {diagnosis.actions.map((action) => (
                <li key={action} style={{ marginBottom: "0.25rem" }}>
                  {action}
                </li>
              ))}
            </ul>
            {syncState?.last_error ? (
              <pre
                style={{
                  margin: 0,
                  padding: "0.75rem",
                  background: "var(--surface-2)",
                  borderRadius: 8,
                  fontSize: "0.78rem",
                  overflowX: "auto",
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                }}
              >
                {syncState.last_error}
              </pre>
            ) : null}
          </div>
        </section>
      ) : null}

      <section>
        <div
          className="card"
          style={{ background: "var(--surface-2)", borderStyle: "dashed", fontSize: "0.85rem", color: "var(--muted)" }}
        >
          <strong style={{ color: "var(--text)" }}>此頁 vs 曝光儀表板</strong>
          <p style={{ margin: "0.5rem 0 0" }}>
            本頁只負責 GSC 串接（授權、credential、同步狀態）。曝光、查詢詞、排名等分析一律在「曝光儀表板」查看。
          </p>
        </div>
      </section>
    </>
  );
}
