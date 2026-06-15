import type { BusinessIntake } from "@exposureflow/shared-types";

export type StrategyIntakeFormValues = {
  company_summary: string;
  market_notes: string;
  customer_segments: string;
  domestic_markets: string;
  export_markets: string;
  sales_regions: string;
  strategic_goals: string;
  constraints: string;
  change_summary: string;
};

export const EMPTY_STRATEGY_INTAKE_FORM: StrategyIntakeFormValues = {
  company_summary: "",
  market_notes: "",
  customer_segments: "",
  domestic_markets: "",
  export_markets: "",
  sales_regions: "",
  strategic_goals: "",
  constraints: "",
  change_summary: "",
};

function linesToList(text: string): string[] {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

function listToLines(value: unknown): string {
  if (!Array.isArray(value)) return "";
  return value.map(String).join("\n");
}

export function intakeToFormValues(intake: BusinessIntake): StrategyIntakeFormValues {
  return {
    company_summary: intake.company_summary ?? "",
    market_notes: intake.market_notes ?? "",
    customer_segments: listToLines(intake.customer_segments_json),
    domestic_markets: listToLines(intake.domestic_markets_json),
    export_markets: listToLines(intake.export_markets_json),
    sales_regions: listToLines(intake.sales_regions_json),
    strategic_goals: listToLines(intake.strategic_goals_json),
    constraints: listToLines(intake.constraints_json),
    change_summary: intake.change_summary ?? "",
  };
}

export function formValuesToIntakePayload(values: StrategyIntakeFormValues) {
  return {
    company_summary: values.company_summary.trim() || null,
    market_notes: values.market_notes.trim() || null,
    customer_segments_json: linesToList(values.customer_segments),
    domestic_markets_json: linesToList(values.domestic_markets),
    export_markets_json: linesToList(values.export_markets),
    sales_regions_json: linesToList(values.sales_regions),
    strategic_goals_json: linesToList(values.strategic_goals),
    constraints_json: linesToList(values.constraints),
    change_summary: values.change_summary.trim() || null,
  };
}

export function intakeStatusLabel(status: string): string {
  switch (status) {
    case "approved":
      return "已核准";
    case "archived":
      return "已封存";
    case "active":
      return "使用中";
    case "draft":
      return "草稿";
    default:
      return status;
  }
}

export function isIntakeApproved(status: string): boolean {
  return status === "approved" || status === "active";
}

export function isCurrentIntake(intake: BusinessIntake): boolean {
  return intake.is_current && intake.status === "approved";
}
