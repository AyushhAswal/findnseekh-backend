from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class TeacherProfileCreateSchema(BaseModel):
    """Validation schema for creating a teacher profile."""

    bio: Optional[str] = Field(default=None, max_length=1000)
    qualification: Optional[str] = Field(default=None, max_length=150)
    experience_years: int = Field(default=0, ge=0)
    city: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    teaching_mode: str = Field(default="both")

    @field_validator("teaching_mode")
    @classmethod
    def _validate_teaching_mode(cls, v: str) -> str:
        allowed = {"online", "offline", "both"}
        if v not in allowed:
            raise ValueError(f"teaching_mode must be one of {allowed}")
        return v


class TeacherProfileUpdateSchema(BaseModel):
    """Validation schema for updating a teacher profile."""

    bio: Optional[str] = Field(default=None, max_length=1000)
    qualification: Optional[str] = Field(default=None, max_length=150)
    experience_years: Optional[int] = Field(default=None, ge=0)
    city: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    teaching_mode: Optional[str] = Field(default=None)

    @field_validator("teaching_mode")
    @classmethod
    def _validate_teaching_mode(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        allowed = {"online", "offline", "both"}
        if v not in allowed:
            raise ValueError(f"teaching_mode must be one of {allowed}")
        return v


class TeacherProfileReadSchema(BaseModel):
    """Output serialization schema for teacher profile."""

    id: int
    user_id: int
    bio: Optional[str] = None
    qualification: Optional[str] = None
    experience_years: int
    city: Optional[str] = None
    state: Optional[str] = None
    teaching_mode: str
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TeacherPublicProfileSchema(BaseModel):
    """Public-facing teacher profile. Excludes private data."""

    id: int
    user_id: int
    name: str
    bio: Optional[str] = None
    qualification: Optional[str] = None
    experience_years: int
    city: Optional[str] = None
    state: Optional[str] = None
    teaching_mode: str
    is_verified: bool

    model_config = {"from_attributes": True}
