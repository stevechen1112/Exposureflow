"use client";

import { useCallback, useEffect, useState } from "react";
import { createClient } from "@exposureflow/sdk";
import { API_BASE_URL, storageKey } from "@/lib/config";

function isStepUpRequired(message: string) {
  return message.includes("2FA_STEP_UP_REQUIRED") || message.includes("2FA step-up");
}

export function TwoFactorStepUpGate({
  workspaceId,
  children,
}: {
  workspaceId?: string;
  children: React.ReactNode;
}) {
  const [needsStepUp, setNeedsStepUp] = useState(false);
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [checked, setChecked] = useState(false);

  const probe = useCallback(async () => {
    const token = localStorage.getItem(storageKey("token"));
    const ws =
      workspaceId ?? localStorage.getItem(storageKey("workspaceId")) ?? undefined;
    if (!token || !ws) {
      setChecked(true);
      return;
    }
    const client = createClient({
      baseUrl: API_BASE_URL,
      token,
      workspaceId: ws,
    });
    try {
      // Must hit a workspace-scoped endpoint that runs require_workspace_access (2FA amr check).
      await client.listSites();
      setNeedsStepUp(false);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "";
      if (isStepUpRequired(msg)) {
        setNeedsStepUp(true);
      }
    } finally {
      setChecked(true);
    }
  }, [workspaceId]);

  useEffect(() => {
    probe();
  }, [probe]);

  async function submitStepUp() {
    if (code.length < 6) {
      setError("請輸入 6 位數驗證碼");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const token = localStorage.getItem(storageKey("token"));
      const client = createClient({ baseUrl: API_BASE_URL, token: token ?? undefined });
      const res = await client.stepUpTwoFactor(code);
      localStorage.setItem(storageKey("token"), res.access_token);
      setNeedsStepUp(false);
      setCode("");
      window.location.reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "驗證失敗");
    } finally {
      setBusy(false);
    }
  }

  if (!checked) {
    return <div style={{ padding: "2rem", color: "var(--muted)" }}>驗證工作區存取…</div>;
  }

  if (needsStepUp) {
    return (
      <div className="card" style={{ maxWidth: 420, margin: "3rem auto" }}>
        <h2 style={{ marginTop: 0, fontSize: "1.1rem" }}>需要 2FA 驗證</h2>
        <p style={{ color: "var(--muted)", fontSize: "0.9rem", lineHeight: 1.6 }}>
          此工作區已啟用雙因素驗證。請輸入驗證器 App 的 6 位數代碼以繼續。
        </p>
        <input
          value={code}
          onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
          placeholder="000000"
          inputMode="numeric"
          autoComplete="one-time-code"
          style={{ width: "100%", letterSpacing: "0.3em", textAlign: "center", fontSize: "1.25rem" }}
        />
        {error ? <p style={{ color: "var(--danger)", marginTop: "0.75rem" }}>{error}</p> : null}
        <button
          type="button"
          className="btn btn-primary"
          style={{ marginTop: "1rem", width: "100%" }}
          disabled={busy || code.length < 6}
          onClick={submitStepUp}
        >
          {busy ? "驗證中…" : "確認並繼續"}
        </button>
      </div>
    );
  }

  return <>{children}</>;
}
