"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { DEV_AUTH_ENABLED, storageKey } from "@/lib/config";

export function SessionBootstrap({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(!DEV_AUTH_ENABLED);

  useEffect(() => {
    if (!DEV_AUTH_ENABLED) return;

    const token = localStorage.getItem(storageKey("token"));
    if (token) {
      setReady(true);
      return;
    }

    router.replace("/app-entry");
  }, [router]);

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

  if (!ready) {
    return <div style={{ padding: "2rem", color: "var(--muted)" }}>載入工作區…</div>;
  }

  return <>{children}</>;
}
