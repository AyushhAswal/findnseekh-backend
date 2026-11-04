from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class UserRegisterSchema(BaseModel):
    """Validation schema for user registration."""

    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Name cannot be blank")
        return s

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, v: str) -> str:
        s = v.strip().lower()
        if not s:
            raise ValueError("Email cannot be blank")
        return s


class UserLoginSchema(BaseModel):
    """Validation schema for user login."""

    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, v: str) -> str:
        s = v.strip().lower()
        if not s:
            raise ValueError("Email cannot be blank")
        return s


class UpdateUserSchema(BaseModel):
    """Validation schema for updating user profile fields."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = v.strip()
        if not s:
            raise ValueError("Name cannot be blank")
        return s


class UserReadSchema(BaseModel):
    """Output serialization schema for user data. Excludes sensitive fields."""

    id: int
    name: str
    email: str
    phone: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserWithRolesSchema(BaseModel):
    """Output schema including user roles."""

    id: int
    name: str
    email: str
    phone: Optional[str] = None
    is_active: bool
    roles: list[str] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TokenResponseSchema(BaseModel):
    """Output schema for login token response."""

    access_token: str
    token_type: str = "bearer"
