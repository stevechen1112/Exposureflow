"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { isValidSiteId } from "@/lib/hooks";

export default function SiteLayout({ children }: { children: React.ReactNode }) {
  const params = useParams<{ workspaceId: string; siteId: string }>();
  const router = useRouter();
  const valid = isValidSiteId(params.siteId);

  useEffect(() => {
    if (!valid) {
      router.replace(`/app/${params.workspaceId}/onboarding`);
    }
  }, [valid, params.workspaceId, router]);

  if (!valid) {
    return (
      <p style={{ padding: "2rem", color: "var(--muted)" }}>站點設定未完成，正在導向 Onboarding…</p>
    );
  }

  return <>{children}</>;
}
