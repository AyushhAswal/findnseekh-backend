from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CategoryReadSchema(BaseModel):
    """Output serialization schema for category."""

    id: int
    name: str
    slug: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
