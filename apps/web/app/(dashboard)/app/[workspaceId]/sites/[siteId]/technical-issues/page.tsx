"use client";

import { useCallback, useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { useSiteContext } from "@/lib/hooks";

export default function TechnicalIssuesPage() {
  const { siteId, client } = useSiteContext();
  const [issues, setIssues] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);

  const load = useCallback(async () => {
    try {
      const rows = await client.listTechnicalIssues(siteId);
      setIssues(rows);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "載入失敗");
    }
  }, [client, siteId]);

  useEffect(() => {
    load();
  }, [load]);

  async function crawl() {
    setSyncing(true);
    try {
      await client.triggerTechSeoCrawl(siteId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Crawl 失敗");
    } finally {
      setSyncing(false);
    }
  }

  return (
    <>
      <PageHeader title="技術問題" subtitle="Open technical SEO issues 與嚴重度" />
      <div className="form-row">
        <button type="button" className="btn btn-primary" disabled={syncing} onClick={crawl}>
          {syncing ? "Crawl 中…" : "觸發 Tech SEO Crawl"}
        </button>
        <button type="button" className="btn" onClick={load}>
          重新整理
        </button>
      </div>
      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}
      <div className="table-wrap card" style={{ padding: 0 }}>
        <table>
          <thead>
            <tr>
              <th>類型</th>
              <th>嚴重度</th>
              <th>URL</th>
              <th>說明</th>
            </tr>
          </thead>
          <tbody>
            {issues.length === 0 ? (
              <tr>
                <td colSpan={4} style={{ color: "var(--muted)" }}>
                  目前沒有 open 技術問題
                </td>
              </tr>
            ) : (
              issues.map((row) => (
                <tr key={String(row.id)}>
                  <td>{String(row.issue_type ?? "")}</td>
                  <td>
                    <span className={`badge ${String(row.severity) === "critical" ? "badge-critical" : ""}`}>
                      {String(row.severity ?? "")}
                    </span>
                  </td>
                  <td style={{ maxWidth: 280, wordBreak: "break-all" }}>{String(row.url ?? "")}</td>
                  <td>{String(row.description ?? row.details ?? "")}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
