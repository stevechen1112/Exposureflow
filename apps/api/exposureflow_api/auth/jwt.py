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


def create_access_token(user_id: UUID, email: str, name: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "email": email,
        "name": name,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> AuthContext:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        return AuthContext(
            user_id=UUID(payload["sub"]),
            email=payload["email"],
            name=payload["name"],
        )
    except (JWTError, KeyError, ValueError) as exc:
        raise ValueError("Invalid token") from exc
