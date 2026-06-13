from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.auth.deps import get_current_user
from exposureflow_api.auth.jwt import AuthContext, create_access_token
from exposureflow_api.auth.permissions import require_permission
from exposureflow_api.common.audit import record_audit
from exposureflow_api.common.errors import APIError, not_found
from exposureflow_api.config import settings
from exposureflow_api.database import get_db
from exposureflow_api.jobs.service import enqueue_job
from exposureflow_api.models import IntegrationCredential, Site, Workspace
from exposureflow_api.tenants import service
from exposureflow_api.tenants.schemas import (
    ApiKeyCreate,
    ApiKeyResponse,
    DevTokenRequest,
    DevTokenResponse,
    IntegrationCredentialCreate,
    IntegrationCredentialResponse,
    InvitationAccept,
    InvitationCreate,
    InvitationResponse,
    JobRunResponse,
    MeResponse,
    MemberResponse,
    MemberRoleUpdate,
    SiteCreate,
    SiteResponse,
    UserResponse,
    WorkspaceCreate,
    WorkspaceResponse,
    WorkspaceSummary,
)

router = APIRouter(prefix="/api/v1", tags=["tenants"])


@router.get("/me", response_model=MeResponse)
async def get_me(
    user_ctx: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MeResponse:
    user = await service.get_user_by_id(db, user_ctx.user_id)
    if user is None:
        raise not_found("User")

    rows = await service.list_user_workspaces(db, user.id)
    workspaces = [
        WorkspaceSummary(
            id=workspace.id,
            name=workspace.name,
            workspace_type=workspace.workspace_type,
            role=role,
            status=workspace.status,
        )
        for workspace, role in rows
    ]
    return MeResponse(user=UserResponse.model_validate(user), workspaces=workspaces)


@router.post("/auth/dev-token", response_model=DevTokenResponse)
async def create_dev_token(
    body: DevTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> DevTokenResponse:
    if settings.app_env == "production":
        raise not_found("Endpoint")

    user, _workspace = await service.bootstrap_dev_user_workspace(db, body.email, body.name)
    await record_audit(
        db,
        action="auth.dev_login",
        target_type="user",
        target_id=str(user.id),
        actor_user_id=user.id,
        metadata={"email": user.email},
    )
    await db.commit()
    token = create_access_token(user.id, user.email, user.name)
    return DevTokenResponse(access_token=token)


@router.get("/workspaces", response_model=list[WorkspaceResponse])
async def list_workspaces(
    user_ctx: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Workspace]:
    rows = await service.list_user_workspaces(db, user_ctx.user_id)
    return [workspace for workspace, _role in rows]


@router.post("/workspaces", response_model=WorkspaceResponse)
async def create_workspace(
    body: WorkspaceCreate,
    user_ctx: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Workspace:
    user = await service.get_user_by_id(db, user_ctx.user_id)
    if user is None:
        raise not_found("User")

    workspace = await service.create_workspace_for_user(
        db,
        user=user,
        name=body.name,
        workspace_type=body.workspace_type,
        client_name=body.client_name,
        default_locale=body.default_locale,
    )
    await record_audit(
        db,
        action="workspace.created",
        target_type="workspace",
        target_id=str(workspace.id),
        workspace_id=workspace.id,
        actor_user_id=user.id,
    )
    await db.commit()
    await db.refresh(workspace)
    return workspace


@router.get("/sites", response_model=list[SiteResponse])
async def list_sites(
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:read")),
    db: AsyncSession = Depends(get_db),
) -> list[Site]:
    _user, _membership, workspace_id = ctx
    result = await db.execute(select(Site).where(Site.workspace_id == workspace_id))
    return list(result.scalars().all())


@router.post("/sites", response_model=SiteResponse)
async def create_site(
    body: SiteCreate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("site:write")),
    db: AsyncSession = Depends(get_db),
) -> Site:
    user, _membership, workspace_id = ctx
    site = await service.create_site(
        db,
        workspace_id=workspace_id,
        domain=body.domain,
        site_name=body.site_name,
        primary_locale=body.primary_locale,
        target_countries=body.target_countries,
        target_languages=body.target_languages,
        industry=body.industry,
        business_model=body.business_model,
    )
    await record_audit(
        db,
        action="site.created",
        target_type="site",
        target_id=str(site.id),
        workspace_id=workspace_id,
        actor_user_id=user.user_id,
    )
    await db.commit()
    await db.refresh(site)
    return site


@router.get("/members", response_model=list[MemberResponse])
async def list_members(
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("member:read")),
    db: AsyncSession = Depends(get_db),
) -> list[MemberResponse]:
    _user, _membership, workspace_id = ctx
    rows = await service.list_workspace_members(db, workspace_id)
    return [
        MemberResponse(
            user_id=membership.user_id,
            email=user.email,
            name=user.name,
            role=membership.role,
            status=membership.status,
        )
        for membership, user in rows
    ]


@router.patch("/members/{member_user_id}", response_model=MemberResponse)
async def update_member(
    member_user_id: UUID,
    body: MemberRoleUpdate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("member:write")),
    db: AsyncSession = Depends(get_db),
) -> MemberResponse:
    user, _membership, workspace_id = ctx
    membership = await service.update_member_role(
        db, workspace_id, member_user_id, body.role, user.user_id
    )
    member_user = await service.get_user_by_id(db, member_user_id)
    if member_user is None:
        raise not_found("User")
    await db.commit()
    return MemberResponse(
        user_id=membership.user_id,
        email=member_user.email,
        name=member_user.name,
        role=membership.role,
        status=membership.status,
    )


