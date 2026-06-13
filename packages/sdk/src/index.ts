import type { ExposureDashboardMetrics } from "@exposureflow/shared-types";

export type ExposureFlowClientOptions = {
  baseUrl: string;
  workspaceId?: string;
  token?: string;
};

export class ExposureFlowClient {
  constructor(private readonly options: ExposureFlowClientOptions) {}

  async getDashboard(siteId: string): Promise<ExposureDashboardMetrics> {
    const url = new URL("/api/v1/exposure/dashboard", this.options.baseUrl);
    url.searchParams.set("site_id", siteId);

    const headers: Record<string, string> = {};
    if (this.options.token) headers.Authorization = `Bearer ${this.options.token}`;
    if (this.options.workspaceId) headers["X-Workspace-Id"] = this.options.workspaceId;

    const response = await fetch(url, { headers });
    if (!response.ok) {
      throw new Error(`ExposureFlow API error: ${response.status}`);
    }
    return response.json() as Promise<ExposureDashboardMetrics>;
  }
}

export function createClient(options: ExposureFlowClientOptions) {
  return new ExposureFlowClient(options);
}
