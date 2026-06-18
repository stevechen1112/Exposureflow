"use client";

import { useCallback, useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import type { Workspace } from "@exposureflow/shared-types";
import { getApiClient, resetApiClientCache } from "@/lib/api-client";
import {
  pathAfterWorkspaceSwitch,
  persistWorkspaceSwitch,
  workspaceDisplayLabel,
} from "@/lib/workspace-navigation";

export function WorkspaceSwitcher({ workspaceId }: { workspaceId: string }) {
  const router = useRouter();
  const pathname = usePathname();
  const [allWorkspaces, setAllWorkspaces] = useState<Workspace[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const client = getApiClient(workspaceId);
      const rows = await client.listWorkspaces();
      setAllWorkspaces(rows);
    } catch {
      setAllWorkspaces([]);
    } finally {
      setLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    load();
  }, [load]);

  const clientWorkspaces = allWorkspaces.filter(
    (w) => (w.status === "active" || w.status === undefined) && w.workspace_type !== "agency_internal",
  );
  const switchable = clientWorkspaces.length > 0 ? clientWorkspaces : allWorkspaces;

  const current =
    allWorkspaces.find((w) => w.id === workspaceId) ??
    switchable.find((w) => w.id === workspaceId) ??
    ({ id: workspaceId, name: "工作區", client_name: null, workspace_type: "client" } as Workspace);

  const currentIsSwitchable = switchable.some((w) => w.id === workspaceId);

  if (loading) {
    return (
      <div className="context-switcher">
        <span className="context-switcher-label">客戶工作區</span>
        <span className="context-switcher-value muted">載入中…</span>
      </div>
    );
  }

  if (switchable.length <= 1 || !currentIsSwitchable) {
    return (
      <div className="context-switcher">
        <span className="context-switcher-label">客戶工作區</span>
        <span className="context-switcher-value">
          {workspaceDisplayLabel(current.name, current.client_name)}
          {current.workspace_type === "agency_internal" ? "（顧問內部）" : ""}
        </span>
      </div>
    );
  }

  return (
    <div className="context-switcher">
      <label className="context-switcher-label" htmlFor="workspace-switcher">
        客戶工作區
      </label>
      <select
        id="workspace-switcher"
        className="context-switcher-select"
        value={workspaceId}
        onChange={(e) => {
          const nextId = e.target.value;
          if (nextId === workspaceId) return;
          persistWorkspaceSwitch(nextId);
          resetApiClientCache();
          const nextPath = pathAfterWorkspaceSwitch(pathname, workspaceId, nextId);
          router.push(nextPath);
        }}
      >
        {switchable.map((w) => (
          <option key={w.id} value={w.id}>
            {workspaceDisplayLabel(w.name, w.client_name)}
            {w.workspace_type === "client" ? "" : ` (${w.workspace_type})`}
          </option>
        ))}
      </select>
    </div>
  );
}
