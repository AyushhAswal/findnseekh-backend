from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class LearningRequestCreateSchema(BaseModel):
    """Validation schema for creating a learning request."""

    skill_listing_id: int
    message: str = Field(min_length=1, max_length=1000)

    @field_validator("message")
    @classmethod
    def _strip_message(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Message cannot be blank")
        return s


class LearningRequestReadSchema(BaseModel):
    """Output serialization schema for learning request."""

    id: int
    skill_listing_id: int
    student_id: int
    teacher_id: int
    message: str
    status: str
    teacher_response: Optional[str] = None
    responded_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LearningRequestPublicSchema(BaseModel):
    """Public-facing learning request with participant info."""

    id: int
    skill_listing_id: int
    skill_title: str
    student_id: int
    student_name: str
    teacher_id: int
    teacher_name: str
    message: str
    status: str
    teacher_response: Optional[str] = None
    responded_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}
