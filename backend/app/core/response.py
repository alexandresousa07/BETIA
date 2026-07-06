from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    message: str = "OK"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def success_response(data: Any = None, message: str = "OK") -> dict[str, Any]:
    return APIResponse(success=True, data=data, message=message).model_dump(mode="json")


def error_response(message: str, data: Any = None) -> dict[str, Any]:
    return APIResponse(success=False, data=data, message=message).model_dump(mode="json")
