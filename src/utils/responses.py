from pydantic import BaseModel
from typing import Any, Optional


class ApiResponse(BaseModel):
    """Standard JSON response envelope wrapping all successful API responses."""

    status: int
    message: str
    data: Optional[Any] = None
    lastUpdated: Optional[Any] = None
