/** Mirror of backend RBAC — keep in sync with apps/api/exposureflow_api/auth/permissions.py */

export type WorkspaceRole =
  | "owner"
  | "admin"
  | "strategist"
  | "editor"
  | "analyst"
  | "client_viewer"
  | "billing_admin"
  | "support_admin";

export const ROLE_LABELS: Record<WorkspaceRole, string> = {
  owner: "擁有者",
  admin: "管理員",
  strategist: "策略師",
  editor: "編輯",
  analyst: "分析師",
  client_viewer: "客戶檢視",
  billing_admin: "計費管理",
  support_admin: "平台支援",
};

const PERMISSIONS: Record<WorkspaceRole, Set<string>> = {
  owner: new Set([
    "workspace:read",
    "workspace:write",
    "site:read",
    "site:write",
    "member:read",
    "member:write",
    "invitation:write",
    "integration:read",
    "integration:write",
    "job:read",
    "job:write",
    "api_key:write",
    "billing:read",
    "agency:read",
    "ops:read",
    "impersonate",
    "client:approve",
  ]),
  admin: new Set([
    "workspace:read",
    "workspace:write",
    "site:read",
    "site:write",
    "member:read",
    "member:write",
    "invitation:write",
    "integration:read",
    "integration:write",
    "job:read",
    "job:write",
    "api_key:write",
    "billing:read",
    "agency:read",
    "ops:read",
    "client:approve",
  ]),
  client_viewer: new Set(["workspace:read", "site:read", "client:approve"]),
  strategist: new Set([
    "workspace:read",
    "site:read",
    "site:write",
    "member:read",
    "integration:read",
    "job:read",
    "job:write",
    "client:approve",
  ]),
  editor: new Set([
    "workspace:read",
    "site:read",
    "site:write",
    "job:read",
    "client:approve",
  ]),
  analyst: new Set(["workspace:read", "site:read", "job:read"]),
  billing_admin: new Set(["workspace:read", "billing:read"]),
  support_admin: new Set(["workspace:read", "site:read", "member:read", "impersonate"]),
};

export function canRole(role: string | undefined, permission: string): boolean {
  if (!role) return false;
  return PERMISSIONS[role as WorkspaceRole]?.has(permission) ?? false;
}

export function isPlatformSupport(role: string | undefined): boolean {
  return role === "support_admin";
}

export function usesClientPortal(role: string | undefined): boolean {
  return role === "client_viewer";
}

export function usesBillingOnlyShell(role: string | undefined): boolean {
  return role === "billing_admin";
}

export function resolveEntryPath(
  workspaceId: string,
  role: string | undefined,
  siteId?: string,
): string {
  if (usesClientPortal(role)) return `/client/${workspaceId}`;
  if (usesBillingOnlyShell(role)) return `/app/${workspaceId}/settings/billing`;
  if (isPlatformSupport(role)) return `/internal-admin/workspaces`;
  if (siteId) return `/app/${workspaceId}/sites/${siteId}/dashboard`;
  return `/app/${workspaceId}/onboarding`;
}
