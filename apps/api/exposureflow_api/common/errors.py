from typing import Any

from fastapi import HTTPException, status


class APIError(HTTPException):
    def __init__(self, code: str, message: str, status_code: int, details: dict[str, Any] | None = None):
        super().__init__(
            status_code=status_code,
            detail={"error": {"code": code, "message": message, "details": details or {}}},
        )


def workspace_access_denied() -> APIError:
    return APIError(
        code="WORKSPACE_ACCESS_DENIED",
        message="You do not have access to this workspace.",
        status_code=status.HTTP_403_FORBIDDEN,
    )


def not_found(resource: str) -> APIError:
    return APIError(
        code="NOT_FOUND",
        message=f"{resource} not found.",
        status_code=status.HTTP_404_NOT_FOUND,
    )


def validation_error(message: str, code: str = "VALIDATION_ERROR") -> APIError:
    return APIError(
        code=code,
        message=message,
        status_code=status.HTTP_400_BAD_REQUEST,
    )
