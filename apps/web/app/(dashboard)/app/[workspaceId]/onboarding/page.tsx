"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import type { Site } from "@exposureflow/shared-types";
import { PageHeader } from "@/components/PageHeader";
import { getApiClient } from "@/lib/api-client";
import { storageKey } from "@/lib/config";

export default function OnboardingPage() {
  const params = useParams<{ workspaceId: string }>();
  const router = useRouter();
  const [sites, setSites] = useState<Site[]>([]);
  const [intakes, setIntakes] = useState<Array<Record<string, unknown>>>([]);
  const [syncStates, setSyncStates] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState<string | null>(null);
  const [storedSiteId, setStoredSiteId] = useState<string | null>(null);

  const client = getApiClient(params.workspaceId);

  useEffect(() => {
    setStoredSiteId(localStorage.getItem(storageKey("siteId")));
    Promise.all([client.listSites(), client.listStrategyIntakes(), client.listSyncStates()])
      .then(([s, i, sync]) => {
        setSites(s);
        setIntakes(i);
        setSyncStates(sync);
        if (s[0]) localStorage.setItem(storageKey("siteId"), s[0].id);
      })
      .catch((err: Error) => setError(err.message));
  }, [client]);

  const siteId = sites[0]?.id ?? storedSiteId;

  function goDashboard() {
    if (siteId) router.push(`/app/${params.workspaceId}/sites/${siteId}/dashboard`);
  }

  return (
    <>
      <PageHeader
        title="Onboarding"
        subtitle="完成策略 intake、資料接入與首站設定"
      />
      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}
      <div className="kpi-grid">
        <div className="card">
          <div className="kpi-label">站點</div>
          <div className="kpi-value">{sites.length}</div>
          {sites[0] ? (
            <p style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
              {sites[0].domain ?? sites[0].site_name}
            </p>
          ) : null}
        </div>
        <div className="card">
          <div className="kpi-label">Strategy Intake</div>
          <div className="kpi-value">{intakes.length}</div>
          <p style={{ color: "var(--muted)", fontSize: "0.85rem" }}>待審批 intake 請至策略頁</p>
        </div>
        <div className="card">
          <div className="kpi-label">整合同步狀態</div>
          <div className="kpi-value">{syncStates.length}</div>
        </div>
      </div>
      <ol style={{ lineHeight: 1.8, color: "var(--muted)", maxWidth: 560 }}>
        <li>連接 GSC / GA4（設定 → 整合）</li>
        <li>完成 Business Intake 與 Keyword Pyramid</li>
        <li>建立 Delivery Commitment 產能邊界</li>
        <li>匯入 Knowledge Sources 並核准</li>
        <li>進入曝光儀表板檢視 baseline</li>
      </ol>
      <button type="button" className="btn btn-primary" disabled={!siteId} onClick={goDashboard}>
        進入曝光儀表板
      </button>
    </>
  );
}
