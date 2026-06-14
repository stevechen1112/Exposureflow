"""Integration credential rotation."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from exposureflow_api.common.audit import record_audit
from exposureflow_api.common.errors import not_found
from exposureflow_api.models import IntegrationCredential
from exposureflow_api.security.kms import default_secret_manager


async def rotate_integration_credential(
    db: AsyncSession,
    *,
    credential_id: UUID,
    workspace_id: UUID,
    actor_user_id: UUID,
) -> IntegrationCredential:
    credential = await db.get(IntegrationCredential, credential_id)
    if credential is None or credential.workspace_id != workspace_id:
        raise not_found("IntegrationCredential")

    new_ciphertext, new_version = default_secret_manager.rotate_ciphertext(
        credential.encrypted_payload
    )
    credential.encrypted_payload = new_ciphertext
    credential.key_version = new_version

    await record_audit(
        db,
        action="integration.credential_rotated",
        target_type="integration_credential",
        target_id=str(credential_id),
        workspace_id=workspace_id,
        actor_user_id=actor_user_id,
        metadata={"provider": credential.provider, "key_version": new_version},
    )
    await db.flush()
    return credential
