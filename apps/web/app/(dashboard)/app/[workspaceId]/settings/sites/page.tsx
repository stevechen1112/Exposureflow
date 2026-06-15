"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import type { Site, Workspace } from "@exposureflow/shared-types";
import { PageHeader } from "@/components/PageHeader";
import { parseApiError } from "@/components/ForbiddenState";
import { RequirePermission } from "@/components/WorkspaceGuard";
import { getApiClient } from "@/lib/api-client";
import { storageKey } from "@/lib/config";
import { useWorkspaceAuth } from "@/lib/auth-context";
import {
  EMPTY_SITE_FORM,
  formValuesToPayload,
  siteToFormValues,
  type SiteFormValues,
} from "@/lib/site-form";

function splitCsvHint() {
  return "多個值以逗號分隔，例如 TW 或 zh-TW";
}

export default function SitesSettingsPage() {
  const params = useParams<{ workspaceId: string }>();
  const { can } = useWorkspaceAuth();
  const client = getApiClient(params.workspaceId);

  const [sites, setSites] = useState<Site[]>([]);
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [siteLimit, setSiteLimit] = useState<number | null>(null);
  const [activeSiteId, setActiveSiteId] = useState<string | null>(null);
  const [createForm, setCreateForm] = useState<SiteFormValues>(EMPTY_SITE_FORM);
  const [editId, setEditId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<SiteFormValues>(EMPTY_SITE_FORM);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);

  const canWrite = can("site:write");

  const load = useCallback(async () => {
    const [siteRows, workspaces] = await Promise.all([client.listSites(), client.listWorkspaces()]);
    setSites(siteRows);
    const ws = workspaces.find((w) => w.id === params.workspaceId) ?? workspaces[0] ?? null;
    setWorkspace(ws);
    const limits = ws?.plan_limits;
    setSiteLimit(
      typeof limits?.site_limit === "number"
        ? limits.site_limit
        : typeof limits?.sites === "number"
          ? limits.sites
          : null,
    );
    const stored = localStorage.getItem(storageKey("siteId"));
    setActiveSiteId(stored && siteRows.some((s) => s.id === stored) ? stored : siteRows[0]?.id ?? null);
  }, [client, params.workspaceId]);

  useEffect(() => {
    load()
      .catch((err: Error) => setError(parseApiError(err.message).friendly))
      .finally(() => setLoading(false));
  }, [load]);

  function selectActiveSite(siteId: string) {
    localStorage.setItem(storageKey("siteId"), siteId);
    setActiveSiteId(siteId);
    setSuccess("已設為目前分析站點");
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!canWrite) return;
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      const payload = formValuesToPayload(createForm);
      const site = await client.createSite(payload);
      localStorage.setItem(storageKey("siteId"), site.id);
      setActiveSiteId(site.id);
      setCreateForm(EMPTY_SITE_FORM);
      setSuccess(`已建立站點 ${site.site_name}（${site.domain}）`);
      await load();
    } catch (err) {
      setError(parseApiError(err instanceof Error ? err.message : "建立失敗").friendly);
    } finally {
      setBusy(false);
    }
  }

  function startEdit(site: Site) {
    setEditId(site.id);
    setEditForm(siteToFormValues(site));
    setError(null);
    setSuccess(null);
  }

  async function handleUpdate(e: React.FormEvent) {
    e.preventDefault();
    if (!canWrite || !editId) return;
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      const site = await client.updateSite(editId, formValuesToPayload(editForm));
      if (activeSiteId === editId) {
        localStorage.setItem(storageKey("siteId"), site.id);
      }
      setEditId(null);
      setSuccess(`已更新站點 ${site.site_name}`);
      await load();
    } catch (err) {
      setError(parseApiError(err instanceof Error ? err.message : "更新失敗").friendly);
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return <p style={{ color: "var(--muted)" }}>載入站點…</p>;
  }

  const atLimit = siteLimit !== null && sites.length >= siteLimit;

  return (
    <RequirePermission permission="site:read" workspaceId={params.workspaceId}>
      <PageHeader
        title="站點管理"
        subtitle="為此工作區新增或編輯要分析的客戶網站（domain、名稱、市場設定）"
      />

      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}
      {success ? <p style={{ color: "var(--success)" }}>{success}</p> : null}

      <div className="card" style={{ marginBottom: "1.25rem" }}>
        <p style={{ margin: 0, fontSize: "0.9rem" }}>
          工作區：<strong>{workspace?.name ?? params.workspaceId.slice(0, 8)}</strong>
          {workspace?.workspace_type ? (
            <span style={{ color: "var(--muted)" }}> · {workspace.workspace_type}</span>
          ) : null}
        </p>
        <p style={{ margin: "0.5rem 0 0", fontSize: "0.85rem", color: "var(--muted)" }}>
          已建立 {sites.length}
          {siteLimit !== null ? ` / 上限 ${siteLimit}` : ""} 個站點
          {activeSiteId ? (
            <>
              {" "}
              · 目前分析站點 ID：<code style={{ fontSize: "0.8rem" }}>{activeSiteId.slice(0, 8)}…</code>
            </>
          ) : null}
        </p>
      </div>

      {canWrite && !atLimit ? (
        <form className="card" onSubmit={handleCreate} style={{ marginBottom: "1.5rem" }}>
          <h2 style={{ fontSize: "1rem", marginTop: 0 }}>新增站點</h2>
          <SiteFormFields values={createForm} onChange={setCreateForm} disabled={busy} />
          <button type="submit" className="btn btn-primary" disabled={busy} style={{ marginTop: "0.75rem" }}>
            {busy ? "建立中…" : "建立站點"}
          </button>
        </form>
      ) : null}

      {canWrite && atLimit ? (
        <p className="card" style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
          已達目前方案站點上限。請編輯現有站點，或聯絡營運調整方案配額。
        </p>
      ) : null}

      <section>
        <h2 style={{ fontSize: "1rem", marginBottom: "0.75rem" }}>站點列表</h2>
        {sites.length === 0 ? (
          <div className="card">
            <p style={{ margin: 0, color: "var(--muted)" }}>
              尚無站點。{canWrite ? "請使用上方表單建立第一個客戶網站。" : "請聯絡工作區管理員建立站點。"}
            </p>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {sites.map((site) => (
              <div key={site.id} className="card">
                <div
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    gap: "0.75rem",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 600, fontSize: "1.05rem" }}>{site.site_name}</div>
                    <div style={{ color: "var(--accent-text)", fontSize: "0.9rem" }}>{site.domain}</div>
                    <div style={{ fontSize: "0.8rem", color: "var(--muted)", marginTop: "0.35rem" }}>
                      {site.industry ? `${site.industry} · ` : ""}
                      {site.business_model ?? "—"}
                      {activeSiteId === site.id ? (
                        <span style={{ marginLeft: "0.5rem", color: "var(--success)" }}>● 目前站點</span>
                      ) : null}
                    </div>
                  </div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
                    <button
                      type="button"
                      className="btn"
                      onClick={() => selectActiveSite(site.id)}
                      disabled={activeSiteId === site.id}
                    >
                      設為目前站點
                    </button>
                    <Link
                      href={`/app/${params.workspaceId}/sites/${site.id}/dashboard`}
                      className="btn btn-primary"
                      onClick={() => localStorage.setItem(storageKey("siteId"), site.id)}
                    >
                      開啟儀表板
                    </Link>
                    {canWrite ? (
                      <button type="button" className="btn" onClick={() => startEdit(site)}>
                        編輯
                      </button>
                    ) : null}
                  </div>
                </div>

                {editId === site.id ? (
                  <form onSubmit={handleUpdate} style={{ marginTop: "1rem", borderTop: "1px solid var(--border)", paddingTop: "1rem" }}>
                    <SiteFormFields values={editForm} onChange={setEditForm} disabled={busy} />
                    <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.75rem" }}>
                      <button type="submit" className="btn btn-primary" disabled={busy}>
                        {busy ? "儲存中…" : "儲存變更"}
                      </button>
                      <button type="button" className="btn" onClick={() => setEditId(null)}>
                        取消
                      </button>
                    </div>
                  </form>
                ) : null}
              </div>
            ))}
          </div>
        )}
      </section>

      {sites.length > 0 ? (
        <p style={{ marginTop: "1.25rem", fontSize: "0.85rem", color: "var(--muted)" }}>
          下一步：{" "}
          <Link href={`/app/${params.workspaceId}/onboarding`}>Onboarding 檢查</Link>
          {" · "}
          <Link href={`/app/${params.workspaceId}/settings/integrations`}>GSC 連線</Link>
        </p>
      ) : null}
    </RequirePermission>
  );
}

