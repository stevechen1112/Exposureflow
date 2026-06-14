"use client";

import { useParams } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { SessionBootstrap } from "@/components/SessionBootstrap";

export default function WorkspaceLayout({ children }: { children: React.ReactNode }) {
  const params = useParams<{ workspaceId: string; siteId?: string }>();
  const workspaceId = params.workspaceId;
  const siteId = params.siteId;

  return (
    <SessionBootstrap>
      <AppShell workspaceId={workspaceId} siteId={siteId}>
        {children}
      </AppShell>
    </SessionBootstrap>
  );
}
