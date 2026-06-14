import type {
  ActionCandidate,
  AiVisibilityDashboard,
  ExposureDashboardMetrics,
  Opportunity,
  SerpMatrixResponse,
  Site,
  Workspace,
} from "@exposureflow/shared-types";

export type ExposureFlowClientOptions = {
  baseUrl: string;
  workspaceId?: string;
  token?: string;
};

function headers(options: ExposureFlowClientOptions): Record<string, string> {
  const h: Record<string, string> = { "Content-Type": "application/json" };
  if (options.token) h.Authorization = `Bearer ${options.token}`;
  if (options.workspaceId) h["X-Workspace-Id"] = options.workspaceId;
  return h;
}

async function request<T>(options: ExposureFlowClientOptions, path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${options.baseUrl}${path}`, {
    ...init,
    headers: { ...headers(options), ...(init?.headers as Record<string, string>) },
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`ExposureFlow API ${response.status}: ${text}`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export class ExposureFlowClient {
  constructor(private readonly options: ExposureFlowClientOptions) {}

  getDashboard(siteId: string): Promise<ExposureDashboardMetrics> {
    return request(this.options, `/api/v1/exposure/dashboard?site_id=${siteId}`);
  }

  listOpportunities(siteId: string): Promise<Opportunity[]> {
    return request(this.options, `/api/v1/exposure/sites/${siteId}/opportunities`);
  }

  listCandidates(siteId: string, status?: string): Promise<ActionCandidate[]> {
    const q = status ? `&status=${encodeURIComponent(status)}` : "";
    return request(this.options, `/api/v1/decisions/candidates?site_id=${siteId}${q}`);
  }

  approveCandidate(candidateId: string, rationale?: string): Promise<unknown> {
    return request(this.options, `/api/v1/decisions/candidates/${candidateId}/approve`, {
      method: "POST",
      body: JSON.stringify({ rationale }),
    });
  }

  rejectCandidate(candidateId: string, rationale?: string): Promise<unknown> {
    return request(this.options, `/api/v1/decisions/candidates/${candidateId}/reject`, {
      method: "POST",
      body: JSON.stringify({ rationale }),
    });
  }

  deferCandidate(candidateId: string, rationale?: string): Promise<unknown> {
    return request(this.options, `/api/v1/decisions/candidates/${candidateId}/defer`, {
      method: "POST",
      body: JSON.stringify({ rationale }),
    });
  }

  getSerpMatrix(siteId: string, clusterId?: string): Promise<SerpMatrixResponse> {
    const q = clusterId ? `&cluster_id=${clusterId}` : "";
    return request(this.options, `/api/v1/serp/matrix?site_id=${siteId}${q}`);
  }

  listSerpSnapshots(siteId: string): Promise<Array<Record<string, unknown>>> {
    return request(this.options, `/api/v1/serp/snapshots?site_id=${siteId}`);
  }

  runSerpSnapshot(siteId: string, keyword: string): Promise<{ job_run_id: string }> {
    return request(this.options, `/api/v1/serp/snapshots/run`, {
      method: "POST",
      body: JSON.stringify({ site_id: siteId, keyword, country: "TW", language: "zh-TW", device: "desktop" }),
    });
  }

  getAiDashboard(siteId: string): Promise<AiVisibilityDashboard> {
    return request(this.options, `/api/v1/ai-visibility/dashboard?site_id=${siteId}`);
  }

  listProbeSets(siteId: string): Promise<Array<Record<string, unknown>>> {
    return request(this.options, `/api/v1/ai-visibility/probe-sets?site_id=${siteId}`);
  }

  listCitations(siteId: string): Promise<Array<Record<string, unknown>>> {
    return request(this.options, `/api/v1/ai-visibility/citations?site_id=${siteId}`);
  }

  listBrandEntities(siteId: string): Promise<Array<Record<string, unknown>>> {
    return request(this.options, `/api/v1/ai-visibility/brand-entities?site_id=${siteId}`);
  }

  listSerpoRecords(siteId: string): Promise<Array<Record<string, unknown>>> {
    return request(this.options, `/api/v1/ai-visibility/serpo-records?site_id=${siteId}`);
  }

  listTopicClusters(siteId: string): Promise<Array<Record<string, unknown>>> {
    return request(this.options, `/api/v1/topics/clusters?site_id=${siteId}`);
  }

  listTopicNodes(siteId: string, clusterId?: string): Promise<Array<Record<string, unknown>>> {
    const q = clusterId ? `&cluster_id=${clusterId}` : "";
    return request(this.options, `/api/v1/topics/nodes?site_id=${siteId}${q}`);
  }

  listTechnicalIssues(siteId: string): Promise<Array<Record<string, unknown>>> {
    return request(this.options, `/api/v1/integrations/technical-issues?site_id=${siteId}`);
  }

  listActionOutcomes(siteId: string): Promise<Array<Record<string, unknown>>> {
    return request(this.options, `/api/v1/outcomes?site_id=${siteId}`);
  }

  listSyncStates(siteId?: string): Promise<Array<Record<string, unknown>>> {
    const q = siteId ? `?site_id=${siteId}` : "";
    return request(this.options, `/api/v1/integrations/sync-states${q}`);
  }

  triggerGscSync(siteId: string): Promise<{ job_run_id: string }> {
    return request(this.options, `/api/v1/integrations/gsc/sync`, {
      method: "POST",
      body: JSON.stringify({ site_id: siteId, input_json: {} }),
    });
  }

  triggerTechSeoCrawl(siteId: string): Promise<{ job_run_id: string }> {
    return request(this.options, `/api/v1/integrations/tech-seo/crawl`, {
      method: "POST",
      body: JSON.stringify({ site_id: siteId, input_json: {} }),
    });
  }

  listWorkspaces(): Promise<Workspace[]> {
    return request(this.options, `/api/v1/workspaces`);
  }

  listSites(): Promise<Site[]> {
    return request(this.options, `/api/v1/sites`);
  }

  listMembers(): Promise<Array<Record<string, unknown>>> {
    return request(this.options, `/api/v1/members`);
  }

  listStrategyIntakes(): Promise<Array<Record<string, unknown>>> {
    return request(this.options, `/api/v1/strategy/intakes`);
  }

  listKeywordPyramid(siteId: string): Promise<Array<Record<string, unknown>>> {
    return request(this.options, `/api/v1/strategy/keyword-pyramid?site_id=${siteId}`);
  }

  listDeliveryCommitments(): Promise<Array<Record<string, unknown>>> {
    return request(this.options, `/api/v1/strategy/delivery-commitments`);
  }

  getBrandProfile(siteId: string): Promise<Record<string, unknown> | null> {
    return request(this.options, `/api/v1/knowledge/brand-profile?site_id=${siteId}`);
  }

  listKnowledgeSources(siteId: string): Promise<Array<Record<string, unknown>>> {
    return request(this.options, `/api/v1/knowledge/sources?site_id=${siteId}`);
  }

  listExecutionJobs(siteId: string): Promise<Array<Record<string, unknown>>> {
    return request(this.options, `/api/v1/execution/jobs?site_id=${siteId}`);
  }

  listRoadmaps(siteId: string): Promise<Array<Record<string, unknown>>> {
    return request(this.options, `/api/v1/roadmaps?site_id=${siteId}`);
  }

  listReports(siteId?: string, reportType?: string): Promise<Array<Record<string, unknown>>> {
    const params = new URLSearchParams();
    if (siteId) params.set("site_id", siteId);
    if (reportType) params.set("report_type", reportType);
    const q = params.toString();
    return request(this.options, `/api/v1/reports${q ? `?${q}` : ""}`);
  }

  generateReport(body: {
    site_id: string;
    delivery_mode: string;
    title?: string;
    branding_json?: Record<string, unknown>;
  }): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/reports/generate`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  exportReport(reportId: string, format: "markdown" | "pdf" | "docx"): Promise<Blob> {
    return fetch(`${this.options.baseUrl}/api/v1/reports/${reportId}/export`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(this.options.token ? { Authorization: `Bearer ${this.options.token}` } : {}),
        ...(this.options.workspaceId ? { "X-Workspace-Id": this.options.workspaceId } : {}),
      },
      body: JSON.stringify({ format }),
    }).then(async (response) => {
      if (!response.ok) throw new Error(`Export failed ${response.status}`);
      return response.blob();
    });
  }

  getClientPortalDashboard(siteId: string): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/client-portal/dashboard?site_id=${siteId}`);
  }

  approveRoadmapItem(itemId: string, siteId: string, note?: string): Promise<unknown> {
    return request(this.options, `/api/v1/client-portal/roadmap-items/${itemId}/approve`, {
      method: "POST",
      body: JSON.stringify({ site_id: siteId, note }),
    });
  }

  rejectRoadmapItem(itemId: string, siteId: string, note?: string): Promise<unknown> {
    return request(this.options, `/api/v1/client-portal/roadmap-items/${itemId}/reject`, {
      method: "POST",
      body: JSON.stringify({ site_id: siteId, note }),
    });
  }

  devToken(email: string, name: string): Promise<{ access_token: string }> {
    return request(this.options, `/api/v1/auth/dev-token`, {
      method: "POST",
      body: JSON.stringify({ email, name }),
    });
  }
}

export function createClient(options: ExposureFlowClientOptions) {
  return new ExposureFlowClient(options);
}