function SiteFormFields({
  values,
  onChange,
  disabled,
}: {
  values: SiteFormValues;
  onChange: (next: SiteFormValues) => void;
  disabled?: boolean;
}) {
  const set = (key: keyof SiteFormValues, value: string) => onChange({ ...values, [key]: value });

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
        gap: "0.75rem",
      }}
    >
      <label>
        <span style={{ display: "block", fontSize: "0.82rem", color: "var(--muted)", marginBottom: "0.25rem" }}>
          網域 *
        </span>
        <input
          required
          value={values.domain}
          onChange={(e) => set("domain", e.target.value)}
          placeholder="ezfix.com.tw"
          disabled={disabled}
          style={{ width: "100%" }}
        />
      </label>
      <label>
        <span style={{ display: "block", fontSize: "0.82rem", color: "var(--muted)", marginBottom: "0.25rem" }}>
          站點名稱 *
        </span>
        <input
          required
          value={values.site_name}
          onChange={(e) => set("site_name", e.target.value)}
          placeholder="恆惠修理紗窗"
          disabled={disabled}
          style={{ width: "100%" }}
        />
      </label>
      <label>
        <span style={{ display: "block", fontSize: "0.82rem", color: "var(--muted)", marginBottom: "0.25rem" }}>
          主要語系
        </span>
        <input
          value={values.primary_locale}
          onChange={(e) => set("primary_locale", e.target.value)}
          disabled={disabled}
          style={{ width: "100%" }}
        />
      </label>
      <label>
        <span style={{ display: "block", fontSize: "0.82rem", color: "var(--muted)", marginBottom: "0.25rem" }}>
          目標國家
        </span>
        <input
          value={values.target_countries}
          onChange={(e) => set("target_countries", e.target.value)}
          placeholder="TW"
          disabled={disabled}
          style={{ width: "100%" }}
        />
        <span style={{ fontSize: "0.75rem", color: "var(--muted)" }}>{splitCsvHint()}</span>
      </label>
      <label>
        <span style={{ display: "block", fontSize: "0.82rem", color: "var(--muted)", marginBottom: "0.25rem" }}>
          目標語言
        </span>
        <input
          value={values.target_languages}
          onChange={(e) => set("target_languages", e.target.value)}
          placeholder="zh-TW"
          disabled={disabled}
          style={{ width: "100%" }}
        />
      </label>
      <label>
        <span style={{ display: "block", fontSize: "0.82rem", color: "var(--muted)", marginBottom: "0.25rem" }}>
          產業
        </span>
        <input
          value={values.industry}
          onChange={(e) => set("industry", e.target.value)}
          placeholder="本地居家維修"
          disabled={disabled}
          style={{ width: "100%" }}
        />
      </label>
      <label>
        <span style={{ display: "block", fontSize: "0.82rem", color: "var(--muted)", marginBottom: "0.25rem" }}>
          商業模式
        </span>
        <input
          value={values.business_model}
          onChange={(e) => set("business_model", e.target.value)}
          placeholder="到府服務、電話詢價"
          disabled={disabled}
          style={{ width: "100%" }}
        />
      </label>
    </div>
  );
}
