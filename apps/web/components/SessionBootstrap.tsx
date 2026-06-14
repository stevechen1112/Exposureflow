"use client";

import { useEffect, useState } from "react";
import { DEV_AUTH_ENABLED } from "@/lib/config";
import { ensureDevSession } from "@/lib/api-client";

export function SessionBootstrap({ children }: { children: React.ReactNode }) {
  const [ready, setReady] = useState(!DEV_AUTH_ENABLED);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!DEV_AUTH_ENABLED) return;
    let cancelled = false;
    (async () => {
      try {
        await ensureDevSession();
        if (!cancelled) setReady(true);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Session bootstrap failed");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (!DEV_AUTH_ENABLED) {
    return (
      <div className="card" style={{ margin: "2rem" }}>
        <p>正式環境請使用 Clerk 登入（dev bootstrap 已停用）。</p>
        <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
          本機開發請設定 NEXT_PUBLIC_ENABLE_DEV_AUTH=true。
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card" style={{ margin: "2rem" }}>
        <p>無法連線 API：{error}</p>
        <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
          請確認後端已啟動（預設 http://localhost:8000）且 NEXT_PUBLIC_API_BASE_URL 正確。
        </p>
      </div>
    );
  }

  if (!ready) {
    return <div style={{ padding: "2rem", color: "var(--muted)" }}>載入工作區…</div>;
  }

  return <>{children}</>;
}
