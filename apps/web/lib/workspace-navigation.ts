import { storageKey } from "./config";

/** Resolve target path when switching workspace while preserving context. */
export function pathAfterWorkspaceSwitch(
  currentPath: string,
  fromWorkspaceId: string,
  toWorkspaceId: string,
): string {
  const suffix = currentPath.replace(`/app/${fromWorkspaceId}`, "") || "";

  if (suffix.startsWith("/consultant-inbox")) {
    return `/app/${toWorkspaceId}/consultant-inbox`;
  }
  if (suffix.startsWith("/agency")) {
    return `/app/${toWorkspaceId}/agency`;
  }
  if (suffix.startsWith("/settings") || suffix.startsWith("/onboarding")) {
    return `/app/${toWorkspaceId}${suffix}`;
  }
  if (suffix.match(/^\/sites\/[^/]+/)) {
    return `/app/${toWorkspaceId}/settings/sites`;
  }
  return `/app/${toWorkspaceId}/consultant-inbox`;
}

export function persistWorkspaceSwitch(workspaceId: string) {
  if (typeof window === "undefined") return;
  localStorage.setItem(storageKey("workspaceId"), workspaceId);
}

export function persistSiteSwitch(siteId: string) {
  if (typeof window === "undefined") return;
  localStorage.setItem(storageKey("siteId"), siteId);
}

export function workspaceDisplayLabel(name: string, clientName?: string | null) {
  return clientName?.trim() || name;
}
