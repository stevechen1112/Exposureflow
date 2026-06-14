from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from jose import JWTError, jwt
from pydantic import BaseModel

from exposureflow_api.config import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


class TokenPayload(BaseModel):
    sub: str
    email: str
    name: str


class AuthContext(BaseModel):
    user_id: UUID
    email: str
    name: str
    amr: list[str] = []
    impersonated_by: UUID | None = None
    impersonation_session_id: UUID | None = None


def create_access_token(
    user_id: UUID,
    email: str,
    name: str,
    *,
    amr: list[str] | None = None,
    impersonated_by: UUID | None = None,
    impersonation_session_id: UUID | None = None,
    expire_minutes: int | None = None,
) -> str:
    ttl = expire_minutes if expire_minutes is not None else ACCESS_TOKEN_EXPIRE_MINUTES
    expire = datetime.now(UTC) + timedelta(minutes=ttl)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "email": email,
        "name": name,
        "exp": expire,
    }
    if amr:
        payload["amr"] = amr
    if impersonated_by:
        payload["impersonated_by"] = str(impersonated_by)
    if impersonation_session_id:
        payload["impersonation_session_id"] = str(impersonation_session_id)
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> AuthContext:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        return AuthContext(
            user_id=UUID(payload["sub"]),
            email=payload["email"],
            name=payload["name"],
            amr=list(payload.get("amr") or []),
            impersonated_by=UUID(payload["impersonated_by"]) if payload.get("impersonated_by") else None,
            impersonation_session_id=(
                UUID(payload["impersonation_session_id"]) if payload.get("impersonation_session_id") else None
            ),
        )
    except (JWTError, KeyError, ValueError) as exc:
        raise ValueError("Invalid token") from exc
