from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


class TeacherCardSchema(BaseModel):
    """Schema for teacher summary cards on home page and search/listing pages."""

    id: int
    user_id: int
    name: str
    specialty: str
    rating: float = 4.8
    reviews_count: int = 0
    experience_years: int = 0
    city: Optional[str] = None
    state: Optional[str] = None
    location: str = ""
    teaching_mode: str = "both"
    hourly_rate: Decimal = Decimal("500.00")
    currency: str = "INR"
    price_unit: str = "hour"
    skills: List[str] = Field(default_factory=list)
    avatar: Optional[str] = None
    is_verified: bool = False
    is_new: bool = False
    bio: Optional[str] = None


class TeacherPaginationSchema(BaseModel):
    """Pagination envelope for teacher listings."""

    total: int
    page: int
    page_size: int
    teachers: List[TeacherCardSchema]

