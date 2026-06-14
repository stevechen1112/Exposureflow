"""Enterprise SSO / SAML configuration (dev mock + config storage)."""

from __future__ import annotations

from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.common.crypto import decrypt_secret, encrypt_secret
from exposureflow_api.common.errors import APIError
from exposureflow_api.config import settings
from exposureflow_api.security.settings import get_or_create_security_settings


def _validate_sso_url(url: str | None) -> None:
    if not url:
        return
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise APIError(
            code="INVALID_SSO_URL",
            message="SAML SSO URL must be a valid HTTPS URL.",
            status_code=400,
        )


async def update_sso_config(
    db: AsyncSession,
    workspace_id: UUID,
    *,
    sso_enabled: bool,
    saml_entity_id: str | None,
    saml_sso_url: str | None,
    saml_certificate: str | None,
) -> dict:
    if sso_enabled:
        _validate_sso_url(saml_sso_url)
    sec = await get_or_create_security_settings(db, workspace_id)
    sec.sso_enabled = sso_enabled
    sec.saml_entity_id = saml_entity_id
    sec.saml_sso_url = saml_sso_url
    if saml_certificate:
        sec.saml_certificate_encrypted = encrypt_secret(saml_certificate)
    await db.flush()
    return {
        "sso_enabled": sec.sso_enabled,
        "saml_entity_id": sec.saml_entity_id,
        "saml_sso_url": sec.saml_sso_url,
    }


async def initiate_sso_login(db: AsyncSession, workspace_id: UUID, email: str) -> dict:
    sec = await get_or_create_security_settings(db, workspace_id)
    if not sec.sso_enabled:
        raise APIError(code="SSO_DISABLED", message="SSO is not enabled.", status_code=400)
    if settings.app_env != "production":
        return {
            "mode": "dev",
            "redirect_url": f"{settings.app_base_url}/auth/sso/callback?workspace_id={workspace_id}&email={email}",
        }
    if not sec.saml_sso_url:
        raise APIError(code="SSO_MISCONFIGURED", message="SAML SSO URL missing.", status_code=400)
    _validate_sso_url(sec.saml_sso_url)
    return {
        "mode": "saml",
        "redirect_url": sec.saml_sso_url,
        "entity_id": sec.saml_entity_id,
    }


def get_saml_certificate_pem(encrypted: str | None) -> str | None:
    if not encrypted:
        return None
    return decrypt_secret(encrypted)
