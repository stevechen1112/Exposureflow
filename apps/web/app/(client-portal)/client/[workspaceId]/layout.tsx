"use client";

import { SessionBootstrap } from "@/components/SessionBootstrap";

export default function ClientPortalLayout({ children }: { children: React.ReactNode }) {
  return <SessionBootstrap>{children}</SessionBootstrap>;
}
