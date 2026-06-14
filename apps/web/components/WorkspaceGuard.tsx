"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useWorkspaceAuth } from "@/lib/auth-context";
import {
  resolveEntryPath,
  usesBillingOnlyShell,
  usesClientPortal,
} from "@/lib/permissions";
import { ForbiddenState } from "./ForbiddenState";

/** Redirect or block when role should not use main app shell routes. */
export function WorkspaceGuard({
  workspaceId,
  children,
}: {
  workspaceId: string;
  children: React.ReactNode;
}) {
  const { loading, role } = useWorkspaceAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (loading || !role) return;
    if (usesClientPortal(role)) {
      router.replace(`/client/${workspaceId}`);
      return;
    }
    if (usesBillingOnlyShell(role)) {
      const allowed = pathname.includes("/settings/billing") || pathname.endsWith("/settings");
      if (!allowed) {
        router.replace(`/app/${workspaceId}/settings/billing`);
      }
    }
  }, [loading, role, workspaceId, router, pathname]);

  if (loading) {
    return <p style={{ padding: "2rem", color: "var(--muted)" }}>載入您的角色與權限…</p>;
  }

  if (usesClientPortal(role)) {
    return (
      <p style={{ padding: "2rem", color: "var(--muted)" }}>正在導向客戶入口…</p>
    );
  }

  return <>{children}</>;
}

export function RequirePermission({
  permission,
  workspaceId,
  fallbackHome,
  children,
}: {
  permission: string;
  workspaceId: string;
  fallbackHome?: string;
  children: React.ReactNode;
}) {
  const { loading, can, role } = useWorkspaceAuth();
  if (loading) {
    return <p style={{ color: "var(--muted)" }}>載入中…</p>;
  }
  if (!can(permission)) {
    return (
      <ForbiddenState
        homeHref={fallbackHome ?? resolveEntryPath(workspaceId, role)}
        homeLabel="返回可存取頁面"
      />
    );
  }
  return <>{children}</>;
}
