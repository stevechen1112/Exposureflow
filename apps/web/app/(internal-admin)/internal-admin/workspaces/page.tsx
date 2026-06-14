"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { getInternalApiClient } from "@/lib/internal-api-client";

type Workspace = {
  id: string;
  name: string;
  account_name: string;
  workspace_type: string;
  status: string;
  member_count: number;
  site_count: number;
  plan_code: string | null;
  billing_status: string | null;
  feature_flags: Record<string, unknown>;
};

export default function InternalWorkspacesPage() {
  const client = getInternalApiClient();
  const [rows, setRows] = useState<Workspace[]>([]);
  const [accounts, setAccounts] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState<string | null>(null);
  const [flagEdit, setFlagEdit] = useState<{ id: string; json: string } | null>(null);

  useEffect(() => {
    Promise.all([client.internalListWorkspaces(), client.internalListAccounts()])
      .then(([ws, acct]) => {
        setRows(ws as Workspace[]);
        setAccounts(acct);
      })
      .catch((err: Error) => setError(err.message));
  }, [client]);

  async function saveFlags() {
    if (!flagEdit) return;
    try {
      const parsed = JSON.parse(flagEdit.json) as Record<string, unknown>;
      await client.internalUpdateFeatureFlags(flagEdit.id, parsed);
      setRows((prev) =>
        prev.map((r) => (r.id === flagEdit.id ? { ...r, feature_flags: { ...r.feature_flags, ...parsed } } : r)),
      );
      setFlagEdit(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed");
    }
  }

  return (
    <>
      <PageHeader title="Internal Admin — Workspaces" subtitle="帳戶、訂閱、feature flags" />
      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}

      <section className="card" style={{ marginBottom: "1.5rem" }}>
        <h3>Accounts ({accounts.length})</h3>
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Billing</th>
              <th>Plan</th>
              <th>Workspaces</th>
            </tr>
          </thead>
          <tbody>
            {accounts.map((a) => (
              <tr key={String(a.id)}>
                <td>{String(a.name)}</td>
                <td>{String(a.account_type)}</td>
                <td>{String(a.billing_status)}</td>
                <td>{String(a.plan_code ?? "—")}</td>
                <td>{String(a.workspace_count)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="card">
        <h3>Workspaces ({rows.length})</h3>
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Account</th>
              <th>Type</th>
              <th>Members</th>
              <th>Sites</th>
              <th>Plan</th>
              <th>Flags</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <td>{r.name}</td>
                <td>{r.account_name}</td>
                <td>{r.workspace_type}</td>
                <td>{r.member_count}</td>
                <td>{r.site_count}</td>
                <td>{r.plan_code ?? "—"}</td>
                <td>
                  <button
                    type="button"
                    onClick={() =>
                      setFlagEdit({ id: r.id, json: JSON.stringify(r.feature_flags ?? {}, null, 2) })
                    }
                  >
                    Edit flags
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {flagEdit ? (
        <div className="card" style={{ marginTop: "1rem" }}>
          <h3>Feature flags — {flagEdit.id}</h3>
          <textarea
            value={flagEdit.json}
            onChange={(e) => setFlagEdit({ ...flagEdit, json: e.target.value })}
            rows={8}
            style={{ width: "100%", fontFamily: "monospace" }}
          />
          <div style={{ marginTop: "0.75rem", display: "flex", gap: "0.5rem" }}>
            <button type="button" onClick={saveFlags}>
              Save
            </button>
            <button type="button" onClick={() => setFlagEdit(null)}>
              Cancel
            </button>
          </div>
        </div>
      ) : null}
    </>
  );
}
