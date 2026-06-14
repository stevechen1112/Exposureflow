"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { getApiClient } from "./api-client";
import { canRole, type WorkspaceRole } from "./permissions";
import { storageKey } from "./config";

type MeUser = { id: string; email: string; name: string };
type MeWorkspace = { id: string; name: string; role: string; workspace_type: string };

type WorkspaceAuthState = {
  loading: boolean;
  user: MeUser | null;
  role: string | undefined;
  workspaces: MeWorkspace[];
  refresh: () => Promise<void>;
  can: (permission: string) => boolean;
};

const WorkspaceAuthContext = createContext<WorkspaceAuthState | null>(null);

export function WorkspaceAuthProvider({
  workspaceId,
  children,
}: {
  workspaceId: string;
  children: ReactNode;
}) {
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<MeUser | null>(null);
  const [workspaces, setWorkspaces] = useState<MeWorkspace[]>([]);
  const [role, setRole] = useState<string | undefined>();

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const client = getApiClient(workspaceId);
      const me = await client.getMe();
      setUser(me.user as MeUser);
      const wsList = (me.workspaces as MeWorkspace[]) ?? [];
      setWorkspaces(wsList);
      const match = wsList.find((w) => w.id === workspaceId);
      setRole(match?.role);
      if (match) localStorage.setItem(storageKey("workspaceId"), match.id);
    } catch {
      setUser(null);
      setWorkspaces([]);
      setRole(undefined);
    } finally {
      setLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const can = useCallback((permission: string) => canRole(role, permission), [role]);

  const value = useMemo(
    () => ({ loading, user, role, workspaces, refresh, can }),
    [loading, user, role, workspaces, refresh, can],
  );

  return (
    <WorkspaceAuthContext.Provider value={value}>{children}</WorkspaceAuthContext.Provider>
  );
}

export function useWorkspaceAuth() {
  const ctx = useContext(WorkspaceAuthContext);
  if (!ctx) {
    throw new Error("useWorkspaceAuth must be used within WorkspaceAuthProvider");
  }
  return ctx;
}

export function roleLabel(role: string | undefined): string {
  if (!role) return "未知角色";
  const labels: Record<string, string> = {
    owner: "擁有者",
    admin: "管理員",
    strategist: "策略師",
    editor: "編輯",
    analyst: "分析師",
    client_viewer: "客戶檢視",
    billing_admin: "計費管理",
    support_admin: "平台支援",
  };
  return labels[role] ?? role;
}

export type { WorkspaceRole };
