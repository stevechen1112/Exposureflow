"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { PageHeader } from "@/components/PageHeader";

export default function SettingsPage() {
  const params = useParams<{ workspaceId: string }>();
  const base = `/app/${params.workspaceId}/settings`;
  return (
    <>
      <PageHeader title="設定" subtitle="工作區偏好與導航" />
      <ul style={{ lineHeight: 2 }}>
        <li>
          <Link href={`${base}/integrations`}>整合（GSC、GA4、SERP…）</Link>
        </li>
        <li>
          <Link href={`${base}/members`}>成員與 RBAC</Link>
        </li>
        <li>
          <Link href={`${base}/billing`}>計費與方案</Link>
        </li>
      </ul>
    </>
  );
}
