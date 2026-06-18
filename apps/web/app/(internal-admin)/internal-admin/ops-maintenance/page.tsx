/* eslint-disable @typescript-eslint/ban-ts-comment */
// @ts-nocheck
"use client";

import { useCallback, useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { getInternalApiClient } from "@/lib/internal-api-client";

function statusColor(status: string | undefined): string {
  if (status === "critical") return "var(--danger)";
  if (status === "warn") return "var(--warning)";
  if (status === "pass") return "var(--success)";
  return "var(--muted)";
}

export default function OpsMaintenancePage() {
  const client = getInternalApiClient();
  const [latest, setLatest] = useState<{ run: Record<string, unknown> | null; signals: Array<Record<string, unknown>> }>({
    run: null,
    signals: [],
  });
  const [history, setHistory] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const [latestRes, runsRes] = await Promise.all([
      client.internalOpsMaintenanceLatest(),
      client.internalOpsMaintenanceRuns(10),
    ]);
    setLatest(latestRes);
    setHistory(runsRes);
  }, [client]);

  useEffect(() => {
    load().catch((err: Error) => setError(err.message));
  }, [load]);

  async function runNow() {
    setBusy(true);
    setError(null);
    try {
      await client.internalOpsMaintenanceRun(true);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "執行失敗");
    } finally {
      setBusy(false);
    }
  }

  const run = latest.run;
  const critical = latest.signals.filter((s) => s.severity === "critical");
  const warn = latest.signals.filter((s) => s.severity === "warn");
  const pass = latest.signals.filter((s) => s.severity === "pass");

  return (
    <>
      <PageHeader
        title="維護工程師"
        subtitle="規則巡檢 + AI 晨報 — 平台健康與顧問交付停滯偵測"
        actions={
          <button type="button" className="btn btn-primary" disabled={busy} onClick={runNow}>
            {busy ? "執行中…" : "手動巡檢"}
          </button>
        }
      />
      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}

      <section className="card" style={{ marginBottom: "1rem" }}>
        <h2 style={{ marginTop: 0, fontSize: "1.1rem" }}>整體狀態</h2>
        {run ? (
          <>
            <p style={{ fontSize: "1.25rem", fontWeight: 600, color: statusColor(String(run.status)) }}>
              {String(run.status).toUpperCase()}
            </p>
            <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
              最近巡檢：{String(run.started_at)} · trigger={String(run.trigger)}
            </p>
            {run.summary_title ? <p style={{ fontWeight: 500 }}>{String(run.summary_title)}</p> : null}
          </>
        ) : (
          <p style={{ color: "var(--muted)" }}>尚無巡檢紀錄。請按「手動巡檢」建立第一筆晨報。</p>
        )}
      </section>

      {run?.summary_markdown ? (
        <section className="card" style={{ marginBottom: "1rem" }}>
          <h2 style={{ marginTop: 0, fontSize: "1.1rem" }}>AI 維護晨報</h2>
          <pre
            style={{
              whiteSpace: "pre-wrap",
              fontFamily: "inherit",
              fontSize: "0.9rem",
              lineHeight: 1.6,
              margin: 0,
            }}
          >
            {String(run.summary_markdown)}
          </pre>
        </section>
      ) : null}

      {critical.length ? (
        <SignalSection title="Critical" signals={critical} color="var(--danger)" />
      ) : null}
      {warn.length ? <SignalSection title="Warn" signals={warn} color="var(--warning)" /> : null}
      {pass.length ? (
        <SignalSection title="Pass" signals={pass.slice(0, 8)} color="var(--success)" collapsedHint={`共 ${pass.length} 項通過`} />
      ) : null}

      {history.length ? (
        <section className="card" style={{ marginTop: "1rem" }}>
          <h2 style={{ marginTop: 0, fontSize: "1.1rem" }}>最近巡檢紀錄</h2>
          <table className="data-table">
            <thead>
              <tr>
                <th>時間</th>
                <th>狀態</th>
                <th>Trigger</th>
                <th>標題</th>
              </tr>
            </thead>
            <tbody>
              {history.map((r) => (
                <tr key={String(r.id)}>
                  <td>{String(r.started_at)}</td>
                  <td style={{ color: statusColor(String(r.status)) }}>{String(r.status)}</td>
                  <td>{String(r.trigger)}</td>
                  <td>{String(r.summary_title ?? "—")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ) : null}
    </>
  );
}

function SignalSection({
  title,
  signals,
  color,
  collapsedHint,
}: {
  title: string;
  signals: Array<Record<string, unknown>>;
  color: string;
  collapsedHint?: string;
}) {
  return (
    <section className="card" style={{ marginBottom: "1rem" }}>
      <h2 style={{ marginTop: 0, fontSize: "1.1rem", color }}>{title}</h2>
      {collapsedHint ? <p style={{ color: "var(--muted)", fontSize: "0.85rem" }}>{collapsedHint}</p> : null}
      <ul style={{ margin: 0, paddingLeft: "1.2rem", lineHeight: 1.7 }}>
        {signals.map((s) => (
          <li key={String(s.id ?? s.check_id)}>
            <strong>{String(s.title)}</strong> — {String(s.message)}
            <div style={{ color: "var(--muted)", fontSize: "0.85rem" }}>{String(s.recommended_action)}</div>
          </li>
        ))}
      </ul>
    </section>
  );
}
