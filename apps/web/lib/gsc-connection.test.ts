import { describe, expect, it } from "vitest";
import {
  defaultGscProperty,
  findSiteCredential,
  resolveGscConnectionPhase,
} from "./gsc-connection";

describe("gsc-connection", () => {
  it("builds sc-domain property from site domain", () => {
    expect(defaultGscProperty("ezfix.com.tw")).toBe("sc-domain:ezfix.com.tw");
    expect(defaultGscProperty("https://ezfix.com.tw/")).toBe("sc-domain:ezfix.com.tw");
  });

  it("resolves connected phase when sync succeeded", () => {
    expect(
      resolveGscConnectionPhase({
        siteId: "site-1",
        credential: {
          id: "c1",
          site_id: "site-1",
          provider: "gsc",
          credential_name: "default",
          credential_type: "service_account",
          status: "active",
        },
        syncState: {
          provider: "gsc",
          site_id: "site-1",
          last_success_at: "2026-06-14T00:00:00Z",
        },
      }),
    ).toBe("connected");
  });

  it("prefers site-scoped credential", () => {
    const cred = findSiteCredential(
      [
        {
          id: "1",
          site_id: "other",
          provider: "gsc",
          credential_name: "default",
          credential_type: "service_account",
          status: "active",
        },
        {
          id: "2",
          site_id: "site-1",
          provider: "gsc",
          credential_name: "default",
          credential_type: "service_account",
          status: "active",
        },
      ],
      "site-1",
    );
    expect(cred?.id).toBe("2");
  });
});
