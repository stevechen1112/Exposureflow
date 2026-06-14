"""Stripe checkout, portal, and webhook handling."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select

from exposureflow_api.config import settings


def stripe_enabled() -> bool:
    return bool(settings.stripe_secret_key)


def create_checkout_session(
    *,
    account_id: UUID,
    plan_code: str,
    billing_interval: str = "month",
    customer_email: str | None = None,
) -> dict:
    if not stripe_enabled():
        return {
            "mode": "dev",
            "checkout_url": f"{settings.app_base_url}/app/demo/settings/billing?upgraded={plan_code}",
            "session_id": f"dev_checkout_{plan_code}",
        }
    import stripe

    stripe.api_key = settings.stripe_secret_key
    from exposureflow_api.billing.plans import PLAN_DEFINITIONS

    spec = next((p for p in PLAN_DEFINITIONS if p["plan_code"] == plan_code), None)
    if spec is None:
        raise ValueError(f"Unknown plan: {plan_code}")
    amount = spec["price_monthly_cents"] if billing_interval == "month" else spec["price_yearly_cents"]
    metadata = {"account_id": str(account_id), "plan_code": plan_code}
    session = stripe.checkout.Session.create(
        mode="subscription",
        customer_email=customer_email,
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": f"ExposureFlow {spec['name']}"},
                    "unit_amount": amount,
                    "recurring": {"interval": "month" if billing_interval == "month" else "year"},
                },
                "quantity": 1,
            }
        ],
        success_url=f"{settings.app_base_url}/app/{{CHECKOUT_SESSION_ID}}/settings/billing?success=1",
        cancel_url=f"{settings.app_base_url}/settings/billing?canceled=1",
        metadata=metadata,
        subscription_data={"metadata": metadata},
    )
    return {"mode": "stripe", "checkout_url": session.url, "session_id": session.id}


def create_billing_portal_session(*, customer_id: str) -> dict:
    if not stripe_enabled():
        return {"mode": "dev", "portal_url": f"{settings.app_base_url}/settings/billing"}
    import stripe

    stripe.api_key = settings.stripe_secret_key
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=f"{settings.app_base_url}/settings/billing",
    )
    return {"mode": "stripe", "portal_url": session.url}


async def _resolve_account_id(db, subscription_obj: dict) -> UUID | None:
    account_id_str = (subscription_obj.get("metadata") or {}).get("account_id")
    if account_id_str:
        return UUID(account_id_str)
    from exposureflow_api.models.commercial import Subscription

    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == subscription_obj["id"])
    )
    sub = result.scalar_one_or_none()
    if sub:
        return sub.account_id
    return None


async def handle_stripe_webhook(payload: bytes, signature: str | None, db) -> dict:
    if not stripe_enabled():
        return {"mode": "dev", "handled": False}
    import stripe

    from exposureflow_api.billing.service import update_subscription_from_stripe
    from exposureflow_api.models.tenant import Account

    stripe.api_key = settings.stripe_secret_key
    event = stripe.Webhook.construct_event(
        payload, signature or "", settings.stripe_webhook_secret or ""
    )
    event_type = event["type"]
    obj = event["data"]["object"]

    if event_type == "checkout.session.completed":
        account_id = UUID(obj["metadata"]["account_id"])
        plan_code = obj["metadata"].get("plan_code")
        customer_id = obj.get("customer")
        account = await db.get(Account, account_id)
        if account and customer_id:
            account.billing_customer_id = str(customer_id)
        subscription_id = obj.get("subscription")
        if subscription_id:
            await update_subscription_from_stripe(
                db,
                account_id,
                stripe_subscription_id=str(subscription_id),
                status="active",
                plan_code=plan_code,
            )
    elif event_type == "customer.subscription.updated":
        account_id = await _resolve_account_id(db, obj)
        if account_id is None:
            return {"mode": "stripe", "handled": False, "type": event_type, "reason": "no account"}
        plan_code = (obj.get("metadata") or {}).get("plan_code")
        await update_subscription_from_stripe(
            db,
            account_id,
            stripe_subscription_id=obj["id"],
            status=obj["status"],
            plan_code=plan_code,
            period_start=datetime.fromtimestamp(obj["current_period_start"], tz=UTC),
            period_end=datetime.fromtimestamp(obj["current_period_end"], tz=UTC),
        )
    elif event_type == "customer.subscription.deleted":
        account_id = await _resolve_account_id(db, obj)
        if account_id:
            await update_subscription_from_stripe(
                db,
                account_id,
                stripe_subscription_id=obj["id"],
                status="canceled",
            )
    elif event_type == "invoice.payment_failed":
        customer = obj.get("customer")
        result = await db.execute(select(Account).where(Account.billing_customer_id == str(customer)))
        account = result.scalar_one_or_none()
        if account:
            account.billing_status = "past_due"
    return {"mode": "stripe", "handled": True, "type": event_type}
