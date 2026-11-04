from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class SkillListingCreateSchema(BaseModel):
    """Validation schema for creating a skill listing."""

    title: str = Field(min_length=1, max_length=140)
    description: str = Field(min_length=1)
    category_id: int
    level: str = Field(default="beginner")
    price_amount: Decimal = Field(default=0, ge=0)
    currency: str = Field(default="INR")
    price_unit: str = Field(default="session")
    teaching_mode: str = Field(default="both")
    city: Optional[str] = Field(default=None, max_length=100)
    area: Optional[str] = Field(default=None, max_length=200)

    @field_validator("title")
    @classmethod
    def _strip_title(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Title cannot be blank")
        return s

    @field_validator("description")
    @classmethod
    def _strip_description(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Description cannot be blank")
        return s

    @field_validator("level")
    @classmethod
    def _validate_level(cls, v: str) -> str:
        allowed = {"beginner", "intermediate", "advanced", "all_levels"}
        if v not in allowed:
            raise ValueError(f"level must be one of {allowed}")
        return v

    @field_validator("teaching_mode")
    @classmethod
    def _validate_teaching_mode(cls, v: str) -> str:
        allowed = {"online", "offline", "both"}
        if v not in allowed:
            raise ValueError(f"teaching_mode must be one of {allowed}")
        return v


class SkillListingUpdateSchema(BaseModel):
    """Validation schema for updating a skill listing."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=140)
    description: Optional[str] = Field(default=None, min_length=1)
    category_id: Optional[int] = None
    level: Optional[str] = Field(default=None)
    price_amount: Optional[Decimal] = Field(default=None, ge=0)
    currency: Optional[str] = Field(default=None)
    price_unit: Optional[str] = Field(default=None)
    teaching_mode: Optional[str] = Field(default=None)
    city: Optional[str] = Field(default=None, max_length=100)
    area: Optional[str] = Field(default=None, max_length=200)

    @field_validator("title")
    @classmethod
    def _strip_title(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = v.strip()
        if not s:
            raise ValueError("Title cannot be blank")
        return s

    @field_validator("description")
    @classmethod
    def _strip_description(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = v.strip()
        if not s:
            raise ValueError("Description cannot be blank")
        return s

    @field_validator("level")
    @classmethod
    def _validate_level(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        allowed = {"beginner", "intermediate", "advanced", "all_levels"}
        if v not in allowed:
            raise ValueError(f"level must be one of {allowed}")
        return v

    @field_validator("teaching_mode")
    @classmethod
    def _validate_teaching_mode(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        allowed = {"online", "offline", "both"}
        if v not in allowed:
            raise ValueError(f"teaching_mode must be one of {allowed}")
        return v


class SkillListingStatusSchema(BaseModel):
    """Validation schema for updating listing status."""

    status: str

    @field_validator("status")
    @classmethod
    def _validate_status(cls, v: str) -> str:
        allowed = {"draft", "published", "paused", "archived"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


class SkillListingReadSchema(BaseModel):
    """Output serialization schema for skill listing."""

    id: int
    teacher_id: int
    category_id: int
    title: str
    description: str
    level: str
    price_amount: Decimal
    currency: str
    price_unit: str
    teaching_mode: str
    city: Optional[str] = None
    area: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SkillListingPublicSchema(BaseModel):
    """Public-facing skill listing with safe teacher summary."""

    id: int
    teacher_id: int
    teacher_name: str
    category_id: int
    category_name: str
    title: str
    description: str
    level: str
    price_amount: Decimal
    currency: str
    price_unit: str
    teaching_mode: str
    city: Optional[str] = None
    area: Optional[str] = None
    status: str

    model_config = {"from_attributes": True}
