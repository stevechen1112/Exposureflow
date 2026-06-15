import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.common.audit import record_audit
from exposureflow_api.common.crypto import encrypt_secret, hash_api_key
from exposureflow_api.jobs.registry import JOB_DEFINITIONS
from exposureflow_api.models import (
    Account,
    ApiKey,
    IntegrationCredential,
    JobDefinition,
    Organization,
    Site,
    User,
    UserSecurity,
    Workspace,
    WorkspaceInvitation,
    WorkspaceMembership,
)


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def list_user_workspaces(db: AsyncSession, user_id: UUID) -> list[tuple[Workspace, str]]:
    result = await db.execute(
        select(Workspace, WorkspaceMembership.role)
        .join(WorkspaceMembership, WorkspaceMembership.workspace_id == Workspace.id)
        .where(WorkspaceMembership.user_id == user_id, WorkspaceMembership.status == "active")
    )
    return list(result.all())


async def _ensure_dev_demo_site(db: AsyncSession, workspace_id: UUID) -> None:
    """Local dev only: ensure at least one site so dashboard routes are usable."""
    from exposureflow_api.config import settings

    if settings.app_env != "local":
        return

    existing = await db.execute(select(Site.id).where(Site.workspace_id == workspace_id).limit(1))
    if existing.scalar_one_or_none() is not None:
        return

    await create_site(
        db,
        workspace_id=workspace_id,
        domain="demo.example.com",
        site_name="Demo Site",
        primary_locale="zh-TW",
        target_countries=["TW"],
        target_languages=["zh-TW"],
        industry="saas",
        business_model="b2b",
    )


async def bootstrap_dev_user_workspace(
    db: AsyncSession, email: str, name: str
) -> tuple[User, Workspace]:
    user = await get_user_by_email(db, email)
    if user is None:
        user = User(email=email, name=name)
        db.add(user)
        await db.flush()
        db.add(UserSecurity(user_id=user.id, email_verified=True))

    existing = await list_user_workspaces(db, user.id)
    if existing:
        workspace = existing[0][0]
        await _ensure_dev_demo_site(db, workspace.id)
        return user, workspace

    account = Account(name=f"{name} Account", account_type="direct")
    db.add(account)
    await db.flush()

    organization = Organization(account_id=account.id, name=f"{name} Organization")
    db.add(organization)
    await db.flush()

    workspace = Workspace(
        account_id=account.id,
        organization_id=organization.id,
        name="Default Workspace",
        workspace_type="agency_internal",
        plan_limits={"sites": 10, "members": 25},
        usage_limits={"api_calls_monthly": 100_000},
        feature_flags={"serp_matrix": True, "ai_visibility": True},
    )
    db.add(workspace)
    await db.flush()

    membership = WorkspaceMembership(
        workspace_id=workspace.id,
        user_id=user.id,
        role="owner",
    )
    db.add(membership)
    await db.flush()

    from exposureflow_api.billing.service import ensure_starter_subscription

    await ensure_starter_subscription(db, account.id)
    await _ensure_dev_demo_site(db, workspace.id)
    return user, workspace


async def apply_dev_role_override(
    db: AsyncSession, user_id: UUID, workspace_id: UUID, role: str
) -> None:
    """Local dev: set membership role so UI role-switcher can be exercised."""
    from exposureflow_api.config import settings

    if settings.app_env == "production":
        return

    allowed = {
        "owner",
        "admin",
        "strategist",
        "editor",
        "analyst",
        "client_viewer",
        "billing_admin",
        "support_admin",
    }
    if role not in allowed:
        return

    result = await db.execute(
        select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.user_id == user_id,
        )
    )
    membership = result.scalar_one_or_none()
    if membership is not None:
        membership.role = role
        await db.flush()


async def bootstrap_platform_support(db: AsyncSession) -> User | None:
    """Seed platform support admin for internal ops (dev/local only)."""
    from exposureflow_api.config import settings

    if settings.app_env == "production":
        return None

    email = "support@example.com"
    user = await get_user_by_email(db, email)
    if user is None:
        user = User(email=email, name="Platform Support")
        db.add(user)
        await db.flush()
        db.add(UserSecurity(user_id=user.id, email_verified=True))

    workspaces = list((await db.execute(select(Workspace).where(Workspace.status == "active").limit(5))).scalars().all())
    if not workspaces:
        return None

    for ws in workspaces[:1]:
        existing = await db.execute(
            select(WorkspaceMembership).where(
                WorkspaceMembership.workspace_id == ws.id,
                WorkspaceMembership.user_id == user.id,
            )
        )
        if existing.scalar_one_or_none() is None:
            db.add(
                WorkspaceMembership(
                    workspace_id=ws.id,
                    user_id=user.id,
                    role="support_admin",
                )
            )
    await db.flush()
    return user


