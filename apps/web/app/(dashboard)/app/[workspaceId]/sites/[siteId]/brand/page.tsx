"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { useSiteContext } from "@/lib/hooks";

export default function BrandPage() {
  const { siteId, client } = useSiteContext();
  const [entities, setEntities] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    client.listBrandEntities(siteId).then(setEntities).catch((err: Error) => setError(err.message));
  }, [client, siteId]);

  return (
    <>
      <PageHeader title="品牌實體" subtitle="Brand entities 與一致性檢查基礎" />
      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}
      <div className="table-wrap card" style={{ padding: 0 }}>
        <table>
          <thead>
            <tr>
              <th>名稱</th>
              <th>類型</th>
              <th>別名</th>
              <th>狀態</th>
            </tr>
          </thead>
          <tbody>
            {entities.map((e) => (
              <tr key={String(e.id)}>
                <td>{String(e.canonical_name ?? e.name ?? "")}</td>
                <td>{String(e.entity_type ?? "")}</td>
                <td>{Array.isArray(e.aliases) ? e.aliases.join(", ") : String(e.aliases ?? "")}</td>
                <td>{String(e.status ?? "")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
