from pydantic import BaseModel


class LaunchCheckItem(BaseModel):
    id: str
    name: str
    category: str
    status: str
    message: str
    evidence: str | None = None


class LaunchChecklistResponse(BaseModel):
    overall: str
    passed: int
    failed: int
    warned: int
    total: int
    checks: list[LaunchCheckItem]
