/* eslint-disable @typescript-eslint/ban-ts-comment */
// @ts-nocheck
"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import type { BusinessIntake, StrategyImpactPreview } from "@exposureflow/shared-types";
import { PageHeader } from "@/components/PageHeader";
import { parseApiError } from "@/components/ForbiddenState";
import { RequirePermission } from "@/components/WorkspaceGuard";
import { useWorkspaceAuth } from "@/lib/auth-context";
import { useSiteContext } from "@/lib/hooks";
import {
  EMPTY_STRATEGY_INTAKE_FORM,
  formValuesToIntakePayload,
  intakeStatusLabel,
  intakeToFormValues,
  isCurrentIntake,
  isIntakeApproved,
  type StrategyIntakeFormValues,
} from "@/lib/strategy-intake-form";

function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <label style={{ display: "block", marginBottom: "1rem", flex: "1 1 280px" }}>
      <div style={{ fontSize: "0.85rem", fontWeight: 600, marginBottom: "0.35rem" }}>{label}</div>
      {hint ? (
        <div style={{ fontSize: "0.78rem", color: "var(--muted)", marginBottom: "0.35rem" }}>{hint}</div>
      ) : null}
      {children}
    </label>
  );
}

function StrategyIntakeFormFields({
  values,
  onChange,
  disabled,
}: {
  values: StrategyIntakeFormValues;
  onChange: (values: StrategyIntakeFormValues) => void;
  disabled?: boolean;
}) {
  function set<K extends keyof StrategyIntakeFormValues>(key: K, value: StrategyIntakeFormValues[K]) {
    onChange({ ...values, [key]: value });
  }

  const listHint = "每行一項，例如：台中、台北";

  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: "0 1rem" }}>
      <Field label="公司／服務摘要" hint="面談重點：做什麼、服務誰、差異化">
        <textarea
          rows={4}
          value={values.company_summary}
          disabled={disabled}
          onChange={(e) => set("company_summary", e.target.value)}
          style={{ width: "100%", minWidth: 280 }}
          placeholder="例：ezfix 提供到府紗窗、紗門維修與更換…"
        />
      </Field>
      <Field label="市場與競爭備註">
        <textarea
          rows={4}
          value={values.market_notes}
          disabled={disabled}
          onChange={(e) => set("market_notes", e.target.value)}
          style={{ width: "100%", minWidth: 280 }}
          placeholder="主要競爭對手、區域特性、季節性…"
        />
      </Field>
      <Field label="目標客群" hint={listHint}>
        <textarea
          rows={3}
          value={values.customer_segments}
          disabled={disabled}
          onChange={(e) => set("customer_segments", e.target.value)}
          style={{ width: "100%", minWidth: 280 }}
        />
      </Field>
      <Field label="國內市場" hint={listHint}>
        <textarea
          rows={3}
          value={values.domestic_markets}
          disabled={disabled}
          onChange={(e) => set("domestic_markets", e.target.value)}
          style={{ width: "100%", minWidth: 280 }}
        />
      </Field>
      <Field label="外銷市場" hint={listHint}>
        <textarea
          rows={2}
          value={values.export_markets}
          disabled={disabled}
          onChange={(e) => set("export_markets", e.target.value)}
          style={{ width: "100%", minWidth: 280 }}
        />
      </Field>
      <Field label="銷售區域" hint={listHint}>
        <textarea
          rows={3}
          value={values.sales_regions}
          disabled={disabled}
          onChange={(e) => set("sales_regions", e.target.value)}
          style={{ width: "100%", minWidth: 280 }}
        />
      </Field>
      <Field label="策略目標（North Star）" hint={listHint}>
        <textarea
          rows={4}
          value={values.strategic_goals}
          disabled={disabled}
          onChange={(e) => set("strategic_goals", e.target.value)}
          style={{ width: "100%", minWidth: 280 }}
          placeholder="例：台中紗窗維修自然曝光成為區域第一"
        />
      </Field>
      <Field label="限制／不做的事" hint={listHint}>
        <textarea
          rows={3}
          value={values.constraints}
          disabled={disabled}
          onChange={(e) => set("constraints", e.target.value)}
          style={{ width: "100%", minWidth: 280 }}
          placeholder="例：不做全台、不做 B2B 批發相關詞"
        />
      </Field>
      <Field label="變更摘要" hint="建立新版本時，簡述這版與上一版的差異">
        <textarea
          rows={2}
          value={values.change_summary}
          disabled={disabled}
          onChange={(e) => set("change_summary", e.target.value)}
          style={{ width: "100%", minWidth: 280 }}
          placeholder="例：縮小服務區域、新增 B2B 限制"
        />
      </Field>
    </div>
  );
}

