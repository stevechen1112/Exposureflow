"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { PageHeader } from "@/components/PageHeader";
import { getApiClient } from "@/lib/api-client";

type Plan = {
  id: string;
  name: string;
  plan_code: string;
  price_monthly_cents: number;
  limits_json: Record<string, unknown>;
};

export default function BillingPage() {
  const params = useParams<{ workspaceId: string }>();
  const client = getApiClient(params.workspaceId);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [subscription, setSubscription] = useState<Record<string, unknown> | null>(null);
  const [usage, setUsage] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([client.listPlans(), client.getSubscription(), client.getBillingUsage()])
      .then(([p, s, u]) => {
        setPlans(p as Plan[]);
        setSubscription(s);
        setUsage(u);
      })
      .catch((err: Error) => setError(err.message));
  }, [client]);

  async function upgrade(planCode: string) {
    setBusy(planCode);
    try {
      const session = await client.startCheckout(planCode);
      const url = String(session.checkout_url ?? "");
      if (url) window.location.href = url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Checkout failed");
    } finally {
      setBusy(null);
    }
  }

  async function openPortal() {
    setBusy("portal");
    try {
      const session = await client.openBillingPortal();
      const url = String(session.portal_url ?? "");
      if (url) window.location.href = url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Portal failed");
    } finally {
      setBusy(null);
    }
  }

  const currentPlanCode =
    subscription && typeof subscription.plan === "object" && subscription.plan !== null
      ? String((subscription.plan as Record<string, unknown>).plan_code ?? "")
      : "";

  return (
    <>
      <PageHeader title="計費與方案" subtitle="訂閱、配額與 Stripe 帳單入口" />
      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}

      {subscription ? (
        <section className="card" style={{ marginBottom: "1.5rem" }}>
          <h3>目前訂閱</h3>
          <p>
            方案：<strong>{currentPlanCode || "—"}</strong> · 狀態：{String(subscription.status ?? "")}
          </p>
          <button type="button" onClick={openPortal} disabled={busy === "portal"}>
            管理付款方式
          </button>
        </section>
      ) : null}

      {usage ? (
        <section className="card" style={{ marginBottom: "1.5rem" }}>
          <h3>本月用量</h3>
          <pre style={{ fontSize: "0.85rem", overflow: "auto" }}>
            {JSON.stringify(usage.metrics ?? {}, null, 2)}
          </pre>
        </section>
      ) : null}

      <section className="card">
        <h3>可升級方案</h3>
        <div style={{ display: "grid", gap: "1rem", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
          {plans.map((plan) => (
            <article key={plan.id} className="card" style={{ padding: "1rem" }}>
              <h4>{plan.name}</h4>
              <p>${(plan.price_monthly_cents / 100).toFixed(0)} / 月</p>
              <p style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
                站點上限 {String(plan.limits_json.site_limit ?? "—")} · 工作區{" "}
                {String(plan.limits_json.workspace_limit ?? "—")}
              </p>
              <button
                type="button"
                disabled={plan.plan_code === currentPlanCode || busy === plan.plan_code}
                onClick={() => upgrade(plan.plan_code)}
              >
                {plan.plan_code === currentPlanCode ? "目前方案" : "升級"}
              </button>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}
