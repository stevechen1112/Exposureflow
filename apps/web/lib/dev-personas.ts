import { ROLE_LABELS, type WorkspaceRole } from "@/lib/permissions";

export type DevPersona = {
  role: WorkspaceRole;
  email: string;
  name: string;
  blurb: string;
};

export type DevPersonaTier = {
  id: string;
  label: string;
  description: string;
  personas: DevPersona[];
};

/** Default dev login — full workspace access for day-to-day local testing. */
export const DEFAULT_DEV_PERSONA: DevPersona = {
  role: "owner",
  email: "owner@example.com",
  name: "Owner",
  blurb: "完整權限，工作區擁有者",
};

export const DEV_PERSONA_TIERS: DevPersonaTier[] = [
  {
    id: "workspace",
    label: "工作區管理",
    description: "成員、整合、站點與方案治理",
    personas: [
      { role: "owner", email: "owner@example.com", name: "Owner", blurb: "完整權限，工作區擁有者" },
      { role: "admin", email: "admin@example.com", name: "Admin", blurb: "管理成員、整合與站點" },
    ],
  },
  {
    id: "consulting",
    label: "顧問團隊",
    description: "策略、內容與分析（權限遞減）",
    personas: [
      {
        role: "strategist",
        email: "strategist@example.com",
        name: "Strategist",
        blurb: "策略規劃、機會核准、內容審核",
      },
      { role: "editor", email: "editor@example.com", name: "Editor", blurb: "內容編輯與審核，無整合管理" },
      { role: "analyst", email: "analyst@example.com", name: "Analyst", blurb: "唯讀分析，無核准操作" },
    ],
  },
  {
    id: "external",
    label: "客戶與計費",
    description: "對外入口與財務檢視",
    personas: [
      {
        role: "client_viewer",
        email: "client@example.com",
        name: "Client",
        blurb: "客戶入口：月報、Roadmap 核准",
      },
      {
        role: "billing_admin",
        email: "billing@example.com",
        name: "Billing",
        blurb: "僅計費與方案管理",
      },
    ],
  },
  {
    id: "platform",
    label: "平台營運",
    description: "Internal Admin（非客戶工作區角色）",
    personas: [
      {
        role: "support_admin",
        email: "support@example.com",
        name: "Support",
        blurb: "平台營運後台",
      },
    ],
  },
];

export const DEV_PERSONAS: DevPersona[] = DEV_PERSONA_TIERS.flatMap((tier) => tier.personas);

export function personaLabel(role: WorkspaceRole): string {
  return ROLE_LABELS[role];
}
