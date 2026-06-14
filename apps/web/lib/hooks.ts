"use client";

import { useParams } from "next/navigation";
import { getApiClient } from "./api-client";

export function useSiteContext() {
  const params = useParams<{ workspaceId: string; siteId: string }>();
  const workspaceId = params.workspaceId;
  const siteId = params.siteId;
  const client = getApiClient(workspaceId);
  return { workspaceId, siteId, client };
}
