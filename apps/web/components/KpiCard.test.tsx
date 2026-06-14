import React from "react";
import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { KpiCard } from "@/components/KpiCard";

describe("KpiCard", () => {
  it("renders label and value", () => {
    const html = renderToStaticMarkup(<KpiCard label="曝光" value={1234} delta={5.2} />);
    expect(html).toContain("曝光");
    expect(html).toContain("1234");
    expect(html).toContain("+5.2%");
  });
});
