"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ensureDevSession } from "@/lib/api-client";
import { DEV_AUTH_ENABLED } from "@/lib/config";

export default function AppEntryPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!DEV_AUTH_ENABLED) {
      setError("正式環境請使用 Clerk 登入（尚未在此頁嵌入）。");
      return;
    }
    ensureDevSession()
      .then(({ workspaceId, siteId }) => {
        if (workspaceId && siteId) {
          router.replace(`/app/${workspaceId}/sites/${siteId}/dashboard`);
        } else if (workspaceId) {
          router.replace(`/app/${workspaceId}/onboarding`);
        } else {
          setError("dev session 未建立 workspace，請確認 API 已啟動");
        }
      })
      .catch((err: Error) => setError(err.message));
  }, [router]);

  if (error) {
    return (
      <div className="card" style={{ margin: "2rem auto", maxWidth: 480 }}>
        <p style={{ color: "var(--danger)" }}>{error}</p>
      </div>
    );
  }

  return <div style={{ padding: "2rem", color: "var(--muted)", textAlign: "center" }}>正在進入 ExposureFlow…</div>;
}
