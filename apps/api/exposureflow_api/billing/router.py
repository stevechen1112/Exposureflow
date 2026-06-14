from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.auth.jwt import AuthContext
from exposureflow_api.auth.permissions import require_permission
from exposureflow_api.billing import quota as quota_service
from exposureflow_api.billing.schemas import (
    CheckoutRequest,
    CheckoutResponse,
    PlanResponse,
    PortalResponse,
    SubscriptionResponse,
    UsageSummaryResponse,
    WorkspaceBrandingResponse,
    WorkspaceBrandingUpdate,
    WorkspaceTransferRequest,
)
from exposureflow_api.billing.service import (
    ensure_starter_subscription,
    get_subscription_for_account,
    transfer_workspace,
    upsert_workspace_branding,
)
from exposureflow_api.billing.stripe_service import (
    create_billing_portal_session,
    create_checkout_session,
    handle_stripe_webhook,
    stripe_enabled,
)
from exposureflow_api.common.audit import record_audit
from exposureflow_api.common.errors import APIError, not_found
from exposureflow_api.database import get_db
from exposureflow_api.models.commercial import Plan
from exposureflow_api.models.tenant import Account, Workspace, WorkspaceMembership
from sqlalchemy import select

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])
webhook_router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


async def _account_for_workspace(db: AsyncSession, workspace_id: UUID) -> Account:
    ws = await db.get(Workspace, workspace_id)
    if ws is None:
        raise not_found("Workspace")
    account = await db.get(Account, ws.account_id)
    if account is None:
        raise not_found("Account")
    return account


@router.get("/plans", response_model=list[PlanResponse])
async def list_plans(db: AsyncSession = Depends(get_db)) -> list[Plan]:
    result = await db.execute(select(Plan).where(Plan.active.is_(True)).order_by(Plan.price_monthly_cents))
    return list(result.scalars().all())


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("billing:read")),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionResponse:
    _user, _membership, workspace_id = ctx
    account = await _account_for_workspace(db, workspace_id)
    sub_plan = await get_subscription_for_account(db, account.id)
    if sub_plan is None:
        await ensure_starter_subscription(db, account.id)
        await db.commit()
        sub_plan = await get_subscription_for_account(db, account.id)
        if sub_plan is None:
            raise not_found("Subscription")
    subscription, plan = sub_plan
    return SubscriptionResponse(
        id=subscription.id,
        account_id=subscription.account_id,
        plan=PlanResponse.model_validate(plan),
        status=subscription.status,
        stripe_subscription_id=subscription.stripe_subscription_id,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        trial_end=subscription.trial_end,
        custom_limits_json=subscription.custom_limits_json,
    )


@router.post("/checkout", response_model=CheckoutResponse)
async def start_checkout(
    body: CheckoutRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("billing:read")),
    db: AsyncSession = Depends(get_db),
) -> CheckoutResponse:
    user, _membership, workspace_id = ctx
    account = await _account_for_workspace(db, workspace_id)
    session = create_checkout_session(
        account_id=account.id,
        plan_code=body.plan_code,
        billing_interval=body.billing_interval,
        customer_email=user.email,
    )
    await record_audit(
        db,
        action="billing.checkout.start",
        target_type="account",
        target_id=str(account.id),
        workspace_id=workspace_id,
        actor_user_id=user.user_id,
        metadata={"plan_code": body.plan_code},
    )
    await db.commit()
    return CheckoutResponse(**session)


@router.post("/portal", response_model=PortalResponse)
async def billing_portal(
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("billing:read")),
    db: AsyncSession = Depends(get_db),
) -> PortalResponse:
    _user, _membership, workspace_id = ctx
    account = await _account_for_workspace(db, workspace_id)
    if stripe_enabled() and not account.billing_customer_id:
        raise APIError(
            code="BILLING_CUSTOMER_MISSING",
            message="Complete checkout before opening the billing portal.",
            status_code=400,
        )
    customer_id = account.billing_customer_id or f"dev_{account.id}"
    session = create_billing_portal_session(customer_id=customer_id)
    return PortalResponse(**session)


@router.get("/usage", response_model=UsageSummaryResponse)
async def get_usage(
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("billing:read")),
    db: AsyncSession = Depends(get_db),
) -> UsageSummaryResponse:
    _user, _membership, workspace_id = ctx
    summary = await quota_service.usage_summary(db, workspace_id)
    return UsageSummaryResponse(**summary)


@router.post("/workspaces/{workspace_id}/transfer")
async def transfer_workspace_ownership(
    workspace_id: UUID,
    body: WorkspaceTransferRequest,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("workspace:write")),
    db: AsyncSession = Depends(get_db),
):
    user, _membership, ctx_workspace_id = ctx
    ws = await db.get(Workspace, workspace_id)
    if ws is None:
        raise not_found("Workspace")
    owner_membership = await db.execute(
        select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.user_id == user.user_id,
            WorkspaceMembership.status == "active",
        )
    )
    membership = owner_membership.scalar_one_or_none()
    if membership is None or membership.role != "owner":
        raise APIError(
            code="FORBIDDEN",
            message="Only workspace owners can transfer ownership.",
            status_code=403,
        )
    ctx_account = await _account_for_workspace(db, ctx_workspace_id)
    if ws.account_id != ctx_account.id:
        raise APIError(
            code="FORBIDDEN",
            message="Cannot transfer workspace outside your account.",
            status_code=403,
        )
    workspace = await transfer_workspace(
        db,
        workspace_id,
        to_account_id=body.to_account_id,
        to_organization_id=body.to_organization_id,
        initiated_by=user.user_id,
    )
    await db.commit()
    return {"id": str(workspace.id), "account_id": str(workspace.account_id)}


@router.get("/branding", response_model=WorkspaceBrandingResponse | None)
async def get_branding(
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("workspace:read")),
    db: AsyncSession = Depends(get_db),
):
    _user, _membership, workspace_id = ctx
    from sqlalchemy import select
    from exposureflow_api.models.commercial import WorkspaceBranding

    result = await db.execute(
        select(WorkspaceBranding).where(WorkspaceBranding.workspace_id == workspace_id)
    )
    return result.scalar_one_or_none()


@router.put("/branding", response_model=WorkspaceBrandingResponse)
async def update_branding(
    body: WorkspaceBrandingUpdate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("workspace:write")),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceBrandingResponse:
    _user, _membership, workspace_id = ctx
    limits = await quota_service.get_effective_limits(
        db, (await _account_for_workspace(db, workspace_id)).id
    )
    if not limits.get("white_label_enabled"):
        from exposureflow_api.common.errors import APIError

        raise APIError(
            code="WHITE_LABEL_DISABLED",
            message="White-label requires Agency or Enterprise plan.",
            status_code=403,
        )
    row = await upsert_workspace_branding(db, workspace_id, **body.model_dump())
    await db.commit()
    await db.refresh(row)
    return row


@webhook_router.post("/stripe")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
):
    payload = await request.body()
    result = await handle_stripe_webhook(payload, stripe_signature, db)
    await db.commit()
    return result
