"use client";

import { useParams } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { SessionBootstrap } from "@/components/SessionBootstrap";
import { TwoFactorStepUpGate } from "@/components/TwoFactorStepUpGate";
import { WorkspaceAuthProvider } from "@/lib/auth-context";
import { WorkspaceGuard } from "@/components/WorkspaceGuard";

export default function WorkspaceLayout({ children }: { children: React.ReactNode }) {
  const params = useParams<{ workspaceId: string }>();
  const workspaceId = params.workspaceId;

  return (
    <SessionBootstrap>
      <TwoFactorStepUpGate workspaceId={workspaceId}>
        <WorkspaceAuthProvider workspaceId={workspaceId}>
          <WorkspaceGuard workspaceId={workspaceId}>
            <AppShell workspaceId={workspaceId}>{children}</AppShell>
          </WorkspaceGuard>
        </WorkspaceAuthProvider>
      </TwoFactorStepUpGate>
    </SessionBootstrap>
  );
}
