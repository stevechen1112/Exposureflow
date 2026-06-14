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
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [storedSiteId, setStoredSiteId] = useState<string | null>(null);

  useEffect(() => {
    const sid = localStorage.getItem(storageKey("siteId"));
    setStoredSiteId(sid);
    Promise.all([
      client.listSites(),
      client.listStrategyIntakes(),
      client.listSyncStates(),
      client.listKnowledgeSources(sid ?? "").catch(() => [] as Array<Record<string, unknown>>),
    ])
      .then(([s, i, sync, ks]) => {
        setSites(s);
        setIntakes(i);
        setSyncStates(sync);
        setKnowledgeSources(ks);
        if (s[0]) localStorage.setItem(storageKey("siteId"), s[0].id);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [client]);

  const siteId = sites[0]?.id ?? storedSiteId;
  const hasGscSync = syncStates.some((s) => String(s.provider) === "gsc" && s.last_success_at);
  const hasApprovedIntake = intakes.some(
    (i) => String(i.status) === "approved" || String(i.status) === "active",
  );
  const hasKeywordPyramid = intakes.some((i) => i.keyword_count && Number(i.keyword_count) > 0);
  const hasApprovedKnowledge = knowledgeSources.some(
    (ks) => String(ks.approval_status) === "approved",
  );

  function buildSteps(): CheckStep[] {
    return [
      {
        id: "site",
        label: "建立站點",
        description: "設定您要分析的網站 domain 與基本資訊",
        status: sites.length > 0 ? "done" : "action_required",
        action: sites.length === 0 ? "前往設定" : undefined,
        href: sites.length === 0 ? `/app/${params.workspaceId}/settings` : undefined,
      },
      {
        id: "gsc",
        label: "連接 Google Search Console",
        description: "取得自然搜尋曝光資料是一切分析的基礎",
        status: hasGscSync
          ? "done"
          : syncStates.some((s) => String(s.provider) === "gsc")
            ? "pending"
            : "action_required",
        action: !hasGscSync ? "前往整合設定" : undefined,
        href: !hasGscSync ? `/app/${params.workspaceId}/settings/integrations` : undefined,
      },
      {
        id: "intake",
        label: "完成策略 Intake",
        description: "填寫業務目標、競爭對手與市場設定",
        status: hasApprovedIntake ? "done" : intakes.length > 0 ? "pending" : "action_required",
        action: !hasApprovedIntake ? "前往策略設定" : undefined,
        href: !hasApprovedIntake ? `/app/${params.workspaceId}/sites/${siteId}/strategy` : undefined,
      },
      {
        id: "keywords",
        label: "建立 Keyword Pyramid",
        description: "定義核心關鍵字、長尾關鍵字與優先級",
        status: hasKeywordPyramid ? "done" : "pending",
      },
      {
        id: "knowledge",
        label: "匯入並核准知識來源",
        description: "品牌聲音、產品資訊與合規政策文件",
        status: hasApprovedKnowledge
          ? "done"
          : knowledgeSources.length > 0
            ? "pending"
            : "action_required",
        action: "前往知識庫",
        href: siteId
          ? `/app/${params.workspaceId}/sites/${siteId}/knowledge`
          : undefined,
      },
      {
        id: "dashboard",
        label: "查看曝光儀表板",
        description: "確認 baseline 資料已匯入，開始追蹤曝光版圖",
        status:
          hasGscSync && sites.length > 0 && hasApprovedIntake ? "done" : "pending",
        action: siteId ? "進入儀表板" : undefined,
        href: siteId
          ? `/app/${params.workspaceId}/sites/${siteId}/dashboard`
          : undefined,
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
                整合設定
              </button>
            </div>
          )}
        </>
      )}
    </>
  );
}
