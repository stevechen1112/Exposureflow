"use client";

import { useCallback, useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import type { Site } from "@exposureflow/shared-types";
import { getApiClient } from "@/lib/api-client";
import { persistSiteSwitch } from "@/lib/workspace-navigation";

function siteSubpath(pathname: string, workspaceId: string, siteId: string): string {
  const prefix = `/app/${workspaceId}/sites/${siteId}`;
  if (pathname.startsWith(prefix)) {
    const rest = pathname.slice(prefix.length);
    return rest || "/dashboard";
  }
  return "/dashboard";
}

export function SiteSwitcher({
  workspaceId,
  siteId,
}: {
  workspaceId: string;
  siteId: string | undefined;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [sites, setSites] = useState<Site[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const client = getApiClient(workspaceId);
      const rows = await client.listSites();
      setSites(rows);
    } catch {
      setSites([]);
    } finally {
      setLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    load();
  }, [load]);

  if (!siteId) return null;

  const current = sites.find((s) => s.id === siteId);

  if (loading) {
    return (
      <div className="context-switcher">
        <span className="context-switcher-label">目前站點</span>
        <span className="context-switcher-value muted">載入中…</span>
      </div>
    );
  }

  if (sites.length <= 1) {
    return (
      <div className="context-switcher">
        <span className="context-switcher-label">目前站點</span>
        <span className="context-switcher-value" title={current?.domain}>
          {current?.site_name ?? current?.domain ?? "—"}
        </span>
      </div>
    );
  }

  return (
    <div className="context-switcher">
      <label className="context-switcher-label" htmlFor="site-switcher">
        目前站點
      </label>
      <select
        id="site-switcher"
        className="context-switcher-select"
        value={siteId}
        onChange={(e) => {
          const nextSiteId = e.target.value;
          if (nextSiteId === siteId) return;
          persistSiteSwitch(nextSiteId);
          const sub = siteSubpath(pathname, workspaceId, siteId);
          router.push(`/app/${workspaceId}/sites/${nextSiteId}${sub}`);
        }}
      >
        {sites.map((s) => (
          <option key={s.id} value={s.id}>
            {s.site_name} ({s.domain})
          </option>
        ))}
      </select>
    </div>
  );
}
