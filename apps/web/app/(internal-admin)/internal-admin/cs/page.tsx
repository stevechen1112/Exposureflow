"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { getInternalApiClient } from "@/lib/internal-api-client";

export default function InternalCsPage() {
  const client = getInternalApiClient();
  const [activation, setActivation] = useState<Array<Record<string, unknown>>>([]);
  const [funnel, setFunnel] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([client.internalCsActivation(), client.internalCsFunnel()])
      .then(([a, f]) => {
        setActivation(a);
        setFunnel(f);
      })
      .catch((err: Error) => setError(err.message));
  }, [client]);

  return (
    <>
      <PageHeader title="Customer Success" subtitle="Activation、onboarding funnel、流失風險" />
      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}

      {funnel ? (
        <section className="kpi-grid" style={{ marginBottom: "1.5rem" }}>
          {[
            ["total_workspaces", "Workspaces"],
            ["has_site", "Has site"],
            ["first_gsc_sync", "GSC sync"],
            ["first_opportunity", "Opportunity"],
            ["first_report", "Report"],
            ["first_approved_decision", "Approved decision"],
            ["fully_activated", "Fully activated"],
          ].map(([key, label]) => (
            <div key={key} className="card">
              <div className="kpi-label">{label}</div>
              <div className="kpi-value">{String(funnel[key] ?? 0)}</div>
            </div>
          ))}
        </section>
      ) : null}

      <section className="card">
        <h3>Activation & churn risk</h3>
        <table className="data-table">
          <thead>
            <tr>
              <th>Workspace</th>
              <th>Account</th>
              <th>Score</th>
              <th>Risk</th>
              <th>Milestones</th>
            </tr>
          </thead>
          <tbody>
            {activation.map((r) => (
              <tr key={String(r.workspace_id)}>
                <td>{String(r.workspace_name)}</td>
                <td>{String(r.account_name)}</td>
                <td>{String(r.activation_score)}</td>
                <td style={{ color: r.churn_risk === "high" ? "var(--danger)" : undefined }}>
                  {String(r.churn_risk)}
                </td>
                <td>
                  <code style={{ fontSize: "0.75rem" }}>{JSON.stringify(r.milestones)}</code>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