async def create_workspace_for_user(
    db: AsyncSession,
    user: User,
    name: str,
    workspace_type: str,
    client_name: str | None,
    default_locale: str,
) -> Workspace:
    memberships = await list_user_workspaces(db, user.id)
    if not memberships:
        raise ValueError("User has no account context")

    account_id = memberships[0][0].account_id
    organization_id = memberships[0][0].organization_id

    from exposureflow_api.billing.quota import check_workspace_limit

    await check_workspace_limit(db, account_id)

    workspace = Workspace(
        account_id=account_id,
        organization_id=organization_id,
        name=name,
        workspace_type=workspace_type,
        client_name=client_name,
        default_locale=default_locale,
        plan_limits={"sites": 10, "members": 25},
        usage_limits={"api_calls_monthly": 100_000},
        feature_flags={"serp_matrix": True, "ai_visibility": True},
    )
    db.add(workspace)
    await db.flush()

    db.add(
        WorkspaceMembership(
            workspace_id=workspace.id,
            user_id=user.id,
            role="owner",
        )
    )
    await db.flush()
    return workspace


def normalize_site_domain(domain: str) -> str:
    value = domain.strip().lower()
    for prefix in ("https://", "http://"):
        if value.startswith(prefix):
            value = value[len(prefix) :]
    value = value.split("/")[0].split("?")[0].rstrip(".")
    return value


async def get_site_in_workspace(db: AsyncSession, workspace_id: UUID, site_id: UUID) -> Site | None:
    result = await db.execute(
        select(Site).where(Site.id == site_id, Site.workspace_id == workspace_id)
    )
    return result.scalar_one_or_none()


async def create_site(
    db: AsyncSession,
    workspace_id: UUID,
    domain: str,
    site_name: str,
    primary_locale: str,
    target_countries: list[str],
    target_languages: list[str],
    industry: str | None,
    business_model: str | None,
) -> Site:
    from exposureflow_api.billing.quota import check_site_limit

    await check_site_limit(db, workspace_id)

    normalized = normalize_site_domain(domain)
    site = Site(
        workspace_id=workspace_id,
        domain=normalized,
        site_name=site_name.strip(),
        primary_locale=primary_locale,
        target_countries=target_countries,
        target_languages=target_languages,
        industry=industry,
        business_model=business_model,
    )
    db.add(site)
    await db.flush()
    return site


async def update_site(
    db: AsyncSession,
    workspace_id: UUID,
    site_id: UUID,
    *,
    domain: str | None = None,
    site_name: str | None = None,
    primary_locale: str | None = None,
    target_countries: list[str] | None = None,
    target_languages: list[str] | None = None,
    industry: str | None = None,
    business_model: str | None = None,
) -> Site:
    site = await get_site_in_workspace(db, workspace_id, site_id)
    if site is None:
        raise ValueError("Site not found")

    if domain is not None:
        site.domain = normalize_site_domain(domain)
    if site_name is not None:
        site.site_name = site_name.strip()
    if primary_locale is not None:
        site.primary_locale = primary_locale
    if target_countries is not None:
        site.target_countries = target_countries
    if target_languages is not None:
        site.target_languages = target_languages
    if industry is not None:
        site.industry = industry.strip() or None
    if business_model is not None:
        site.business_model = business_model.strip() or None

    await db.flush()
    return site


async def list_workspace_members(
    db: AsyncSession, workspace_id: UUID
) -> list[tuple[WorkspaceMembership, User]]:
    result = await db.execute(
        select(WorkspaceMembership, User)
        .join(User, User.id == WorkspaceMembership.user_id)
        .where(WorkspaceMembership.workspace_id == workspace_id)
    )
    return list(result.all())


