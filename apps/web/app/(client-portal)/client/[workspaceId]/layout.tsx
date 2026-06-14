"use client";

import { useParams } from "next/navigation";
import { ClientShell } from "@/components/ClientShell";
import { SessionBootstrap } from "@/components/SessionBootstrap";
import { WorkspaceAuthProvider } from "@/lib/auth-context";

export default function ClientPortalLayout({ children }: { children: React.ReactNode }) {
  const params = useParams<{ workspaceId: string }>();
  return (
    <SessionBootstrap>
      <WorkspaceAuthProvider workspaceId={params.workspaceId}>
        <ClientShell workspaceId={params.workspaceId}>{children}</ClientShell>
      </WorkspaceAuthProvider>
    </SessionBootstrap>
  );
}
