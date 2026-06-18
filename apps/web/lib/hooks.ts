"use client";

import { useMemo } from "react";
import { useParams } from "next/navigation";
import { getApiClient } from "./api-client";

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export function isValidSiteId(siteId: string | undefined): siteId is string {
  return !!siteId && siteId !== "null" && siteId !== "undefined" && UUID_RE.test(siteId);
}

export function useSiteContext() {
  const params = useParams<{ workspaceId: string; siteId: string }>();
  const workspaceId = params.workspaceId;
  const siteIdParam = params.siteId;
  // SiteLayout validates and redirects if invalid, so siteId is always valid here
  const siteId = isValidSiteId(siteIdParam) ? siteIdParam : siteIdParam;
  const client = useMemo(() => getApiClient(workspaceId), [workspaceId]);
  return { workspaceId, siteId, siteIdParam, client };
}

export function useWorkspaceClient() {
  const params = useParams<{ workspaceId: string }>();
  const workspaceId = params.workspaceId;
  const client = useMemo(() => getApiClient(workspaceId), [workspaceId]);
  return { workspaceId, client };
}
