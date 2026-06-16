"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import type { Site } from "@exposureflow/shared-types";
import { PageHeader } from "@/components/PageHeader";
import { getApiClient } from "@/lib/api-client";
import { storageKey } from "@/lib/config";

type CheckStep = {
  id: string;
  label: string;
  description: string;
  status: "done" | "pending" | "action_required";
  action?: string;
  href?: string;
  /** SEO 策略文件對應章節 */
  seoRef?: string;
};

function StepIcon({ status }: { status: CheckStep["status"] }) {
  if (status === "done")
    return (
      <span
        style={{
          width: 28,
          height: 28,
          borderRadius: "50%",
          background: "var(--success)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
          fontSize: "0.9rem",
        }}
      >
        ✓
      </span>
    );
  if (status === "action_required")
    return (
      <span
        style={{
          width: 28,
          height: 28,
          borderRadius: "50%",
          background: "var(--warning)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
          fontSize: "0.9rem",
          color: "var(--text)",
        }}
      >
        !
      </span>
    );
  return (
    <span
      style={{
        width: 28,
        height: 28,
        borderRadius: "50%",
        border: "2px solid var(--border)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
        fontSize: "0.8rem",
        color: "var(--muted)",
      }}
    >
      ○
    </span>
  );
}

export default function OnboardingPage() {
  const params = useParams<{ workspaceId: string }>();
  const router = useRouter();
  const client = getApiClient(params.workspaceId);

  const [sites, setSites] = useState<Site[]>([]);
  const [intakes, setIntakes] = useState<Array<Record<string, unknown>>>([]);
  const [syncStates, setSyncStates] = useState<Array<Record<string, unknown>>>([]);
  const [knowledgeSources, setKnowledgeSources] = useState<Array<Record<string, unknown>>>([]);
  const [keywordNodes, setKeywordNodes] = useState<Array<Record<string, unknown>>>([]);
  const [competitors, setCompetitors] = useState<Array<Record<string, unknown>>>([]);
  const [brandProfile, setBrandProfile] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [storedSiteId, setStoredSiteId] = useState<string | null>(null);

  useEffect(() => {
    const sid = localStorage.getItem(storageKey("siteId"));
    setStoredSiteId(sid);
    client
      .listSites()
      .then((s) => {
        const activeSiteId = s[0]?.id ?? sid;
        if (!activeSiteId) {
          return Promise.all([
            Promise.resolve(s),
            Promise.resolve([] as Array<Record<string, unknown>>),
            client.listSyncStates(),
            Promise.resolve([] as Array<Record<string, unknown>>),
            Promise.resolve([] as Array<Record<string, unknown>>),
            Promise.resolve([] as Array<Record<string, unknown>>),
            Promise.resolve(null as Record<string, unknown> | null),
          ]);
        }
        return Promise.all([
          Promise.resolve(s),
          client.listStrategyIntakes(activeSiteId),
          client.listSyncStates(),
          client.listKnowledgeSources(activeSiteId).catch(
            () => [] as Array<Record<string, unknown>>,
          ),
          client.listKeywordPyramid(activeSiteId).catch(() => [] as Array<Record<string, unknown>>),
          client.listCompetitors(activeSiteId).catch(() => [] as Array<Record<string, unknown>>),
          client.getBrandProfile(activeSiteId).catch(() => null as Record<string, unknown> | null),
        ]);
      })
      .then(([s, i, sync, ks, keywords, comps, bp]) => {
        const siteList = s as Site[];
        setSites(siteList);
        setIntakes(i as Array<Record<string, unknown>>);
        setSyncStates(sync as Array<Record<string, unknown>>);
        setKnowledgeSources(ks as Array<Record<string, unknown>>);
        setKeywordNodes(keywords as Array<Record<string, unknown>>);
        setCompetitors(comps as Array<Record<string, unknown>>);
        setBrandProfile(bp as Record<string, unknown> | null);
        if (siteList[0]) localStorage.setItem(storageKey("siteId"), siteList[0].id);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [client]);

  const siteId = sites[0]?.id ?? storedSiteId;
  const hasGscSync = syncStates.some((s) => String(s.provider) === "gsc" && s.last_success_at);
  const hasApprovedIntake = intakes.some(
    (i) =>
      (Boolean(i.is_current) && String(i.status) === "approved") ||
      String(i.status) === "approved" ||
      String(i.status) === "active",
  );
  const hasKeywordPyramid = keywordNodes.some(
    (node) =>
      String(node.business_fit_status) === "in_scope" &&
      Boolean(node.approved_at) &&
      ["pillar", "cluster", "long_tail"].includes(String(node.node_type)),
  );
  const hasApprovedKnowledge = knowledgeSources.some(
    (ks) =>
      String(ks.approval_status) === "approved" ||
      String(ks.status) === "approved",
  );
  const hasCompetitors = competitors.length > 0;
  const hasBrandProfile = brandProfile != null && String(brandProfile.canonical_brand_name ?? "").length > 0;

  function buildSteps(): CheckStep[] {
    return [
      {
        id: "site",
        label: "建立站點",
        description: "設定目標網站的 domain、產業、商業模式與市場設定",
        status: sites.length > 0 ? "done" : "action_required",
        action: sites.length === 0 ? "前往站點管理" : undefined,
        href: `/app/${params.workspaceId}/settings/sites`,
        seoRef: "策略文件 §一 專案目標與策略邊界",
      },
      {
        id: "gsc",
        label: "連接 Google Search Console",
        description: "取得自然搜尋曝光資料——所有分析的數據基礎。建議使用 service account 授權並設定每日自動同步",
        status: hasGscSync
          ? "done"
          : syncStates.some((s) => String(s.provider) === "gsc")
            ? "pending"
            : "action_required",
        action: !hasGscSync ? "前往 GSC 連線" : undefined,
        href: !hasGscSync ? `/app/${params.workspaceId}/settings/integrations` : undefined,
        seoRef: "策略文件 §九 技術基礎：確保內容能被索引",
      },
      {
        id: "intake",
        label: "完成策略 Intake",
        description: "定義 North Star、服務摘要、銷售區域、目標客群與限制條件。核准後自動影響關鍵字金字塔與機會評分",
        status: hasApprovedIntake ? "done" : intakes.length > 0 ? "pending" : "action_required",
        action: !hasApprovedIntake ? "前往策略設定" : undefined,
        href: !hasApprovedIntake ? `/app/${params.workspaceId}/sites/${siteId}/strategy` : undefined,
        seoRef: "策略文件 §一 專案目標、§三 關鍵字策略",
      },
      {
        id: "competitors",
        label: "建立競爭對手清單",
        description: "登錄 3-5 個主要競爭對手 domain，用於 SERP 版位歸屬、AI 提及分類與曝光差距分析",
        status: hasCompetitors ? "done" : "action_required",
        action: !hasCompetitors ? "前往競爭對手管理" : undefined,
        href: !hasCompetitors
          ? `/app/${params.workspaceId}/sites/${siteId}/competitors`
          : undefined,
        seoRef: "策略文件 §二 第 2 週：曝光版位矩陣與競品分析",
      },
      {
        id: "keywords",
        label: "建立 Keyword Pyramid",
        description: "定義 pillar / cluster / long-tail 三層關鍵字架構。建議至少 15-20 個核准節點，並執行 Cold-start 研究擴充候選字",
        status: hasKeywordPyramid ? "done" : siteId ? "action_required" : "pending",
        action: !hasKeywordPyramid && siteId ? "前往關鍵字金字塔" : undefined,
        href:
          !hasKeywordPyramid && siteId
            ? `/app/${params.workspaceId}/sites/${siteId}/keyword-pyramid`
            : undefined,
        seoRef: "策略文件 §三 關鍵字金字塔、§四 主題集群",
      },
      {
        id: "brand",
        label: "建立 Brand Profile",
        description: "設定品牌正式名稱、品牌聲音、定位、目標市場與 buyer personas——AI 引用與內容生成的品牌一致性基礎",
        status: hasBrandProfile ? "done" : "action_required",
        action: !hasBrandProfile ? "前往品牌設定" : undefined,
        href: !hasBrandProfile
          ? `/app/${params.workspaceId}/sites/${siteId}/knowledge`
          : undefined,
        seoRef: "策略文件 §六 AI 搜尋引用策略、Brand Entity 訊號",
      },
      {
        id: "knowledge",
        label: "匯入並核准知識來源",
        description: "官網內容、FAQ、服務流程、品牌文件——讓系統理解你的業務才能正確評估曝光機會",
        status: hasApprovedKnowledge
          ? "done"
          : knowledgeSources.length > 0
            ? "pending"
            : "action_required",
        action: "前往知識庫",
        href: siteId
          ? `/app/${params.workspaceId}/sites/${siteId}/knowledge`
          : undefined,
        seoRef: "策略文件 §六 AI 引用友善內容格式、§四 內容佈局",
      },
      {
        id: "dashboard",
        label: "查看曝光儀表板",
        description: "確認 baseline 資料已匯入，追蹤自然曝光、排名分佈、Topic Cluster 覆蓋與 AI 引用",
        status:
          hasGscSync && sites.length > 0 && hasApprovedIntake ? "done" : "pending",
        action: siteId ? "進入儀表板" : undefined,
        href: siteId
          ? `/app/${params.workspaceId}/sites/${siteId}/dashboard`
          : undefined,
        seoRef: "策略文件 §十一 成效追蹤方式：主要 KPI",
      },
    ];
  }

  const steps = buildSteps();
  const doneCount = steps.filter((s) => s.status === "done").length;
  const progress = Math.round((doneCount / steps.length) * 100);

  return (
    <>
      <PageHeader
        title="Onboarding"
        subtitle="完成以下設定步驟，開始追蹤您的自然曝光版圖"
      />

      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}

      {!loading && (
        <>
          {/* Progress bar */}
          <div className="card" style={{ marginBottom: "1.5rem" }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "0.75rem",
              }}
            >
              <span style={{ fontWeight: 600 }}>設定進度</span>
              <span
                style={{
                  fontSize: "0.88rem",
                  color: progress === 100 ? "var(--success)" : "var(--muted)",
                }}
              >
                {doneCount} / {steps.length} 已完成
              </span>
            </div>
            <div
              style={{
                height: 8,
                background: "var(--surface-2)",
                borderRadius: 999,
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  width: `${progress}%`,
                  height: "100%",
                  background:
                    progress === 100
                      ? "var(--success)"
                      : progress >= 50
                        ? "var(--accent)"
                        : "var(--warning)",
                  borderRadius: 999,
                  transition: "width 0.4s ease",
                }}
              />
            </div>
            {progress === 100 && (
              <p style={{ color: "var(--success)", margin: "0.75rem 0 0", fontSize: "0.9rem" }}>
                設定完成！您的 ExposureFlow 工作區已就緒。
              </p>
            )}
            <p
              style={{
                margin: "0.5rem 0 0",
                fontSize: "0.75rem",
                color: "var(--muted)",
                opacity: 0.7,
              }}
            >
              🗓 對應策略文件第 1 階段：基礎盤點與曝光版位地圖（第 1-2 週）
            </p>
          </div>

          {/* Step list */}
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {steps.map((step, idx) => (
              <div
                key={step.id}
                className="card"
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: "1rem",
                  opacity: step.status === "done" ? 0.75 : 1,
                  borderColor:
                    step.status === "action_required"
                      ? "var(--warning)"
                      : step.status === "done"
                        ? "var(--border)"
                        : "var(--border)",
                }}
              >
                <StepIcon status={step.status} />
                <div style={{ flex: 1 }}>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "0.5rem",
                      marginBottom: "0.2rem",
                    }}
                  >
                    <span
                      style={{
                        fontSize: "0.75rem",
                        color: "var(--muted)",
                        width: 20,
                      }}
                    >
                      {idx + 1}
                    </span>
                    <span
                      style={{
                        fontWeight: 600,
                        textDecoration: step.status === "done" ? "line-through" : undefined,
                        color: step.status === "done" ? "var(--muted)" : undefined,
                      }}
                    >
                      {step.label}
                    </span>
                    {step.status === "action_required" && (
                      <span
                        style={{
                          fontSize: "0.72rem",
                          background: "var(--warning-soft)",
                          color: "var(--warning)",
                          padding: "0.1rem 0.4rem",
                          borderRadius: 999,
                        }}
                      >
                        需要操作
                      </span>
                    )}
                    {step.status === "pending" && (
                      <span
                        style={{
                          fontSize: "0.72rem",
                          background: "var(--surface-2)",
                          color: "var(--muted)",
                          padding: "0.1rem 0.4rem",
                          borderRadius: 999,
                        }}
                      >
                        進行中
                      </span>
                    )}
                  </div>
                  <p
                    style={{
                      margin: 0,
                      fontSize: "0.85rem",
                      color: "var(--muted)",
                      paddingLeft: 28,
                    }}
                  >
                    {step.description}
                  </p>
                  {step.seoRef && (
                    <p
                      style={{
                        margin: "0.3rem 0 0",
                        fontSize: "0.72rem",
                        color: "var(--muted)",
                        paddingLeft: 28,
                        opacity: 0.7,
                      }}
                    >
                      📎 {step.seoRef}
                    </p>
                  )}
                </div>
                {step.action && step.href && step.status !== "done" && (
                  <button
                    type="button"
                    className="btn btn-primary"
                    style={{ flexShrink: 0, fontSize: "0.82rem", padding: "0.35rem 0.8rem" }}
                    onClick={() => router.push(step.href!)}
                  >
                    {step.action}
                  </button>
                )}
              </div>
            ))}
          </div>

          {/* Quick links */}
          {siteId && (
            <div style={{ marginTop: "2rem", display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
              <button
                type="button"
                className="btn btn-primary"
                disabled={!siteId}
                onClick={() =>
                  router.push(`/app/${params.workspaceId}/sites/${siteId}/dashboard`)
                }
              >
                進入曝光儀表板
              </button>
              <button
                type="button"
                className="btn"
                onClick={() => router.push(`/app/${params.workspaceId}/settings/integrations`)}
              >
                GSC 連線
              </button>
            </div>
          )}
        </>
      )}
    </>
  );
}
