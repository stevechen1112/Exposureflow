"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { BusinessConstraintRule, KeywordPyramidNode } from "@exposureflow/shared-types";
import { PageHeader } from "@/components/PageHeader";
import { parseApiError } from "@/components/ForbiddenState";
import { RequirePermission } from "@/components/WorkspaceGuard";
import { useSiteContext } from "@/lib/hooks";
import { useWorkspaceAuth } from "@/lib/auth-context";
import {
  BUSINESS_FIT_OPTIONS,
  EMPTY_KEYWORD_PYRAMID_FORM,
  FUNNEL_OPTIONS,
  INTENT_OPTIONS,
  KEYWORD_LEVEL_OPTIONS,
  NODE_TYPE_OPTIONS,
  buildPyramidTree,
  createdByLabel,
  enrichmentSummary,
  formValuesToPayload,
  inclusionStatus,
  inclusionStatusHint,
  inclusionStatusLabel,
  isActiveNode,
  isApprovedOfficialNode,
  isCandidateNode,
  isExcludedNode,
  isPendingApprovalNode,
  nodeToFormValues,
  nodeTypeLabel,
  parentLabel,
  parseBatchKeywords,
  type BusinessFitStatus,
  type KeywordPyramidFormValues,
  type PyramidTreeNode,
} from "@/lib/keyword-pyramid-form";

type EditorMode = "create" | "edit";
type DefaultStatus = BusinessFitStatus;

