"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { getInternalApiClient } from "@/lib/internal-api-client";

export default function InternalLaunchPage() {
  const client = getInternalApiClient();
  const [checklist, setChecklist] = useState<Record<string, unknown> | null>(null);
  const [metrics, setMetrics] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([client.internalLaunchChecklist(), client.internalBusinessMetrics()])
      .then(([cl, m]) => {
        setChecklist(cl);
        setMetrics(m);
      })
      .catch((err: Error) => setError(err.message));
  }, [client]);

  const checks = (checklist?.checks as Array<Record<string, unknown>>) ?? [];

  return (
    <>
      <PageHeader title="Launch Readiness" subtitle="EF-1401 正式上線檢查表" />
      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}

      {checklist ? (
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <h3>
            Overall: {String(checklist.overall)} — {String(checklist.passed)}/{String(checklist.total)} passed
          </h3>
        </div>
      ) : null}

      <section className="card" style={{ marginBottom: "1.5rem" }}>
        <h3>Checklist</h3>
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Status</th>
              <th>Message</th>
            </tr>
          </thead>
          <tbody>
            {checks.map((c) => (
              <tr key={String(c.id)}>
                <td>{String(c.id)}</td>
                <td>{String(c.name)}</td>
                <td style={{ color: c.status === "pass" ? "var(--success)" : "var(--danger)" }}>{String(c.status)}</td>
                <td>{String(c.message)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {metrics ? (
        <section className="card">
          <h3>Business metrics (EF-1403)</h3>
          <div className="kpi-grid" style={{ marginBottom: "1rem" }}>
            {[
              ["product_activation_rate", "Activation rate"],
              ["workspace_gsc_sync_rate", "GSC sync rate"],
              ["opportunity_approved_rate", "Approval rate"],
              ["monthly_active_workspaces", "MAW"],
            ].map(([key, label]) => (
              <div key={key}>
                <div className="kpi-label">{label}</div>
                <div className="kpi-value">{String(metrics[key] ?? "—")}</div>
              </div>
            ))}
          </div>
          <pre style={{ fontSize: "0.75rem", overflow: "auto" }}>{JSON.stringify(metrics, null, 2)}</pre>
        </section>
      ) : null}
    </>
  );
}
