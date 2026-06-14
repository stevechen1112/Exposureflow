"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { getInternalApiClient } from "@/lib/internal-api-client";

export default function InternalAuditPage() {
  const client = getInternalApiClient();
  const [logs, setLogs] = useState<Array<Record<string, unknown>>>([]);
  const [users, setUsers] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState<string | null>(null);
  const [email, setEmail] = useState("");

  useEffect(() => {
    client
      .internalListAuditLogs({ action_prefix: "support" })
      .then(setLogs)
      .catch((err: Error) => setError(err.message));
  }, [client]);

  async function searchUsers() {
    try {
      const rows = await client.internalSearchUsers(email || undefined);
      setUsers(rows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    }
  }

  return (
    <>
      <PageHeader title="Audit Logs" subtitle="Support actions 與使用者查詢" />
      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}

      <section className="card" style={{ marginBottom: "1.5rem" }}>
        <h3>Support audit trail</h3>
        <table className="data-table">
          <thead>
            <tr>
              <th>Action</th>
              <th>Target</th>
              <th>Workspace</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((l) => (
              <tr key={String(l.id)}>
                <td>{String(l.action)}</td>
                <td>
                  {String(l.target_type)}:{String(l.target_id ?? "")}
                </td>
                <td>{String(l.workspace_id ?? "—")}</td>
                <td>{String(l.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="card">
        <h3>User search</h3>
        <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
          <input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="email filter"
            style={{ flex: 1 }}
          />
          <button type="button" onClick={searchUsers}>
            Search
          </button>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Email</th>
              <th>Name</th>
              <th>Memberships</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={String(u.id)}>
                <td>{String(u.email)}</td>
                <td>{String(u.name)}</td>
                <td>{JSON.stringify(u.memberships)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
