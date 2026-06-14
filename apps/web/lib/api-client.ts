"use client";

import { createClient } from "@exposureflow/sdk";
import { API_BASE_URL, storageKey } from "./config";

export function getApiClient(workspaceId?: string) {
  const token = typeof window !== "undefined" ? localStorage.getItem(storageKey("token")) : null;
  const ws =
    workspaceId ??
    (typeof window !== "undefined" ? localStorage.getItem(storageKey("workspaceId")) : null) ??
    undefined;
  return createClient({
    baseUrl: API_BASE_URL,
    token: token ?? undefined,
    workspaceId: ws ?? undefined,
  });
}

export async function ensureDevSession(email = "consultant@example.com", name = "Consultant") {
  const client = createClient({ baseUrl: API_BASE_URL });
  const { access_token } = await client.devToken(email, name);
  localStorage.setItem(storageKey("token"), access_token);
  const authed = createClient({ baseUrl: API_BASE_URL, token: access_token });
  const workspaces = await authed.listWorkspaces();
  if (workspaces[0]) {
    localStorage.setItem(storageKey("workspaceId"), workspaces[0].id);
  }
  const wsClient = createClient({
    baseUrl: API_BASE_URL,
    token: access_token,
    workspaceId: workspaces[0]?.id,
  });
  const sites = await wsClient.listSites();
  if (sites[0]) {
    localStorage.setItem(storageKey("siteId"), sites[0].id);
  }
  return { token: access_token, workspaceId: workspaces[0]?.id, siteId: sites[0]?.id };
}
