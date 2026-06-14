export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

/** When false, web app expects Clerk (production); dev bootstrap is disabled. */
export const DEV_AUTH_ENABLED =
  process.env.NEXT_PUBLIC_ENABLE_DEV_AUTH === "true" ||
  process.env.NODE_ENV === "development";

export function storageKey(name: string) {
  return `exposureflow:${name}`;
}
