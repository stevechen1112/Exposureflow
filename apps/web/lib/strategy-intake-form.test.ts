import { describe, expect, it } from "vitest";
import {
  EMPTY_STRATEGY_INTAKE_FORM,
  formValuesToIntakePayload,
  intakeToFormValues,
  isIntakeApproved,
} from "./strategy-intake-form";

describe("strategy-intake-form", () => {
  it("converts multiline fields to json lists", () => {
    const payload = formValuesToIntakePayload({
      ...EMPTY_STRATEGY_INTAKE_FORM,
      strategic_goals: "台中紗窗曝光\n台北區域服務",
      constraints: "  ",
    });
    expect(payload.strategic_goals_json).toEqual(["台中紗窗曝光", "台北區域服務"]);
    expect(payload.constraints_json).toEqual([]);
  });

  it("round-trips intake values", () => {
    const values = intakeToFormValues({
      id: "1",
      workspace_id: "w",
      site_id: "s",
      status: "draft",
      version_number: 1,
      parent_intake_id: null,
      is_current: false,
      archived_at: null,
      change_summary: "初版",
      company_summary: "ezfix",
      market_notes: null,
      customer_segments_json: ["家庭"],
      domestic_markets_json: ["TW"],
      export_markets_json: [],
      sales_regions_json: ["台中"],
      strategic_goals_json: ["自然曝光"],
      constraints_json: ["不做全台"],
      approved_by: null,
      approved_at: null,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    });
    expect(values.customer_segments).toBe("家庭");
    expect(isIntakeApproved("approved")).toBe(true);
  });
});
