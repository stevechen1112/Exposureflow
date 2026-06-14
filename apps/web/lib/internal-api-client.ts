"use client";

import { createClient } from "@exposureflow/sdk";
import { API_BASE_URL, storageKey } from "./config";

export function getInternalApiClient() {
  const token = typeof window !== "undefined" ? localStorage.getItem(storageKey("token")) : null;
  return createClient({
    baseUrl: API_BASE_URL,
    token: token ?? undefined,
  });
}

export async function ensureInternalAdminSession() {
  const client = createClient({ baseUrl: API_BASE_URL });
  const { access_token } = await client.devToken("support@example.com", "Platform Support");
  localStorage.setItem(storageKey("token"), access_token);
  const authed = createClient({ baseUrl: API_BASE_URL, token: access_token });
  const workspaces = await authed.listWorkspaces();
  if (workspaces[0]) {
    localStorage.setItem(storageKey("workspaceId"), workspaces[0].id);
  }
  return { token: access_token, client: authed };
}
