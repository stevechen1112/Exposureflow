"use client";

import { useParams } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { SessionBootstrap } from "@/components/SessionBootstrap";
import { TwoFactorStepUpGate } from "@/components/TwoFactorStepUpGate";

export default function WorkspaceLayout({ children }: { children: React.ReactNode }) {
  const params = useParams<{ workspaceId: string; siteId?: string }>();
  const workspaceId = params.workspaceId;
  const siteId = params.siteId;

  return (
    <SessionBootstrap>
      <TwoFactorStepUpGate>
        <AppShell workspaceId={workspaceId} siteId={siteId}>
          {children}
        </AppShell>
      </TwoFactorStepUpGate>
    </SessionBootstrap>
  );
}