function fmtTime(iso?: string | null) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("zh-TW", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function InclusionBadge({ node }: { node: KeywordPyramidNode }) {
  const status = inclusionStatus(node);
  const styles: Record<string, { bg: string; color: string }> = {
    approved: { bg: "rgba(22, 163, 74, 0.12)", color: "#15803d" },
    pending_approval: { bg: "rgba(234, 88, 12, 0.12)", color: "#c2410c" },
    candidate: { bg: "rgba(100, 116, 139, 0.12)", color: "#475569" },
    excluded: { bg: "rgba(148, 163, 184, 0.15)", color: "#64748b" },
    blocked: { bg: "rgba(220, 38, 38, 0.1)", color: "#b91c1c" },
  };
  const palette = styles[status] ?? styles.candidate;
  return (
    <span
      title={inclusionStatusHint(node)}
      style={{
        display: "inline-block",
        padding: "0.15rem 0.45rem",
        borderRadius: "999px",
        fontSize: "0.78rem",
        fontWeight: 600,
        background: palette.bg,
        color: palette.color,
        whiteSpace: "nowrap",
      }}
    >
      {inclusionStatusLabel(node)}
    </span>
  );
}

function ScopeSummary({
  approvedCount,
  pendingApprovalCount,
  candidateCount,
  excludedCount,
}: {
  approvedCount: number;
  pendingApprovalCount: number;
  candidateCount: number;
  excludedCount: number;
}) {
  const items = [
    { label: "已正式納入", value: approvedCount, hint: "顧問已核准，連結曝光地圖", accent: "#15803d" },
    { label: "待按核准", value: pendingApprovalCount, hint: "已在 scope 但尚未核准", accent: "#c2410c" },
    { label: "待審候選", value: candidateCount, hint: "Intake / 研究草稿", accent: "#475569" },
    { label: "已排除", value: excludedCount, hint: "不納入專案", accent: "#64748b" },
  ];
  return (
    <div
      className="card"
      style={{
        marginBottom: "1.5rem",
        background: "var(--surface-2)",
        border: "1px solid var(--border)",
      }}
    >
      <h2 style={{ fontSize: "1rem", margin: "0 0 0.35rem" }}>本專案關鍵字一覽</h2>
      <p style={{ margin: "0 0 1rem", color: "var(--muted)", fontSize: "0.88rem" }}>
        <strong>正式納入</strong> = 顧問已按「核准」、有核准時間，且為 pillar / cluster / long-tail。
        其餘為草稿或排除，不會當成專案正式關鍵字組。
      </p>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
          gap: "0.75rem",
        }}
      >
        {items.map((item) => (
          <div
            key={item.label}
            style={{
              padding: "0.75rem",
              borderRadius: "8px",
              background: "var(--surface-1, #fff)",
              border: "1px solid var(--border)",
            }}
          >
            <div style={{ fontSize: "1.5rem", fontWeight: 700, color: item.accent }}>{item.value}</div>
            <div style={{ fontSize: "0.9rem", fontWeight: 600 }}>{item.label}</div>
            <div style={{ fontSize: "0.78rem", color: "var(--muted)", marginTop: "0.2rem" }}>{item.hint}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label style={{ display: "grid", gap: "0.35rem", fontSize: "0.9rem" }}>
      <span style={{ color: "var(--muted)" }}>{label}</span>
      {children}
    </label>
  );
}

function NodeTable({
  rows,
  nodesById,
  emptyText,
  canWrite,
  busyId,
  actionMode,
  onEdit,
  onApprove,
  onReject,
  onRestore,
  onDelete,
}: {
  rows: KeywordPyramidNode[];
  nodesById: Map<string, KeywordPyramidNode>;
  emptyText: string;
  canWrite: boolean;
  busyId: string | null;
  actionMode: "active" | "candidate" | "excluded";
  onEdit: (node: KeywordPyramidNode) => void;
  onApprove: (nodeId: string, keyword: string) => void;
  onReject: (nodeId: string, keyword: string) => void;
  onRestore: (nodeId: string, keyword: string) => void;
  onDelete: (nodeId: string) => void;
}) {
  if (rows.length === 0) {
    return <p style={{ margin: 0, color: "var(--muted)", fontSize: "0.9rem" }}>{emptyText}</p>;
  }

  return (
    <div className="table-wrap card" style={{ padding: 0 }}>
      <table>
        <thead>
          <tr>
            <th>層級</th>
            <th>關鍵字</th>
            <th>納入狀態</th>
            <th>上層</th>
            <th>意圖</th>
            <th>SERP</th>
            <th>來源</th>
            <th>核准時間</th>
            {canWrite ? <th>操作</th> : null}
          </tr>
        </thead>
        <tbody>
          {rows.map((node) => (
            <tr key={node.id}>
              <td>{nodeTypeLabel(node.node_type)}</td>
              <td>
                <strong>{node.keyword}</strong>
                {node.is_target ? " ★" : null}
              </td>
              <td>
                <InclusionBadge node={node} />
              </td>
              <td>{parentLabel(node, nodesById)}</td>
              <td>{node.intent ?? "—"}</td>
              <td>{enrichmentSummary(node)}</td>
              <td>{createdByLabel(node.created_by)}</td>
              <td>{node.approved_at ? fmtTime(node.approved_at) : "—"}</td>
              {canWrite ? (
                <td style={{ whiteSpace: "nowrap" }}>
                  <button
                    type="button"
                    className="btn btn-ghost"
                    disabled={busyId === node.id}
                    onClick={() => onEdit(node)}
                  >
                    編輯
                  </button>
                  {(actionMode === "candidate" ||
                    (actionMode === "active" && isActiveNode(node) && !node.approved_at)) && (
                    <button
                      type="button"
                      className="btn btn-primary"
                      style={{ marginLeft: "0.35rem" }}
                      disabled={busyId === node.id}
                      onClick={() => onApprove(node.id, node.keyword)}
                    >
                      核准
                    </button>
                  )}
                  {actionMode === "candidate" ? (
                    <button
                      type="button"
                      className="btn btn-ghost"
                      style={{ marginLeft: "0.35rem" }}
                      disabled={busyId === node.id}
                      onClick={() => onReject(node.id, node.keyword)}
                    >
                      排除
                    </button>
                  ) : null}
                  {actionMode === "excluded" && node.business_fit_status === "out_of_scope" ? (
                    <>
                      <button
                        type="button"
                        className="btn btn-ghost"
                        style={{ marginLeft: "0.35rem" }}
                        disabled={busyId === node.id}
                        onClick={() => onRestore(node.id, node.keyword)}
                      >
                        恢復待審
                      </button>
                      <button
                        type="button"
                        className="btn btn-primary"
                        style={{ marginLeft: "0.35rem" }}
                        disabled={busyId === node.id}
                        onClick={() => onApprove(node.id, node.keyword)}
                      >
                        核准納入
                      </button>
                    </>
                  ) : null}
                  <button
                    type="button"
                    className="btn btn-ghost"
                    style={{ marginLeft: "0.35rem", color: "var(--danger)" }}
                    disabled={busyId === node.id}
                    onClick={() => onDelete(node.id)}
                  >
                    刪除
                  </button>
                </td>
              ) : null}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function PyramidTree({
  tree,
  depth = 0,
  onEdit,
  officialOnly = false,
}: {
  tree: PyramidTreeNode[];
  depth?: number;
  onEdit: (node: KeywordPyramidNode) => void;
  officialOnly?: boolean;
}) {
  if (tree.length === 0) return null;
  return (
    <ul style={{ listStyle: "none", margin: 0, paddingLeft: depth ? "1rem" : 0 }}>
      {tree.map(({ node, children }) => {
        const typed = node as KeywordPyramidNode;
        const approved = isApprovedOfficialNode(typed);
        return (
          <li key={String(node.id)} style={{ marginBottom: "0.35rem" }}>
            <button
              type="button"
              className="btn btn-ghost"
              style={{
                padding: "0.15rem 0.35rem",
                fontSize: "0.88rem",
                opacity: officialOnly || approved ? 1 : 0.72,
              }}
              onClick={() => onEdit(typed)}
            >
              {!officialOnly ? <InclusionBadge node={typed} /> : null}
              <span style={{ color: "var(--muted)", marginRight: "0.35rem", marginLeft: officialOnly ? 0 : "0.35rem" }}>
                {nodeTypeLabel(String(node.node_type))}
              </span>
              {String(node.keyword)}
              {node.is_target ? " ★" : null}
            </button>
            <PyramidTree tree={children} depth={depth + 1} onEdit={onEdit} officialOnly={officialOnly} />
          </li>
        );
      })}
    </ul>
  );
}

export default function KeywordPyramidPage() {
  const { workspaceId, siteId, client } = useSiteContext();
  const { can } = useWorkspaceAuth();
  const canWrite = can("site:write");

  const [nodes, setNodes] = useState<KeywordPyramidNode[]>([]);
  const [rules, setRules] = useState<BusinessConstraintRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [editorMode, setEditorMode] = useState<EditorMode | null>(null);
  const [editId, setEditId] = useState<string | null>(null);
  const [form, setForm] = useState<KeywordPyramidFormValues>(EMPTY_KEYWORD_PYRAMID_FORM);
  const [batchText, setBatchText] = useState("");
  const [batchStatus, setBatchStatus] = useState<DefaultStatus>("needs_review");
  const [scopes, setScopes] = useState<Array<{ id: string; name: string }>>([]);
  const [coldStartSeeds, setColdStartSeeds] = useState("");
  const [coldStartBusy, setColdStartBusy] = useState(false);
  const editorRef = useRef<HTMLDivElement | null>(null);

  const load = useCallback(async () => {
    if (!siteId) return;
    setLoading(true);
    try {
      const [nodeRows, ruleRows, scopeRows] = await Promise.all([
        client.listKeywordPyramid(siteId),
        client.listConstraintRules(siteId),
        client.listProductScopes(siteId, "active"),
      ]);
      setNodes(nodeRows as KeywordPyramidNode[]);
      setRules(ruleRows as BusinessConstraintRule[]);
      setScopes(
        (scopeRows as Array<{ id: string; name: string }>).map((row) => ({
          id: row.id,
          name: row.name,
        })),
      );
      setError(null);
    } catch (err) {
      setError(parseApiError(err instanceof Error ? err.message : "載入失敗").friendly);
    } finally {
      setLoading(false);
    }
  }, [client, siteId]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (!editorMode) return;
    editorRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [editorMode, editId]);

  const nodesById = useMemo(() => new Map(nodes.map((node) => [node.id, node])), [nodes]);
  const pillarOptions = useMemo(
    () => nodes.filter((node) => node.node_type === "pillar" && node.id !== editId),
    [nodes, editId],
  );

  const officialNodes = useMemo(
    () => nodes.filter((node) => isActiveNode(node) && Boolean(node.approved_at)),
    [nodes],
  );
  const pendingApprovalNodes = useMemo(
    () => nodes.filter((node) => isPendingApprovalNode(node)),
    [nodes],
  );
  const candidateNodes = useMemo(() => nodes.filter((node) => isCandidateNode(node)), [nodes]);
  const excludedNodes = useMemo(() => nodes.filter((node) => isExcludedNode(node)), [nodes]);
  const officialPyramidTree = useMemo(() => buildPyramidTree(officialNodes), [officialNodes]);

  const editingNode = useMemo(
    () => (editId ? nodesById.get(editId) : undefined),
    [editId, nodesById],
  );

  function businessFitOptionsForEditor(): typeof BUSINESS_FIT_OPTIONS {
    if (editorMode !== "edit" || !editingNode) return BUSINESS_FIT_OPTIONS;
    if (isCandidateNode(editingNode)) {
      return BUSINESS_FIT_OPTIONS.filter((option) => option.value !== "in_scope");
    }
    if (isActiveNode(editingNode) && editingNode.approved_at) {
      return BUSINESS_FIT_OPTIONS.filter((option) => option.value !== "needs_review");
    }
    return BUSINESS_FIT_OPTIONS;
  }

  function openCreate(defaultStatus: DefaultStatus) {
    setEditorMode("create");
    setEditId(null);
    setForm({ ...EMPTY_KEYWORD_PYRAMID_FORM, business_fit_status: defaultStatus });
    setError(null);
    setMessage(null);
  }

  function startEdit(node: KeywordPyramidNode) {
    setEditorMode("edit");
    setEditId(node.id);
    setForm(nodeToFormValues(node));
    setError(null);
    setMessage(`正在編輯「${node.keyword}」，請在上方表單修改後按儲存`);
  }

  function closeEditor() {
    setEditorMode(null);
    setEditId(null);
    setForm(EMPTY_KEYWORD_PYRAMID_FORM);
    setMessage(null);
  }

  async function handleSave() {
    if (!siteId || !form.keyword.trim()) {
      setError("請填寫關鍵字");
      return;
    }
    if (
      editorMode === "edit" &&
      editingNode &&
      isCandidateNode(editingNode) &&
      form.business_fit_status === "in_scope"
    ) {
      setError("待審候選請使用列上的「核准」按鈕納入正式關鍵字組");
      return;
    }
    const busyKey = editId ?? "create";
    setBusyId(busyKey);
    setMessage(null);
    try {
      const payload = formValuesToPayload(siteId, form);
      if (editorMode === "edit" && editId) {
        await client.updateKeywordPyramidNode(editId, {
          keyword: payload.keyword,
          node_type: payload.node_type,
          parent_id: payload.parent_id,
          product_service_scope_id: payload.product_service_scope_id,
          intent: payload.intent,
          target_market: payload.target_market,
          language: payload.language,
          keyword_level: payload.keyword_level,
          funnel_stage: payload.funnel_stage,
          is_target: payload.is_target,
          priority: payload.priority,
          business_fit_status: payload.business_fit_status,
        });
        setMessage("已更新關鍵字節點");
      } else {
        const created = (await client.createKeywordPyramidNode(payload)) as KeywordPyramidNode;
        if (form.business_fit_status === "in_scope") {
          await client.approveKeywordPyramidNode(created.id);
          setMessage("已新增並核准為正式關鍵字");
        } else {
          setMessage("已新增關鍵字節點");
        }
      }
      closeEditor();
      await load();
    } catch (err) {
      setError(parseApiError(err instanceof Error ? err.message : "儲存失敗").friendly);
    } finally {
      setBusyId(null);
    }
  }

  async function handleColdStart() {
    if (!siteId) return;
    const seeds = coldStartSeeds
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);
    if (seeds.length === 0) {
      setError("請輸入至少一個 seed 關鍵字");
      return;
    }
    setColdStartBusy(true);
    setMessage(null);
    try {
      const result = await client.coldStartResearch({
        site_id: siteId,
        seed_keywords: seeds,
        market: "TW",
        language: "zh-TW",
      });
      setMessage(`Cold-start 已排程（job ${result.job_id}），完成後請重新整理`);
      setColdStartSeeds("");
    } catch (err) {
      setError(parseApiError(err instanceof Error ? err.message : "Cold-start 失敗").friendly);
    } finally {
      setColdStartBusy(false);
    }
  }

  async function handleSyncBridge() {
    if (!siteId) return;
    setBusyId("bridge");
    try {
      const result = await client.syncPyramidTopicBridge(siteId);
      setMessage(`已同步 Topic Graph：${result.linked} 連結、${result.skipped} 略過`);
      await load();
    } catch (err) {
      setError(parseApiError(err instanceof Error ? err.message : "同步失敗").friendly);
    } finally {
      setBusyId(null);
    }
  }

  async function handleBatchImport() {
    if (!siteId) return;
    const parsed = parseBatchKeywords(batchText);
    if (parsed.length === 0) {
      setError("批次內容沒有可匯入的關鍵字");
      return;
    }
    setBusyId("batch");
    setMessage(null);
    try {
      const parsed = parseBatchKeywords(batchText);
      const result = await client.bulkImportKeywordPyramid({
        site_id: siteId,
        created_by: "consultant",
        rows: parsed.map((row) => ({
          keyword: row.keyword,
          node_type: row.node_type,
          business_fit_status: batchStatus,
          language: "zh-TW",
          priority: 3,
        })),
      });
      setBatchText("");
      setMessage(`已匯入 ${result.created} 個關鍵字（略過 ${result.skipped}）`);
      await load();
    } catch (err) {
      setError(parseApiError(err instanceof Error ? err.message : "批次匯入失敗").friendly);
    } finally {
      setBusyId(null);
    }
  }

  async function handleApprove(nodeId: string, keyword: string) {
    if (!window.confirm(`確定核准「${keyword}」並納入正式關鍵字組？`)) return;
    setBusyId(nodeId);
    setMessage(null);
    setError(null);
    try {
      await client.approveKeywordPyramidNode(nodeId);
      if (editId === nodeId) closeEditor();
      setMessage(`已核准「${keyword}」並納入正式關鍵字組`);
      await load();
    } catch (err) {
      setError(parseApiError(err instanceof Error ? err.message : "核准失敗").friendly);
    } finally {
      setBusyId(null);
    }
  }

  async function handleReject(nodeId: string, keyword: string) {
    if (!window.confirm(`確定排除「${keyword}」？排除後可在下方區塊恢復或刪除。`)) return;
    setBusyId(nodeId);
    setMessage(null);
    setError(null);
    try {
      await client.updateKeywordPyramidNode(nodeId, { business_fit_status: "out_of_scope" });
      if (editId === nodeId) closeEditor();
      setMessage(`已排除「${keyword}」`);
      await load();
    } catch (err) {
      setError(parseApiError(err instanceof Error ? err.message : "排除失敗").friendly);
    } finally {
      setBusyId(null);
    }
  }

  async function handleRestore(nodeId: string, keyword: string) {
    setBusyId(nodeId);
    setMessage(null);
    setError(null);
    try {
      await client.updateKeywordPyramidNode(nodeId, { business_fit_status: "needs_review" });
      if (editId === nodeId) closeEditor();
      setMessage(`已將「${keyword}」恢復為待審候選`);
      await load();
    } catch (err) {
      setError(parseApiError(err instanceof Error ? err.message : "恢復失敗").friendly);
    } finally {
      setBusyId(null);
    }
  }

  async function handleDelete(nodeId: string) {
    const node = nodesById.get(nodeId);
    const label = node?.keyword ?? "此節點";
    if (!window.confirm(`確定刪除「${label}」？`)) return;
    setBusyId(nodeId);
    setMessage(null);
    try {
      await client.deleteKeywordPyramidNode(nodeId);
      if (editId === nodeId) closeEditor();
      setMessage("已刪除關鍵字節點");
      await load();
    } catch (err) {
      setError(parseApiError(err instanceof Error ? err.message : "刪除失敗").friendly);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <RequirePermission permission="site:read" workspaceId={workspaceId}>
      <PageHeader
        title="關鍵字金字塔"
        subtitle="下方綠色「已正式納入」才是本專案核准的關鍵字組；其餘為待審草稿或已排除"
      />

      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}
      {message ? <p style={{ color: "var(--success)" }}>{message}</p> : null}
      {loading ? <p style={{ color: "var(--muted)" }}>載入中…</p> : null}

      {canWrite && editorMode ? (
        <div
          ref={editorRef}
          className="card"
          style={{
            marginBottom: "1.5rem",
            scrollMarginTop: "1rem",
            border: "1px solid var(--accent, #2563eb)",
          }}
        >
          <h2 style={{ fontSize: "1rem", marginTop: 0 }}>
            {editorMode === "edit" ? "編輯關鍵字節點" : "新增關鍵字節點"}
          </h2>
          {editorMode === "edit" && editingNode && isCandidateNode(editingNode) ? (
            <p style={{ margin: "0 0 0.75rem", color: "var(--muted)", fontSize: "0.88rem" }}>
              待審候選請先修改內容，再按列上「核准」納入正式組；不可在此直接改為正式狀態。
            </p>
          ) : null}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
              gap: "0.75rem",
            }}
          >
            <Field label="關鍵字">
              <input
                className="input"
                value={form.keyword}
                onChange={(e) => setForm((prev) => ({ ...prev, keyword: e.target.value }))}
              />
            </Field>
            <Field label="層級">
              <select
                className="input"
                value={form.node_type}
                onChange={(e) =>
                  setForm((prev) => ({
                    ...prev,
                    node_type: e.target.value as KeywordPyramidFormValues["node_type"],
                  }))
                }
              >
                {NODE_TYPE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="上層 Pillar">
              <select
                className="input"
                value={form.parent_id}
                onChange={(e) => setForm((prev) => ({ ...prev, parent_id: e.target.value }))}
              >
                <option value="">無（頂層）</option>
                {pillarOptions.map((pillar) => (
                  <option key={pillar.id} value={pillar.id}>
                    {pillar.keyword}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Business Fit 狀態">
              <select
                className="input"
                value={form.business_fit_status}
                onChange={(e) =>
                  setForm((prev) => ({
                    ...prev,
                    business_fit_status: e.target.value as BusinessFitStatus,
                  }))
                }
              >
                {businessFitOptionsForEditor().map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="意圖">
              <select
                className="input"
                value={form.intent}
                onChange={(e) => setForm((prev) => ({ ...prev, intent: e.target.value }))}
              >
                {INTENT_OPTIONS.map((option) => (
                  <option key={option.value || "none"} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="市場">
              <input
                className="input"
                value={form.target_market}
                onChange={(e) => setForm((prev) => ({ ...prev, target_market: e.target.value }))}
              />
            </Field>
            <Field label="語系">
              <input
                className="input"
                value={form.language}
                onChange={(e) => setForm((prev) => ({ ...prev, language: e.target.value }))}
              />
            </Field>
            <Field label="優先級">
              <input
                className="input"
                type="number"
                min={1}
                max={5}
                value={form.priority}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, priority: Number(e.target.value) || 3 }))
                }
              />
            </Field>
            <Field label="Product Scope">
              <select
                className="input"
                value={form.product_service_scope_id}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, product_service_scope_id: e.target.value }))
                }
              >
                <option value="">未指定</option>
                {scopes.map((scope) => (
                  <option key={scope.id} value={scope.id}>
                    {scope.name}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Keyword Level">
              <select
                className="input"
                value={form.keyword_level}
                onChange={(e) => setForm((prev) => ({ ...prev, keyword_level: e.target.value }))}
              >
                {KEYWORD_LEVEL_OPTIONS.map((option) => (
                  <option key={option.value || "auto"} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="漏斗階段">
              <select
                className="input"
                value={form.funnel_stage}
                onChange={(e) => setForm((prev) => ({ ...prev, funnel_stage: e.target.value }))}
              >
                {FUNNEL_OPTIONS.map((option) => (
                  <option key={option.value || "none"} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="本季目標字">
              <label style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <input
                  type="checkbox"
                  checked={form.is_target}
                  onChange={(e) => setForm((prev) => ({ ...prev, is_target: e.target.checked }))}
                />
                標記為 watchlist
              </label>
            </Field>
          </div>
          <div style={{ marginTop: "0.75rem", display: "flex", gap: "0.5rem" }}>
            <button
              type="button"
              className="btn btn-primary"
              disabled={busyId !== null && busyId !== (editId ?? "create")}
              onClick={handleSave}
            >
              儲存
            </button>
            <button type="button" className="btn btn-ghost" onClick={closeEditor}>
              取消
            </button>
          </div>
        </div>
      ) : null}

      {!loading ? (
        <ScopeSummary
          approvedCount={officialNodes.length}
          pendingApprovalCount={pendingApprovalNodes.length}
          candidateCount={candidateNodes.length}
          excludedCount={excludedNodes.length}
        />
      ) : null}

      <section
        className="card"
        style={{
          marginBottom: "1.5rem",
          border: "1px solid rgba(22, 163, 74, 0.35)",
          background: "rgba(22, 163, 74, 0.04)",
        }}
      >
        <h2 style={{ fontSize: "1.05rem", margin: "0 0 0.35rem", color: "#15803d" }}>
          ✅ 已正式納入的關鍵字（{officialNodes.length}）
        </h2>
        <p style={{ color: "var(--muted)", fontSize: "0.88rem", marginTop: 0 }}>
          這就是本專案已核准的關鍵字組，會連結曝光地圖、Onboarding 與後續機會生成。只有按「核准」後才會出現在此。
        </p>
        {!loading && officialPyramidTree.length > 0 ? (
          <div style={{ margin: "1rem 0" }}>
            <h3 style={{ fontSize: "0.95rem", margin: "0 0 0.5rem" }}>金字塔結構（僅已核准）</h3>
            <PyramidTree tree={officialPyramidTree} onEdit={startEdit} officialOnly />
          </div>
        ) : null}
        <NodeTable
          rows={officialNodes}
          nodesById={nodesById}
          emptyText="尚無已核准的正式關鍵字。請從下方待審候選按「核准」，或使用「+ 新增正式關鍵字」。"
          canWrite={canWrite}
          busyId={busyId}
          actionMode="active"
          onEdit={startEdit}
          onApprove={handleApprove}
          onReject={handleReject}
          onRestore={handleRestore}
          onDelete={handleDelete}
        />
      </section>

      {pendingApprovalNodes.length > 0 ? (
        <section className="card" style={{ marginBottom: "1.5rem", border: "1px solid rgba(234, 88, 12, 0.35)" }}>
          <h2 style={{ fontSize: "1.05rem", margin: "0 0 0.35rem", color: "#c2410c" }}>
            ⚠ 待按核准（{pendingApprovalNodes.length}）
          </h2>
          <p style={{ color: "var(--muted)", fontSize: "0.88rem" }}>
            這些字已在 scope 內，但尚未按核准，不算正式納入。
          </p>
          <NodeTable
            rows={pendingApprovalNodes}
            nodesById={nodesById}
            emptyText=""
            canWrite={canWrite}
            busyId={busyId}
            actionMode="active"
            onEdit={startEdit}
            onApprove={handleApprove}
            onReject={handleReject}
            onRestore={handleRestore}
            onDelete={handleDelete}
          />
        </section>
      ) : null}

      {canWrite ? (
        <div
          className="card"
          style={{
            marginBottom: "1.5rem",
            background: "var(--surface-2)",
            display: "flex",
            flexWrap: "wrap",
            gap: "0.5rem",
            alignItems: "center",
          }}
        >
          <span style={{ fontSize: "0.9rem", color: "var(--muted)", marginRight: "0.5rem" }}>
            顧問操作：
          </span>
          <button type="button" className="btn btn-primary" onClick={() => openCreate("in_scope")}>
            + 新增正式關鍵字
          </button>
          <button type="button" className="btn btn-ghost" onClick={() => openCreate("needs_review")}>
            + 新增待審候選
          </button>
          <button
            type="button"
            className="btn btn-ghost"
            disabled={busyId !== null}
            onClick={handleSyncBridge}
          >
            同步 Topic Graph
          </button>
        </div>
      ) : null}

      {canWrite ? (
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <h2 style={{ fontSize: "1rem", marginTop: 0 }}>Cold-start 關鍵字研究</h2>
          <p style={{ margin: "0 0 0.75rem", color: "var(--muted)", fontSize: "0.88rem" }}>
            輸入 seed 關鍵字，系統會抓取 SERP、PAA 與相關搜尋，將候選字寫入「待審候選」（全部需顧問核准）。
          </p>
          <textarea
            className="input"
            rows={3}
            value={coldStartSeeds}
            onChange={(e) => setColdStartSeeds(e.target.value)}
            placeholder={"台中紗窗維修\n修理紗窗"}
          />
          <button
            type="button"
            className="btn btn-primary"
            style={{ marginTop: "0.75rem" }}
            disabled={coldStartBusy}
            onClick={handleColdStart}
          >
            {coldStartBusy ? "排程中…" : "執行 Cold-start 研究"}
          </button>
        </div>
      ) : null}

      <section style={{ marginBottom: "1.5rem" }}>
        <h2 style={{ fontSize: "1.05rem", margin: "0 0 0.35rem" }}>
          待審候選（{candidateNodes.length}）
        </h2>
        <p style={{ color: "var(--muted)", fontSize: "0.88rem" }}>
          Intake 自動抽取的 keyword 草稿。請依專案實際策略修改後再核准，不需要的可直接刪除。
        </p>
        <NodeTable
          rows={candidateNodes}
          nodesById={nodesById}
          emptyText="目前沒有待審候選。"
          canWrite={canWrite}
          busyId={busyId}
          actionMode="candidate"
          onEdit={startEdit}
          onApprove={handleApprove}
          onReject={handleReject}
          onRestore={handleRestore}
          onDelete={handleDelete}
        />
      </section>

      <section style={{ marginBottom: "1.5rem" }}>
        <h2 style={{ fontSize: "1.05rem", margin: "0 0 0.35rem" }}>排除／封鎖節點</h2>
        <p style={{ color: "var(--muted)", fontSize: "0.88rem" }}>
          被標記為 out_of_scope 或 blocked 的 pyramid 節點（不含限制規則表）。
        </p>
        <NodeTable
          rows={excludedNodes}
          nodesById={nodesById}
          emptyText="沒有排除或封鎖節點。"
          canWrite={canWrite}
          busyId={busyId}
          actionMode="excluded"
          onEdit={startEdit}
          onApprove={handleApprove}
          onReject={handleReject}
          onRestore={handleRestore}
          onDelete={handleDelete}
        />
      </section>

      <section style={{ marginBottom: "1.5rem" }}>
        <h2 style={{ fontSize: "1.05rem", margin: "0 0 0.35rem" }}>限制規則</h2>
        <p style={{ color: "var(--muted)", fontSize: "0.88rem" }}>
          來自 Strategy Intake「限制／不做的事」。若要調整，請到策略 Intake 修改後重新套用。
        </p>
        {rules.length === 0 ? (
          <p style={{ margin: 0, color: "var(--muted)", fontSize: "0.9rem" }}>尚無限制規則。</p>
        ) : (
          <div className="table-wrap card" style={{ padding: 0 }}>
            <table>
              <thead>
                <tr>
                  <th>原始限制</th>
                  <th>比對模式</th>
                  <th>動作</th>
                  <th>版本</th>
                </tr>
              </thead>
              <tbody>
                {rules.map((rule) => (
                  <tr key={rule.id}>
                    <td>{rule.description}</td>
                    <td>{rule.match_pattern}</td>
                    <td>{rule.action}</td>
                    <td>{rule.source_intake_version ? `v${rule.source_intake_version}` : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {canWrite ? (
        <div className="card">
          <h2 style={{ fontSize: "1rem", marginTop: 0 }}>批次匯入</h2>
          <p style={{ margin: "0 0 0.75rem", color: "var(--muted)", fontSize: "0.88rem" }}>
            每行格式：`層級,關鍵字` 或僅關鍵字（預設 pillar）。匯入後仍可在上方各區塊編輯。
          </p>
          <Field label="匯入後狀態">
            <select
              className="input"
              value={batchStatus}
              onChange={(e) => setBatchStatus(e.target.value as DefaultStatus)}
              style={{ maxWidth: 280 }}
            >
              {BUSINESS_FIT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </Field>
          <textarea
            className="input"
            rows={5}
            value={batchText}
            onChange={(e) => setBatchText(e.target.value)}
            placeholder={"pillar,台中紗窗維修\ncluster,修理紗窗\nlong_tail,換紗窗價格"}
            style={{ marginTop: "0.75rem" }}
          />
          <button
            type="button"
            className="btn btn-primary"
            style={{ marginTop: "0.75rem" }}
            disabled={busyId !== null}
            onClick={handleBatchImport}
          >
            匯入批次
          </button>
        </div>
      ) : null}
    </RequirePermission>
  );
}