async def update_member_role(
    db: AsyncSession,
    workspace_id: UUID,
    member_user_id: UUID,
    role: str,
    actor_user_id: UUID,
) -> WorkspaceMembership:
    result = await db.execute(
        select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.user_id == member_user_id,
        )
    )
    membership = result.scalar_one_or_none()
    if membership is None:
        raise ValueError("Member not found")
    membership.role = role
    await record_audit(
        db,
        action="member.role_updated",
        target_type="workspace_membership",
        target_id=str(membership.id),
        workspace_id=workspace_id,
        actor_user_id=actor_user_id,
        metadata={"new_role": role},
    )
    await db.flush()
    return membership


async def create_invitation(
    db: AsyncSession,
    workspace_id: UUID,
    email: str,
    role: str,
    invited_by: UUID,
) -> tuple[WorkspaceInvitation, str]:
    from exposureflow_api.billing.quota import check_member_limit

    await check_member_limit(db, workspace_id)

    token = secrets.token_urlsafe(32)
    invitation = WorkspaceInvitation(
        workspace_id=workspace_id,
        email=email.lower(),
        role=role,
        token_hash=hash_api_key(token),
        invited_by=invited_by,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db.add(invitation)
    await record_audit(
        db,
        action="invitation.created",
        target_type="workspace_invitation",
        target_id=email,
        workspace_id=workspace_id,
        actor_user_id=invited_by,
        metadata={"role": role},
    )
    await db.flush()
    return invitation, token


async def accept_invitation(
    db: AsyncSession, token: str, user: User
) -> WorkspaceMembership:
    token_hash = hash_api_key(token)
    result = await db.execute(
        select(WorkspaceInvitation).where(
            WorkspaceInvitation.token_hash == token_hash,
            WorkspaceInvitation.status == "pending",
        )
    )
    invitation = result.scalar_one_or_none()
    if invitation is None or invitation.expires_at < datetime.now(UTC):
        raise ValueError("Invalid or expired invitation")
    if invitation.email.lower() != user.email.lower():
        raise ValueError("Invitation email mismatch")

    invitation.status = "accepted"
    invitation.accepted_at = datetime.now(UTC)

    membership = WorkspaceMembership(
        workspace_id=invitation.workspace_id,
        user_id=user.id,
        role=invitation.role,
        invited_by=invitation.invited_by,
    )
    db.add(membership)
    await record_audit(
        db,
        action="invitation.accepted",
        target_type="workspace_invitation",
        target_id=str(invitation.id),
        workspace_id=invitation.workspace_id,
        actor_user_id=user.id,
    )
    await db.flush()
    return membership


async def store_integration_credential(
    db: AsyncSession,
    workspace_id: UUID,
    provider: str,
    credential_type: str,
    payload: str,
    site_id: UUID | None = None,
    credential_name: str = "default",
    actor_user_id: UUID | None = None,
) -> IntegrationCredential:
    credential = IntegrationCredential(
        workspace_id=workspace_id,
        site_id=site_id,
        provider=provider,
        credential_name=credential_name,
        credential_type=credential_type,
        encrypted_payload=encrypt_secret(payload),
    )
    db.add(credential)
    await record_audit(
        db,
        action="integration.credential_stored",
        target_type="integration_credential",
        target_id=provider,
        workspace_id=workspace_id,
        actor_user_id=actor_user_id,
        metadata={"credential_type": credential_type, "site_id": str(site_id) if site_id else None},
    )
    await db.flush()
    return credential


async def create_api_key(
    db: AsyncSession,
    workspace_id: UUID,
    name: str,
    scopes: list[str],
    created_by: UUID,
) -> tuple[ApiKey, str]:
    raw_key = f"ef_{secrets.token_urlsafe(32)}"
    api_key = ApiKey(
        workspace_id=workspace_id,
        name=name,
        key_prefix=raw_key[:8],
        key_hash=hash_api_key(raw_key),
        scopes=scopes,
        created_by=created_by,
    )
    db.add(api_key)
    await record_audit(
        db,
        action="api_key.created",
        target_type="api_key",
        target_id=name,
        workspace_id=workspace_id,
        actor_user_id=created_by,
        metadata={"scopes": scopes},
    )
    await db.flush()
    return api_key, raw_key


async def seed_job_definitions(db: AsyncSession) -> None:
    for item in JOB_DEFINITIONS:
        result = await db.execute(
            select(JobDefinition).where(JobDefinition.job_type == item["job_type"])
        )
        if result.scalar_one_or_none() is None:
            db.add(JobDefinition(**item))
    await db.flush()
