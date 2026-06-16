import type {
  ActionCandidate,
  AiVisibilityDashboard,
  ExposureDashboardMetrics,
  Opportunity,
  SerpMatrixResponse,
  Site,
  SiteCreateInput,
  SiteUpdateInput,
  Workspace,
  WorkspaceCreateInput,
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

  getDashboard(siteId: string, days = 28): Promise<ExposureDashboardMetrics> {
    return request(this.options, `/api/v1/exposure/dashboard?site_id=${siteId}&days=${days}`);
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

  createProbeSet(body: {
    site_id: string;
    name: string;
    prompts_json?: string[];
    surfaces_json?: string[];
    schedule?: string | null;
    active?: boolean;
  }): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/ai-visibility/probe-sets?site_id=${body.site_id}`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  listCitations(siteId: string): Promise<Array<Record<string, unknown>>> {
    return request(this.options, `/api/v1/ai-visibility/citations?site_id=${siteId}`);
  }

  listAiProbeRuns(siteId: string, probeSetId?: string): Promise<Array<Record<string, unknown>>> {
    const q = probeSetId ? `&probe_set_id=${encodeURIComponent(probeSetId)}` : "";
    return request(this.options, `/api/v1/ai-visibility/runs?site_id=${siteId}${q}`);
  }

  listBrandEntities(siteId: string): Promise<Array<Record<string, unknown>>> {
    return request(this.options, `/api/v1/ai-visibility/brand-entities?site_id=${siteId}`);
  }

  createBrandEntity(body: {
    site_id: string;
    canonical_name: string;
    entity_type?: string;
    aliases_json?: string[];
    description?: string | null;
    official_profiles_json?: Record<string, unknown>;
  }): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/ai-visibility/brand-entities?site_id=${body.site_id}`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  listSerpoRecords(siteId: string): Promise<Array<Record<string, unknown>>> {
    return request(this.options, `/api/v1/ai-visibility/serpo-records?site_id=${siteId}`);
  }

  createSerpoRecord(body: {
    site_id: string;
    brand_query: string;
    keyword?: string;
    first_page_positive_count?: number;
    first_page_neutral_count?: number;
    first_page_negative_count?: number;
    first_page_wrong_info_count?: number;
    recommended_actions_json?: Record<string, unknown>;
  }): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/ai-visibility/serpo-records?site_id=${body.site_id}`, {
      method: "POST",
      body: JSON.stringify(body),
    });
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

  listIntegrationCredentials(): Promise<
    Array<{
      id: string;
      site_id: string | null;
      provider: string;
      credential_name: string;
      credential_type: string;
      status: string;
    }>
  > {
    return request(this.options, `/api/v1/integrations/credentials`);
  }

  listGscPerformance(
    siteId: string,
    opts?: { query?: string; page?: string; limit?: number },
  ): Promise<Array<Record<string, unknown>>> {
    const params = new URLSearchParams({ site_id: siteId });
    if (opts?.query) params.set("query", opts.query);
    if (opts?.page) params.set("page", opts.page);
    if (opts?.limit != null) params.set("limit", String(opts.limit));
    return request(this.options, `/api/v1/integrations/gsc/performance?${params}`);
  }

  getGscDataSummary(
    siteId: string,
    topQueries?: number,
  ): Promise<{
    total_rows: number;
    distinct_queries: number;
    distinct_pages: number;
    earliest_date: string | null;
    latest_date: string | null;
    top_queries: Array<{
      query: string;
      impressions: number;
      clicks: number;
      position: number;
    }>;
  }> {
    const params = new URLSearchParams({ site_id: siteId });
    if (topQueries != null) params.set("top_queries", String(topQueries));
    return request(this.options, `/api/v1/integrations/gsc/summary?${params}`);
  }

  triggerGscSync(
    siteId: string,
    inputJson?: Record<string, unknown>,
  ): Promise<{ job_run_id: string; status: string }> {
    return request(this.options, `/api/v1/integrations/gsc/sync`, {
      method: "POST",
      body: JSON.stringify({ site_id: siteId, input_json: inputJson ?? {} }),
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

  getMe(): Promise<{ user: Record<string, unknown>; workspaces: Array<Record<string, unknown>> }> {
    return request(this.options, `/api/v1/me`);
  }

  listSites(): Promise<Site[]> {
    return request(this.options, `/api/v1/sites`);
  }

  getSite(siteId: string): Promise<Site> {
    return request(this.options, `/api/v1/sites/${siteId}`);
  }

  createSite(body: SiteCreateInput): Promise<Site> {
    return request(this.options, `/api/v1/sites`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  updateSite(siteId: string, body: SiteUpdateInput): Promise<Site> {
    return request(this.options, `/api/v1/sites/${siteId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
  }

  createWorkspace(body: WorkspaceCreateInput): Promise<Workspace> {
    return request(this.options, `/api/v1/workspaces`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  listMembers(): Promise<Array<Record<string, unknown>>> {
    return request(this.options, `/api/v1/members`);
  }

  updateMemberRole(memberUserId: string, role: string): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/members/${memberUserId}`, {
      method: "PATCH",
      body: JSON.stringify({ role }),
    });
  }

  createInvitation(email: string, role: string): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/invitations`, {
      method: "POST",
      body: JSON.stringify({ email, role }),
    });
  }

  listStrategyIntakes(siteId: string): Promise<Array<Record<string, unknown>>> {
    return request(this.options, `/api/v1/strategy/intakes?site_id=${siteId}`);
  }

  getCurrentStrategyIntake(siteId: string): Promise<Record<string, unknown> | null> {
    return request(this.options, `/api/v1/strategy/intakes/current?site_id=${siteId}`);
  }

  createStrategyIntake(body: {
    site_id: string;
    company_summary?: string | null;
    market_notes?: string | null;
    customer_segments_json?: string[];
    domestic_markets_json?: string[];
    export_markets_json?: string[];
    sales_regions_json?: string[];
    strategic_goals_json?: string[];
    constraints_json?: string[];
    change_summary?: string | null;
  }): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/strategy/intakes`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  forkStrategyIntake(intakeId: string): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/strategy/intakes/${intakeId}/fork`, {
      method: "POST",
      body: JSON.stringify({}),
    });
  }

  previewStrategyIntakeImpact(intakeId: string): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/strategy/intakes/${intakeId}/impact-preview`);
  }

  updateStrategyIntake(
    intakeId: string,
    body: Partial<{
      company_summary: string | null;
      market_notes: string | null;
      customer_segments_json: string[];
      domestic_markets_json: string[];
      export_markets_json: string[];
      sales_regions_json: string[];
      strategic_goals_json: string[];
      constraints_json: string[];
      change_summary: string | null;
    }>,
  ): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/strategy/intakes/${intakeId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
  }

  approveStrategyIntake(intakeId: string): Promise<{
    intake: Record<string, unknown>;
    impact: Record<string, unknown>;
  }> {
    return request(this.options, `/api/v1/strategy/intakes/${intakeId}/approve`, {
      method: "POST",
      body: JSON.stringify({}),
    });
  }

  reapplyCurrentStrategyIntake(siteId: string): Promise<{
    intake: Record<string, unknown>;
    impact: Record<string, unknown>;
  }> {
    return request(this.options, `/api/v1/strategy/intakes/current/reapply?site_id=${siteId}`, {
      method: "POST",
      body: JSON.stringify({}),
    });
  }

  listKeywordPyramid(
    siteId: string,
    filters?: { status?: string; market?: string; language?: string },
  ): Promise<Array<Record<string, unknown>>> {
    const params = new URLSearchParams({ site_id: siteId });
    if (filters?.status) params.set("status", filters.status);
    if (filters?.market) params.set("market", filters.market);
    if (filters?.language) params.set("language", filters.language);
    return request(this.options, `/api/v1/strategy/keyword-pyramid?${params.toString()}`);
  }

  listConstraintRules(
    siteId: string,
    activeOnly = true,
  ): Promise<Array<Record<string, unknown>>> {
    return request(
      this.options,
      `/api/v1/strategy/constraint-rules?site_id=${siteId}&active_only=${activeOnly}`,
    );
  }

  createKeywordPyramidNode(body: {
    site_id: string;
    keyword: string;
    node_type: string;
    parent_id?: string | null;
    product_service_scope_id?: string | null;
    intent?: string | null;
    target_market?: string | null;
    language?: string | null;
    keyword_level?: string | null;
    funnel_stage?: string | null;
    is_target?: boolean;
    business_fit_status?: string;
    priority?: number;
    created_by?: string;
  }): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/strategy/keyword-pyramid`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  updateKeywordPyramidNode(
    nodeId: string,
    body: Partial<{
      keyword: string;
      node_type: string;
      parent_id: string | null;
      product_service_scope_id: string | null;
      intent: string | null;
      target_market: string | null;
      language: string | null;
      keyword_level: string | null;
      funnel_stage: string | null;
      is_target: boolean;
      business_fit_status: string;
      priority: number;
    }>,
  ): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/strategy/keyword-pyramid/${nodeId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
  }

  approveKeywordPyramidNode(nodeId: string): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/strategy/keyword-pyramid/${nodeId}/approve`, {
      method: "POST",
      body: JSON.stringify({}),
    });
  }

  deleteKeywordPyramidNode(nodeId: string): Promise<void> {
    return request(this.options, `/api/v1/strategy/keyword-pyramid/${nodeId}`, {
      method: "DELETE",
    });
  }

  bulkImportKeywordPyramid(body: {
    site_id: string;
    created_by?: string;
    rows: Array<{
      keyword: string;
      node_type?: string;
      parent_keyword?: string | null;
      intent?: string | null;
      target_market?: string | null;
      language?: string | null;
      keyword_level?: string | null;
      funnel_stage?: string | null;
      is_target?: boolean;
      business_fit_status?: string;
      priority?: number;
      product_service_scope_id?: string | null;
    }>;
  }): Promise<{ created: number; skipped: number; errors: string[] }> {
    return request(this.options, `/api/v1/strategy/keyword-pyramid/bulk-import`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  syncPyramidTopicBridge(siteId: string): Promise<{ linked: number; skipped: number }> {
    return request(
      this.options,
      `/api/v1/strategy/keyword-pyramid/sync-topic-bridge?site_id=${siteId}`,
      { method: "POST", body: JSON.stringify({}) },
    );
  }

  coldStartResearch(body: {
    site_id: string;
    seed_keywords: string[];
    market?: string | null;
    language?: string | null;
    include_paa?: boolean;
    include_related?: boolean;
    max_expansions?: number;
    max_seeds?: number;
  }): Promise<{ job_id: string; status: string }> {
    return request(this.options, `/api/v1/strategy/cold-start-research`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  listProductScopes(siteId: string, status?: string): Promise<Array<Record<string, unknown>>> {
    const q = status ? `&status=${encodeURIComponent(status)}` : "";
    return request(this.options, `/api/v1/strategy/product-scopes?site_id=${siteId}${q}`);
  }

  listDeliveryCommitments(siteId: string): Promise<Array<Record<string, unknown>>> {
    return request(this.options, `/api/v1/strategy/delivery-commitments?site_id=${siteId}`);
  }

  createDeliveryCommitment(body: {
    site_id: string;
    period?: string;
    new_content_target?: number;
    refresh_target?: number;
    faq_schema_target?: number;
    technical_fix_target?: number;
    report_target?: number;
    effective_from: string;
    effective_to?: string | null;
    notes?: string | null;
  }): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/strategy/delivery-commitments?site_id=${body.site_id}`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  deactivateDeliveryCommitment(commitmentId: string): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/strategy/delivery-commitments/${commitmentId}/deactivate`, {
      method: "POST",
      body: JSON.stringify({}),
    });
  }

  listCompetitors(siteId: string): Promise<Array<Record<string, unknown>>> {
    return request(this.options, `/api/v1/competitors?site_id=${siteId}`);
  }

  createCompetitor(body: {
    site_id: string;
    name: string;
    domain: string;
    aliases?: string[];
    notes?: string | null;
  }): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/competitors?site_id=${body.site_id}`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  deleteCompetitor(competitorId: string): Promise<{ status: string }> {
    return request(this.options, `/api/v1/competitors/${competitorId}`, {
      method: "DELETE",
    });
  }

  getBrandProfile(siteId: string): Promise<Record<string, unknown> | null> {
    return request(this.options, `/api/v1/knowledge/brand-profile?site_id=${siteId}`);
  }

  upsertBrandProfile(body: {
    site_id?: string;
    canonical_brand_name: string;
    brand_voice_json?: Record<string, unknown>;
    positioning_json?: Record<string, unknown>;
    target_markets_json?: string[];
    buyer_personas_json?: string[];
    compliance_policy_json?: Record<string, unknown>;
    default_review_policy?: string;
  }): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/knowledge/brand-profile`, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
  }

  listKnowledgeSources(siteId: string): Promise<Array<Record<string, unknown>>> {
    return request(this.options, `/api/v1/knowledge/sources?site_id=${siteId}`);
  }

  listExecutionJobs(siteId: string): Promise<Array<Record<string, unknown>>> {
    return request(this.options, `/api/v1/execution/jobs?site_id=${siteId}`);
  }

  createExecutionJob(body: {
    site_id: string;
    job_type: string;
    decision_id?: string;
    opportunity_id?: string;
    executor_type?: string;
    input_json?: Record<string, unknown>;
  }): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/execution/jobs`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  listGenerationRuns(siteId: string, status?: string): Promise<Array<Record<string, unknown>>> {
    const q = status ? `&status=${encodeURIComponent(status)}` : "";
    return request(this.options, `/api/v1/content/generation-runs?site_id=${siteId}${q}`);
  }

  buildSourcePack(body: {
    site_id: string;
    opportunity_id?: string;
    execution_job_id?: string;
    market?: string;
    language?: string;
    brief_type?: string;
  }): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/content/source-packs/build`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  buildContentBrief(body: {
    site_id: string;
    opportunity_id: string;
    source_pack_id: string;
    decision_id?: string;
  }): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/content/briefs/build`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  createGenerationRun(body: {
    site_id: string;
    execution_job_id: string;
    content_brief_id: string;
    generation_mode?: string;
    review_level?: string;
    auto_compile?: boolean;
  }): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/content/generation-runs`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  approveGenerationRun(runId: string, rationale?: string, override = false): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/content/generation-runs/${runId}/approve`, {
      method: "POST",
      body: JSON.stringify({ rationale, override }),
    });
  }

  requestChangesGenerationRun(runId: string, notes: string): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/content/generation-runs/${runId}/request-changes`, {
      method: "POST",
      body: JSON.stringify({ notes }),
    });
  }

  createKnowledgeSource(body: {
    site_id?: string;
    title: string;
    source_type: string;
    source_url?: string;
    content_text?: string;
  }): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/knowledge/sources`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  approveKnowledgeSource(sourceId: string): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/knowledge/sources/${sourceId}/approve`, { method: "POST" });
  }

  triggerKnowledgeIngest(sourceId: string): Promise<{ job_run_id: string }> {
    return request(this.options, `/api/v1/knowledge/sources/${sourceId}/ingest`, { method: "POST" });
  }

  submitProbeRun(body: {
    site_id: string;
    probe_set_id: string;
    surface: string;
    prompt: string;
    answer_text: string;
    cited_urls?: string[];
    mentioned_brands?: string[];
    sentiment?: string;
  }): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/ai-visibility/runs/assisted`, {
      method: "POST",
      body: JSON.stringify({ ...body, probe_mode: "assisted_manual" }),
    });
  }

  listRoadmaps(siteId: string): Promise<Array<Record<string, unknown>>> {
    return request(this.options, `/api/v1/roadmaps?site_id=${siteId}`);
  }

  buildRoadmap(siteId: string, body?: { name?: string; description?: string }): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/roadmaps/build?site_id=${siteId}`, {
      method: "POST",
      body: JSON.stringify({ site_id: siteId, ...body }),
    });
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

  devToken(email: string, name: string, role?: string): Promise<{ access_token: string }> {
    return request(this.options, `/api/v1/auth/dev-token`, {
      method: "POST",
      body: JSON.stringify({ email, name, role }),
    });
  }

  stepUpTwoFactor(code: string): Promise<{ access_token: string }> {
    return request(this.options, `/api/v1/auth/2fa/step-up`, {
      method: "POST",
      body: JSON.stringify({ code }),
    });
  }

  listPlans(): Promise<Array<Record<string, unknown>>> {
    return request(this.options, `/api/v1/billing/plans`);
  }

  getSubscription(): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/billing/subscription`);
  }

  getBillingUsage(): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/billing/usage`);
  }

  startCheckout(planCode: string, billingInterval = "month"): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/billing/checkout`, {
      method: "POST",
      body: JSON.stringify({ plan_code: planCode, billing_interval: billingInterval }),
    });
  }

  openBillingPortal(): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/billing/portal`, { method: "POST" });
  }

  getAgencyDashboard(): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/agency/dashboard`);
  }

  updateWorkspaceBranding(body: Record<string, unknown>): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/billing/branding`, {
      method: "PUT",
      body: JSON.stringify(body),
    });
  }

  listNotifications(status?: string): Promise<Array<Record<string, unknown>>> {
    const q = status ? `?status=${encodeURIComponent(status)}` : "";
    return request(this.options, `/api/v1/notifications${q}`);
  }

  markNotificationRead(notificationId: string): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/notifications/${notificationId}/read`, { method: "POST" });
  }

  markAllNotificationsRead(): Promise<{ status: string }> {
    return request(this.options, `/api/v1/notifications/read-all`, { method: "POST" });
  }

  createSupportTicket(body: { subject: string; description: string; priority?: string }): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/support/tickets`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  listSupportTickets(): Promise<Array<Record<string, unknown>>> {
    return request(this.options, `/api/v1/support/tickets`);
  }

  getPublicStatus(): Promise<Array<Record<string, unknown>>> {
    return request(this.options, `/api/v1/status`);
  }

  internalListWorkspaces(): Promise<Array<Record<string, unknown>>> {
    return request(this.options, `/api/v1/internal/workspaces`);
  }

  internalListAccounts(): Promise<Array<Record<string, unknown>>> {
    return request(this.options, `/api/v1/internal/accounts`);
  }

  internalSearchUsers(email?: string): Promise<Array<Record<string, unknown>>> {
    const q = email ? `?email=${encodeURIComponent(email)}` : "";
    return request(this.options, `/api/v1/internal/users${q}`);
  }

  internalListJobs(params?: { workspace_id?: string; status?: string }): Promise<Array<Record<string, unknown>>> {
    const search = new URLSearchParams();
    if (params?.workspace_id) search.set("workspace_id", params.workspace_id);
    if (params?.status) search.set("status", params.status);
    const q = search.toString();
    return request(this.options, `/api/v1/internal/jobs${q ? `?${q}` : ""}`);
  }

  internalListSyncStates(params?: { workspace_id?: string; failing_only?: boolean }): Promise<Array<Record<string, unknown>>> {
    const search = new URLSearchParams();
    if (params?.workspace_id) search.set("workspace_id", params.workspace_id);
    if (params?.failing_only) search.set("failing_only", "true");
    const q = search.toString();
    return request(this.options, `/api/v1/internal/sync-states${q ? `?${q}` : ""}`);
  }

  internalListAuditLogs(params?: { workspace_id?: string; action_prefix?: string }): Promise<Array<Record<string, unknown>>> {
    const search = new URLSearchParams();
    if (params?.workspace_id) search.set("workspace_id", params.workspace_id);
    if (params?.action_prefix) search.set("action_prefix", params.action_prefix);
    const q = search.toString();
    return request(this.options, `/api/v1/internal/audit-logs${q ? `?${q}` : ""}`);
  }

  internalUpdateFeatureFlags(workspaceId: string, featureFlags: Record<string, unknown>): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/internal/workspaces/${workspaceId}/feature-flags`, {
      method: "PATCH",
      body: JSON.stringify({ feature_flags: featureFlags }),
    });
  }

  internalCsActivation(): Promise<Array<Record<string, unknown>>> {
    return request(this.options, `/api/v1/internal/cs/activation`);
  }

  internalCsFunnel(): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/internal/cs/onboarding-funnel`);
  }

  internalIntegrationHealth(): Promise<Array<Record<string, unknown>>> {
    return request(this.options, `/api/v1/internal/integration-health`);
  }

  internalProviderCosts(days = 30): Promise<Array<Record<string, unknown>>> {
    return request(this.options, `/api/v1/internal/provider-costs?days=${days}`);
  }

  internalListSupportTickets(workspaceId?: string): Promise<Array<Record<string, unknown>>> {
    const q = workspaceId ? `?workspace_id=${workspaceId}` : "";
    return request(this.options, `/api/v1/internal/support/tickets${q}`);
  }

  internalListStatusIncidents(): Promise<Array<Record<string, unknown>>> {
    return request(this.options, `/api/v1/internal/status/incidents`);
  }

  internalCreateStatusIncident(body: Record<string, unknown>): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/internal/status/incidents`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  internalImpersonate(body: { target_user_id: string; workspace_id?: string; reason: string }): Promise<{ access_token: string }> {
    return request(this.options, `/api/v1/internal/impersonate`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  getLaunchReadiness(): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/launch/readiness`);
  }

  internalLaunchChecklist(): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/internal/launch/checklist`);
  }

  internalBusinessMetrics(days = 30): Promise<Record<string, unknown>> {
    return request(this.options, `/api/v1/internal/business-metrics?days=${days}`);
  }
}

export function createClient(options: ExposureFlowClientOptions) {
  return new ExposureFlowClient(options);
}