@router.post("/invitations", response_model=InvitationResponse)
async def create_invitation(
    body: InvitationCreate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("invitation:write")),
    db: AsyncSession = Depends(get_db),
) -> InvitationResponse:
    user, _membership, workspace_id = ctx
    invitation, token = await service.create_invitation(
        db, workspace_id, body.email, body.role, user.user_id
    )
    await db.commit()
    return InvitationResponse(
        id=invitation.id,
        email=invitation.email,
        role=invitation.role,
        status=invitation.status,
        expires_at=invitation.expires_at,
        invite_token=token if settings.app_env != "production" else None,
    )


@router.post("/invitations/accept", response_model=MemberResponse)
async def accept_invitation(
    body: InvitationAccept,
    user_ctx: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MemberResponse:
    user = await service.get_user_by_id(db, user_ctx.user_id)
    if user is None:
        raise not_found("User")
    try:
        membership = await service.accept_invitation(db, body.token, user)
    except ValueError as exc:
        raise APIError(code="INVITATION_INVALID", message=str(exc), status_code=400) from exc
    member_user = user
    await db.commit()
    return MemberResponse(
        user_id=membership.user_id,
        email=member_user.email,
        name=member_user.name,
        role=membership.role,
        status=membership.status,
    )


@router.post("/integrations/credentials", response_model=IntegrationCredentialResponse)
async def create_integration_credential(
    body: IntegrationCredentialCreate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("integration:write")),
    db: AsyncSession = Depends(get_db),
) -> IntegrationCredential:
    user, _membership, workspace_id = ctx
    credential = await service.store_integration_credential(
        db,
        workspace_id=workspace_id,
        provider=body.provider,
        credential_type=body.credential_type,
        payload=body.payload,
        site_id=body.site_id,
        credential_name=body.credential_name,
        actor_user_id=user.user_id,
    )
    await db.commit()
    await db.refresh(credential)
    return credential


@router.get("/integrations/credentials", response_model=list[IntegrationCredentialResponse])
async def list_integration_credentials(
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("integration:read")),
    db: AsyncSession = Depends(get_db),
) -> list[IntegrationCredential]:
    _user, _membership, workspace_id = ctx
    result = await db.execute(
        select(IntegrationCredential).where(IntegrationCredential.workspace_id == workspace_id)
    )
    return list(result.scalars().all())


@router.post("/api-keys", response_model=ApiKeyResponse)
async def create_api_key(
    body: ApiKeyCreate,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("api_key:write")),
    db: AsyncSession = Depends(get_db),
) -> ApiKeyResponse:
    user, _membership, workspace_id = ctx
    api_key, raw_key = await service.create_api_key(
        db, workspace_id, body.name, body.scopes, user.user_id
    )
    await db.commit()
    return ApiKeyResponse(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes,
        status=api_key.status,
        raw_key=raw_key,
    )


@router.post("/jobs/enqueue", response_model=JobRunResponse)
async def enqueue_workspace_job(
    job_type: str,
    ctx: tuple[AuthContext, object, UUID] = Depends(require_permission("job:write")),
    db: AsyncSession = Depends(get_db),
) -> JobRunResponse:
    _user, _membership, workspace_id = ctx
    run = await enqueue_job(db, workspace_id=workspace_id, job_type=job_type)
    await db.commit()
    await db.refresh(run)
    return JobRunResponse.model_validate(run)
