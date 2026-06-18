/* eslint-disable @typescript-eslint/ban-ts-comment */
// @ts-nocheck
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { PageHeader } from "@/components/PageHeader";
import { useSiteContext } from "@/lib/hooks";

type TodayItem = {
  id: string;
  type: "review" | "gap" | "job" | "approval" | "sync" | "completed";
  label: string;
  detail: string;
  href: string;
  meta?: string;
};

export default function TodayPage() {
  const { workspaceId, siteId, client } = useSiteContext();
  const [items, setItems] = useState<{ urgent: TodayItem[]; inProgress: TodayItem[]; done: TodayItem[] }>({ urgent: [], inProgress: [], done: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const urgent: TodayItem[] = [];
        const inProgress: TodayItem[] = [];
        const done: TodayItem[] = [];

        // Technical issues (indexability, crawl, etc.)
        try {
          const issues = await client.listTechnicalIssues(siteId);
          for (const issue of (issues as Array<{ id: string; issue_type: string; severity: string; description: string; recommended_action?: string }>).slice(0, 10)) {
            const isCritical = issue.severity === "critical" || issue.severity === "high";
            urgent.push({
              id: issue.id,
              type: "sync",
              label: `技術問題：${issue.issue_type}`,
              detail: issue.recommended_action || issue.description,
              href: `/app/${workspaceId}/sites/${siteId}/technical-issues`,
              meta: isCritical ? "🔴 技術" : "🟠 技術",
            });
          }
        } catch {}

        // Pending action candidates
        try {
          const candidates = await client.listCandidates(siteId, "pending");
          for (const c of (candidates as Array<{ id: string; action_type: string; risk_level: string }>).slice(0, 5)) {
            urgent.push({
              id: c.id,
              type: "approval",
              label: `待決策：${c.action_type}`,
              detail: "機會佇列待核准",
              href: `/app/${workspaceId}/sites/${siteId}/opportunities`,
              meta: c.risk_level === "high" ? "🔴 決策" : "🟠 決策",
            });
          }
        } catch {}

        // Content review - pending reviews
        try {
          const runs = await client.listGenerationRuns(siteId);
          const pending = (runs as Array<{ id: string; status: string; generation_mode: string; updated_at: string }>).filter(r => r.status === "needs_review" || r.status === "needs_changes");
          for (const r of pending) {
            urgent.push({ id: r.id, type: "review", label: r.status === "needs_review" ? "待審核內容" : "需修改內容", detail: `${r.generation_mode} · ${new Date(r.updated_at).toLocaleDateString("zh-TW")}`, href: `/app/${workspaceId}/sites/${siteId}/content-review`, meta: r.status === "needs_review" ? "🔴 待審核" : "🟠 需修改" });
          }
        } catch {}

        // Topic nodes with gaps
        try {
          const nodes = await client.listTopicNodes(siteId);
          const gaps = (nodes as Array<{ id: string; keyword: string; status: string }>).filter(n => n.status === "gap");
          for (const g of gaps.slice(0, 5)) {
            urgent.push({ id: g.id, type: "gap", label: `補缺口：${g.keyword}`, detail: "Topic Cluster 覆蓋缺口", href: `/app/${workspaceId}/sites/${siteId}/exposure-map`, meta: "🔴 Gap" });
          }
        } catch {}

        // Pending approvals (keyword pyramid)
        try {
          const pyramid = await client.listKeywordPyramid(siteId);
          const pendingApproval = (pyramid as Array<{ id: string; keyword: string; business_fit_status?: string; approved_at?: string | null }>).filter(n => n.business_fit_status === "in_scope" && !n.approved_at);
          for (const p of pendingApproval.slice(0, 5)) {
            urgent.push({ id: p.id, type: "approval", label: `待核准關鍵字：${p.keyword}`, detail: "關鍵字金字塔待按核准", href: `/app/${workspaceId}/sites/${siteId}/keyword-pyramid`, meta: "🟠 待核准" });
          }
        } catch {}

        // Opportunities
        try {
          const opps = await client.listOpportunities(siteId);
          const openOpps = (opps as Array<{ id: string; action_type: string; keyword?: string; status?: string }>).filter(o => !o.status || o.status === "open");
          for (const o of openOpps.slice(0, 5)) {
            inProgress.push({ id: o.id, type: "job", label: o.keyword ? `${o.action_type}：${o.keyword}` : o.action_type, detail: "開放機會", href: `/app/${workspaceId}/sites/${siteId}/opportunities`, meta: "🟡 進行中" });
          }
        } catch {}

        // Roadmap items in progress
        try {
          const roadmaps = await client.listRoadmaps(siteId);
          const active = (roadmaps as Array<{ id: string; action_type: string; keyword?: string; status: string }>).filter(r => r.status === "in_progress" || r.status === "active");
          for (const r of active.slice(0, 5)) {
            inProgress.push({ id: r.id, type: "job", label: r.keyword ? `${r.action_type}：${r.keyword}` : r.action_type, detail: "執行路線圖進行中", href: `/app/${workspaceId}/sites/${siteId}/roadmap`, meta: "🟡 進行中" });
          }
        } catch {}

        // Recently completed (outcomes)
        try {
          const outcomes = await client.listActionOutcomes(siteId);
          const recent = (outcomes as Array<{ id: string; decision_id: string; action_type: string; keyword?: string; created_at?: string }>).slice(0, 5);
          for (const o of recent) {
            done.push({ id: o.id ?? o.decision_id, type: "completed", label: o.keyword ? `${o.action_type}：${o.keyword}` : o.action_type, detail: "近期完成行動", href: `/app/${workspaceId}/sites/${siteId}/outcomes`, meta: "🟢 已完成" });
          }
        } catch {}

        // Approved content
        try {
          const runs = await client.listGenerationRuns(siteId);
          const approved = (runs as Array<{ id: string; status: string; generation_mode: string; updated_at: string }>).filter(r => r.status === "approved" || r.status === "published");
          for (const r of approved.slice(0, 3)) {
            done.push({ id: r.id, type: "completed", label: r.status === "published" ? "已發布內容" : "已核准內容", detail: `${r.generation_mode} · ${new Date(r.updated_at).toLocaleDateString("zh-TW")}`, href: `/app/${workspaceId}/sites/${siteId}/content-review`, meta: "🟢 已完成" });
          }
        } catch {}

        setItems({ urgent, inProgress, done });
      } catch (err) {
        setError(err instanceof Error ? err.message : "載入失敗");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [client, siteId, workspaceId]);

  if (loading) return <p style={{ color: "var(--muted)" }}>載入今日工作摘要…</p>;

  return (
    <>
      <PageHeader title="今日工作" subtitle="本站上今日待辦；跨站點彙總請至顧問工作台" />
      <p style={{ marginBottom: "1rem", fontSize: "0.9rem" }}>
        <Link href={`/app/${workspaceId}/consultant-inbox`} style={{ color: "var(--accent)" }}>
          → 查看工作區顧問工作台（跨站點待辦彙總）
        </Link>
      </p>
      {error ? <p style={{ color: "var(--danger)", marginBottom: "1rem" }}>{error}</p> : null}

      {/* Urgent */}
      <div className="today-section">
        <h2>🔴 待處理 <span style={{ fontSize: "0.82rem", color: "var(--muted)", fontWeight: 400 }}>（{items.urgent.length} 項）</span></h2>
        <div className="card">
          {items.urgent.length === 0 ? (
            <div className="empty-state">
              <p>🎉 沒有待處理項目！</p>
            </div>
          ) : (
            items.urgent.map(item => (
              <div key={item.id} className="today-item">
                <span className="today-dot urgent" />
                <span style={{ flex: 1 }}>
                  <Link href={item.href} className="today-link">{item.label}</Link>
                  <div style={{ fontSize: "0.78rem", color: "var(--muted)" }}>{item.detail}</div>
                </span>
                <span className="today-meta">{item.meta}</span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* In Progress */}
      <div className="today-section">
        <h2>🟡 進行中 <span style={{ fontSize: "0.82rem", color: "var(--muted)", fontWeight: 400 }}>（{items.inProgress.length} 項）</span></h2>
        <div className="card">
          {items.inProgress.length === 0 ? (
            <div className="empty-state">
              <p>尚無進行中項目</p>
              <div className="empty-cta">
                <Link href={`/app/${workspaceId}/sites/${siteId}/opportunities`} className="btn btn-primary">查看機會佇列</Link>
              </div>
            </div>
          ) : (
            items.inProgress.map(item => (
              <div key={item.id} className="today-item">
                <span className="today-dot in-progress" />
                <span style={{ flex: 1 }}>
                  <Link href={item.href} className="today-link">{item.label}</Link>
                  <div style={{ fontSize: "0.78rem", color: "var(--muted)" }}>{item.detail}</div>
                </span>
                <span className="today-meta">{item.meta}</span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Done */}
      <div className="today-section">
        <h2>🟢 最近完成 <span style={{ fontSize: "0.82rem", color: "var(--muted)", fontWeight: 400 }}>（{items.done.length} 項）</span></h2>
        <div className="card">
          {items.done.length === 0 ? (
            <div className="empty-state">
              <p>尚無近期完成項目，開始執行機會吧！</p>
              <div className="empty-cta">
                <Link href={`/app/${workspaceId}/sites/${siteId}/opportunities`} className="btn btn-primary">查看機會佇列</Link>
                <Link href={`/app/${workspaceId}/sites/${siteId}/roadmap`} className="btn">執行路線圖</Link>
              </div>
            </div>
          ) : (
            items.done.map(item => (
              <div key={item.id} className="today-item">
                <span className="today-dot done" />
                <span style={{ flex: 1 }}>
                  <Link href={item.href} className="today-link">{item.label}</Link>
                  <div style={{ fontSize: "0.78rem", color: "var(--muted)" }}>{item.detail}</div>
                </span>
                <span className="today-meta">{item.meta}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </>
  );
}