function StrategyIntakeReadOnlySummary({ intake }: { intake: BusinessIntake }) {
  const values = intakeToFormValues(intake);

  function ReadOnlyField({ label, value }: { label: string; value: string }) {
    if (!value.trim()) return null;
    return (
      <div style={{ flex: "1 1 280px", marginBottom: "1rem" }}>
        <div style={{ fontSize: "0.85rem", fontWeight: 600, marginBottom: "0.35rem" }}>{label}</div>
        <div
          style={{
            fontSize: "0.9rem",
            whiteSpace: "pre-wrap",
            lineHeight: 1.55,
            padding: "0.65rem 0.75rem",
            background: "var(--surface-2)",
            borderRadius: 8,
          }}
        >
          {value}
        </div>
      </div>
    );
  }

  const hasAnyContent = Object.values(values).some((value) => value.trim());

  return (
    <div className="card" style={{ marginBottom: "1.5rem" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "0.75rem",
          flexWrap: "wrap",
          marginBottom: "0.75rem",
        }}
      >
        <h2 style={{ fontSize: "1rem", margin: 0 }}>目前核准內容</h2>
        <span className="badge">{intakeStatusLabel(intake.status)}</span>
      </div>
      <p style={{ margin: "0 0 1rem", fontSize: "0.85rem", color: "var(--muted)" }}>
        以下為已填寫並核准的策略設定。若要修改，請按上方「建立新版本」重新填寫。
      </p>
      {!hasAnyContent ? (
        <p style={{ margin: 0, color: "var(--muted)", fontSize: "0.9rem" }}>
          此版本尚未記錄詳細欄位，僅有版本紀錄。
        </p>
      ) : (
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0 1rem" }}>
          <ReadOnlyField label="公司／服務摘要" value={values.company_summary} />
          <ReadOnlyField label="市場與競爭備註" value={values.market_notes} />
          <ReadOnlyField label="目標客群" value={values.customer_segments} />
          <ReadOnlyField label="國內市場" value={values.domestic_markets} />
          <ReadOnlyField label="外銷市場" value={values.export_markets} />
          <ReadOnlyField label="銷售區域" value={values.sales_regions} />
          <ReadOnlyField label="策略目標（North Star）" value={values.strategic_goals} />
          <ReadOnlyField label="限制／不做的事" value={values.constraints} />
        </div>
      )}
    </div>
  );
}

function ImpactPreviewCard({ preview }: { preview: StrategyImpactPreview }) {
  return (
    <div className="card" style={{ marginBottom: "1rem", background: "var(--surface-2)" }}>
      <h2 style={{ fontSize: "1rem", margin: "0 0 0.75rem" }}>核准前影響預覽</h2>
      <p style={{ margin: "0 0 0.75rem", fontSize: "0.88rem", color: "var(--muted)" }}>
        核准後會從策略文字抽取待審關鍵字、同步限制規則，並重算 Business Fit 與 open 機會。
      </p>
      <ul style={{ margin: 0, paddingLeft: "1.2rem", fontSize: "0.9rem", lineHeight: 1.6 }}>
        <li>新增待審關鍵字：{preview.keywords_to_add.length} 個</li>
        <li>同步限制規則：{preview.constraint_rules_to_upsert.length} 條</li>
        <li>受規則影響的既有節點：{preview.keywords_to_block.length} 個</li>
        <li>受影響 open 機會：{preview.opportunities_affected} 筆</li>
      </ul>
      {preview.keywords_to_add.length > 0 ? (
        <div style={{ marginTop: "0.75rem", fontSize: "0.85rem", color: "var(--muted)" }}>
          候選範例：{String(preview.keywords_to_add[0]?.keyword ?? "—")}（
          {String(preview.keywords_to_add[0]?.node_type ?? "—")}）
        </div>
      ) : null}
      {preview.opportunity_samples.length > 0 ? (
        <div style={{ marginTop: "0.75rem", fontSize: "0.85rem", color: "var(--muted)" }}>
          機會範例：{String(preview.opportunity_samples[0]?.keyword ?? "—")}（
          {String(preview.opportunity_samples[0]?.old_score)} →{" "}
          {String(preview.opportunity_samples[0]?.new_score)}）
        </div>
      ) : null}
    </div>
  );
}

