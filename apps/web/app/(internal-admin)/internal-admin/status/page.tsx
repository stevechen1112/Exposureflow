/* eslint-disable @typescript-eslint/ban-ts-comment */
// @ts-nocheck
"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { getInternalApiClient } from "@/lib/internal-api-client";

export default function InternalStatusPage() {
  const client = getInternalApiClient();
  const [incidents, setIncidents] = useState<Array<Record<string, unknown>>>([]);
  const [publicStatus, setPublicStatus] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({ title: "", summary: "", severity: "minor", is_public: false });

  useEffect(() => {
    Promise.all([client.internalListStatusIncidents(), client.getPublicStatus()])
      .then(([admin, pub]) => {
        setIncidents(admin);
        setPublicStatus(pub);
      })
      .catch((err: Error) => setError(err.message));
  }, [client]);

  async function createIncident() {
    try {
      const row = await client.internalCreateStatusIncident({
        title: form.title,
        summary: form.summary,
        severity: form.severity,
        affected_components: ["api"],
        is_public: form.is_public,
      });
      setIncidents((prev) => [row, ...prev]);
      if (form.is_public) setPublicStatus((prev) => [row, ...prev]);
      setForm({ title: "", summary: "", severity: "minor", is_public: false });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create failed");
    }
  }

  return (
    <>
      <PageHeader title="Status Page" subtitle="公開服務狀態與 incident 管理" />
      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}

      <section className="card" style={{ marginBottom: "1.5rem" }}>
        <h3>Public status ({publicStatus.length})</h3>
        {publicStatus.map((i) => (
          <div key={String(i.id)} style={{ marginBottom: "0.75rem", paddingBottom: "0.75rem", borderBottom: "1px solid var(--border)" }}>
            <strong>{String(i.title)}</strong> · {String(i.status)} · {String(i.severity)}
            <p style={{ color: "var(--muted)", margin: "0.25rem 0 0" }}>{String(i.summary)}</p>
          </div>
        ))}
      </section>

      <section className="card" style={{ marginBottom: "1.5rem" }}>
        <h3>Create incident</h3>
        <input
          placeholder="Title"
          value={form.title}
          onChange={(e) => setForm({ ...form, title: e.target.value })}
          style={{ width: "100%", marginBottom: "0.5rem" }}
        />
        <textarea
          placeholder="Summary"
          value={form.summary}
          onChange={(e) => setForm({ ...form, summary: e.target.value })}
          rows={3}
          style={{ width: "100%", marginBottom: "0.5rem" }}
        />
        <label style={{ display: "block", marginBottom: "0.5rem" }}>
          <input
            type="checkbox"
            checked={form.is_public}
            onChange={(e) => setForm({ ...form, is_public: e.target.checked })}
          />{" "}
          Publish publicly
        </label>
        <select value={form.severity} onChange={(e) => setForm({ ...form, severity: e.target.value })}>
          <option value="minor">minor</option>
          <option value="major">major</option>
          <option value="critical">critical</option>
        </select>
        <div style={{ marginTop: "0.75rem" }}>
          <button type="button" onClick={createIncident} disabled={!form.title || !form.summary}>
            Publish incident
          </button>
        </div>
      </section>

      <section className="card">
        <h3>All incidents</h3>
        <table className="data-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Status</th>
              <th>Public</th>
              <th>Started</th>
            </tr>
          </thead>
          <tbody>
            {incidents.map((i) => (
              <tr key={String(i.id)}>
                <td>{String(i.title)}</td>
                <td>{String(i.status)}</td>
                <td>{String(i.is_public)}</td>
                <td>{String(i.started_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
