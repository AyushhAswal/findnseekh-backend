from typing import Optional
from pydantic import BaseModel


class LocationSuggestionSchema(BaseModel):
    """Schema for location autocomplete suggestion."""

    city: str
    state: Optional[str] = None
    display: str
    teacher_count: int = 0