function fmtTime(iso?: string | null) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("zh-TW", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function StrategyPage() {
  const { workspaceId, siteId, client } = useSiteContext();
  const { can } = useWorkspaceAuth();
  const canWrite = can("site:write");

  const [intakes, setIntakes] = useState<Array<Record<string, unknown>>>([]);
  const [activeIntakeId, setActiveIntakeId] = useState<string | null>(null);
  const [form, setForm] = useState<StrategyIntakeFormValues>(EMPTY_STRATEGY_INTAKE_FORM);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [impactPreview, setImpactPreview] = useState<StrategyImpactPreview | null>(null);

  const load = useCallback(async () => {
    if (!siteId) return;
    const rows = (await client.listStrategyIntakes(siteId)) as BusinessIntake[];
    setIntakes(rows);
    const draft = rows.find((row) => row.status === "draft");
    if (draft) {
      setActiveIntakeId(draft.id);
      setForm(intakeToFormValues(draft));
    } else {
      setActiveIntakeId(null);
      setForm(EMPTY_STRATEGY_INTAKE_FORM);
      setImpactPreview(null);
    }
  }, [client, siteId]);

  useEffect(() => {
    if (!siteId) {
      setLoading(false);
      return;
    }
    load()
      .catch((err: Error) => setError(parseApiError(err.message).friendly))
      .finally(() => setLoading(false));
  }, [load, siteId]);

  const currentIntake = useMemo(
    () => intakes.find((row) => isCurrentIntake(row)) ?? null,
    [intakes],
  );

  const activeIntake = useMemo(
    () => intakes.find((row) => row.id === activeIntakeId) ?? null,
    [intakes, activeIntakeId],
  );

  const editingDraft = activeIntake != null && activeIntake.status === "draft";
  const hasAnyIntake = intakes.length > 0;

  useEffect(() => {
    if (!activeIntakeId || !editingDraft) {
      setImpactPreview(null);
      return;
    }
    client
      .previewStrategyIntakeImpact(activeIntakeId)
      .then((preview) => setImpactPreview(preview as StrategyImpactPreview))
      .catch(() => setImpactPreview(null));
  }, [activeIntakeId, client, editingDraft, form]);

  async function refreshImpactPreview(intakeId: string) {
    const preview = (await client.previewStrategyIntakeImpact(intakeId)) as StrategyImpactPreview;
    setImpactPreview(preview);
  }

  async function handleCreateDraft() {
    if (!siteId || !canWrite) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const row = (await client.createStrategyIntake({
        site_id: siteId,
        ...formValuesToIntakePayload(form),
      })) as BusinessIntake;
      setActiveIntakeId(row.id);
      setForm(intakeToFormValues(row));
      setMessage("已建立策略 Intake 草稿");
      await load();
    } catch (err) {
      setError(parseApiError(err instanceof Error ? err.message : "建立失敗").friendly);
    } finally {
      setBusy(false);
    }
  }

  async function handleSaveDraft(e: React.FormEvent) {
    e.preventDefault();
    if (!siteId || !canWrite) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      let intakeId = activeIntakeId;
      if (!intakeId) {
        const created = (await client.createStrategyIntake({
          site_id: siteId,
          ...formValuesToIntakePayload(form),
        })) as BusinessIntake;
        intakeId = created.id;
        setActiveIntakeId(intakeId);
      } else {
        await client.updateStrategyIntake(intakeId, formValuesToIntakePayload(form));
      }
      setMessage("草稿已儲存");
      if (intakeId) {
        await refreshImpactPreview(intakeId);
      }
      await load();
    } catch (err) {
      setError(parseApiError(err instanceof Error ? err.message : "儲存失敗").friendly);
    } finally {
      setBusy(false);
    }
  }

  async function handleApprove() {
    if (!activeIntakeId || !canWrite) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      await client.updateStrategyIntake(activeIntakeId, formValuesToIntakePayload(form));
      const result = await client.approveStrategyIntake(activeIntakeId);
      const impact = result.impact as {
        keywords_created?: number;
        keywords_updated?: number;
        opportunities_rescored?: number;
      };
      setMessage(
        `策略 Intake v${String((result.intake as BusinessIntake).version_number)} 已核准並套用：` +
          `新增 ${impact.keywords_created ?? 0} 個關鍵字、` +
          `更新 ${impact.keywords_updated ?? 0} 個、` +
          `重算 ${impact.opportunities_rescored ?? 0} 筆機會`,
      );
      setActiveIntakeId(null);
      setForm(EMPTY_STRATEGY_INTAKE_FORM);
      setImpactPreview(null);
      await load();
    } catch (err) {
      setError(parseApiError(err instanceof Error ? err.message : "核准失敗").friendly);
    } finally {
      setBusy(false);
    }
  }

  async function startNewVersion() {
    if (!currentIntake || !canWrite) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const row = (await client.forkStrategyIntake(currentIntake.id)) as BusinessIntake;
      setActiveIntakeId(row.id);
      setForm(intakeToFormValues(row));
      await refreshImpactPreview(row.id);
      setMessage(`已建立 v${row.version_number} 草稿，內容已從目前核准版複製`);
      await load();
    } catch (err) {
      setError(parseApiError(err instanceof Error ? err.message : "建立新版本失敗").friendly);
    } finally {
      setBusy(false);
    }
  }

  const showIntakeForm = canWrite && (!hasAnyIntake || editingDraft);

  if (!siteId) {
    return <p style={{ color: "var(--muted)" }}>請先選擇有效站點。</p>;
  }

  if (loading) {
    return <p style={{ color: "var(--muted)" }}>載入策略 Intake…</p>;
  }

  return (
    <RequirePermission permission="site:read" workspaceId={workspaceId}>
      <PageHeader
        title="策略 Intake"
        subtitle="顧問面談後記錄 business scope——核准後會自動影響關鍵字金字塔與機會評分"
      />

      {error ? <p style={{ color: "var(--danger)", marginBottom: "1rem" }}>{error}</p> : null}
      {message ? <p style={{ color: "var(--success)", marginBottom: "1rem" }}>{message}</p> : null}

      {currentIntake && !editingDraft ? (
        <>
          {/* Strategy Hero Card */}
          <div className="strategy-hero">
            <h2>🎯 North Star：{currentIntake.strategic_goals_json[0] ?? currentIntake.company_summary?.slice(0, 120) ?? "尚未設定"}</h2>
            <p>核准版 v{currentIntake.version_number} · 核准時間 {fmtTime(currentIntake.approved_at)} · 此版本已套用到關鍵字金字塔與 Business Fit</p>
          </div>

          {/* Strategy Card Grid */}
          <div className="strategy-card-grid">
            {currentIntake.company_summary && (
              <div className="strategy-card">
                <h3>公司／服務摘要</h3>
                <p style={{ margin: 0, fontSize: "0.88rem", lineHeight: 1.6, whiteSpace: "pre-wrap" }}>{currentIntake.company_summary}</p>
              </div>
            )}
            {currentIntake.market_notes && (
              <div className="strategy-card">
                <h3>市場與競爭</h3>
                <p style={{ margin: 0, fontSize: "0.88rem", lineHeight: 1.6, whiteSpace: "pre-wrap" }}>{currentIntake.market_notes}</p>
              </div>
            )}
            {currentIntake.customer_segments && (
              <div className="strategy-card">
                <h3>目標客群</h3>
                <ul>{currentIntake.customer_segments.split("\n").filter(Boolean).map((s, i) => <li key={i}>{s}</li>)}</ul>
              </div>
            )}
            {currentIntake.domestic_markets && (
              <div className="strategy-card">
                <h3>國內市場</h3>
                <ul>{currentIntake.domestic_markets.split("\n").filter(Boolean).map((s, i) => <li key={i}>{s}</li>)}</ul>
              </div>
            )}
            {currentIntake.export_markets && (
              <div className="strategy-card">
                <h3>外銷市場</h3>
                <ul>{currentIntake.export_markets.split("\n").filter(Boolean).map((s, i) => <li key={i}>{s}</li>)}</ul>
              </div>
            )}
            {currentIntake.sales_regions && (
              <div className="strategy-card">
                <h3>銷售區域</h3>
                <ul>{currentIntake.sales_regions.split("\n").filter(Boolean).map((s, i) => <li key={i}>{s}</li>)}</ul>
              </div>
            )}
            {currentIntake.strategic_goals_json.length > 1 && (
              <div className="strategy-card">
                <h3>策略目標</h3>
                <ul>{currentIntake.strategic_goals_json.slice(1).map((g, i) => <li key={i}>{g}</li>)}</ul>
              </div>
            )}
            {currentIntake.constraints_json.length > 0 && (
              <div className="strategy-card" style={{ borderColor: "var(--warning)" }}>
                <h3>⚠ 限制／不做的事</h3>
                <ul>{currentIntake.constraints_json.map((c, i) => <li key={i}>{c}</li>)}</ul>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="card card-secondary" style={{ marginBottom: "1.5rem" }}>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", alignItems: "center" }}>
              <Link href={`/app/${workspaceId}/sites/${siteId}/keyword-pyramid`} className="btn btn-primary" style={{ fontSize: "0.85rem" }}>關鍵字金字塔</Link>
              <Link href={`/app/${workspaceId}/onboarding`} className="btn" style={{ fontSize: "0.85rem" }}>回到 Onboarding</Link>
              {canWrite ? (
                <>
                  <button type="button" className="btn" style={{ fontSize: "0.85rem" }} disabled={busy} onClick={startNewVersion}>建立新版本</button>
                  <button type="button" className="btn" style={{ fontSize: "0.85rem" }} disabled={busy} onClick={async () => {
                    if (!siteId) return;
                    setBusy(true); setError(null);
                    try {
                      const result = await client.reapplyCurrentStrategyIntake(siteId);
                      const impact = result.impact as { keywords_created?: number; keywords_updated?: number };
                      setMessage(`已重新套用 v${String((result.intake as BusinessIntake).version_number)}：新增 ${impact.keywords_created ?? 0} 個關鍵字、更新 ${impact.keywords_updated ?? 0} 個`);
                    } catch (err) { setError(parseApiError(err instanceof Error ? err.message : "套用失敗").friendly); }
                    finally { setBusy(false); }
                  }}>重新套用策略影響</button>
                </>
              ) : null}
            </div>
          </div>
        </>
      ) : null}

      {currentIntake && !editingDraft ? (
        <StrategyIntakeReadOnlySummary intake={currentIntake} />
      ) : null}

      {editingDraft && impactPreview ? <ImpactPreviewCard preview={impactPreview} /> : null}

      {showIntakeForm ? (
        <form className="card" onSubmit={handleSaveDraft} style={{ marginBottom: "1.5rem" }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              gap: "0.75rem",
              flexWrap: "wrap",
              marginBottom: "0.75rem",
            }}
          >
            <h2 style={{ fontSize: "1rem", margin: 0 }}>
              {editingDraft
                ? `編輯草稿 v${activeIntake?.version_number ?? ""}`
                : "建立策略 Intake v1"}
            </h2>
            {editingDraft ? (
              <span className="badge">{intakeStatusLabel(activeIntake!.status)}</span>
            ) : null}
          </div>
          <StrategyIntakeFormFields values={form} onChange={setForm} disabled={busy} />
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginTop: "0.5rem" }}>
            {!activeIntakeId ? (
              <button type="button" className="btn" disabled={busy} onClick={handleCreateDraft}>
                建立草稿
              </button>
            ) : null}
            <button type="submit" className="btn btn-primary" disabled={busy}>
              {busy ? "儲存中…" : "儲存草稿"}
            </button>
            {activeIntakeId ? (
              <button type="button" className="btn btn-primary" disabled={busy} onClick={handleApprove}>
                核准並套用策略影響
              </button>
            ) : null}
          </div>
        </form>
      ) : !canWrite && !currentIntake ? (
        <p className="card" style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
          您的角色只能檢視。請 strategist 或 admin 填寫並核准 Intake。
        </p>
      ) : null}

      <section>
        <h2 style={{ fontSize: "1rem", marginBottom: "0.75rem" }}>版本紀錄</h2>
        {intakes.length === 0 ? (
          <div className="card">
            <p style={{ margin: 0, color: "var(--muted)" }}>
              尚無 Intake。{canWrite ? "請使用上方表單建立第一版策略摘要。" : ""}
            </p>
          </div>
        ) : (
          <div className="table-wrap card" style={{ padding: 0 }}>
            <table>
              <thead>
                <tr>
                  <th>版本</th>
                  <th>狀態</th>
                  <th>策略目標</th>
                  <th>變更摘要</th>
                  <th>更新時間</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {intakes.map((row) => (
                  <tr key={row.id}>
                    <td>
                      v{row.version_number}
                      {row.is_current ? (
                        <span className="badge" style={{ marginLeft: "0.35rem" }}>
                          目前
                        </span>
                      ) : null}
                    </td>
                    <td>
                      <span className="badge">{intakeStatusLabel(row.status)}</span>
                    </td>
                    <td style={{ maxWidth: 320 }}>
                      {row.strategic_goals_json[0] ??
                        row.company_summary?.slice(0, 80) ??
                        "—"}
                    </td>
                    <td style={{ maxWidth: 240, fontSize: "0.85rem", color: "var(--muted)" }}>
                      {row.change_summary || "—"}
                    </td>
                    <td style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
                      {fmtTime(row.updated_at)}
                    </td>
                    <td>
                      {canWrite && row.status === "draft" ? (
                        <button
                          type="button"
                          className="btn"
                          style={{ fontSize: "0.8rem" }}
                          onClick={() => {
                            setActiveIntakeId(row.id);
                            setForm(intakeToFormValues(row));
                          }}
                        >
                          編輯
                        </button>
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </RequirePermission>
  );
}
