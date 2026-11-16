from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


class TeacherCardSchema(BaseModel):
    """Schema for teacher summary cards on home page and search/listing pages."""

    id: int
    user_id: int
    name: str
    specialty: str
    category: Optional[str] = None
    category_id: Optional[str] = None
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


class TeacherReviewSchema(BaseModel):
    """Schema for individual student review."""

    id: str
    student_name: str
    rating: float = 5.0
    date: str
    comment: str


class TeacherFaqSchema(BaseModel):
    """Schema for teacher profile FAQ items."""

    question: str
    answer: str


class TeacherListingItemSchema(BaseModel):
    """Schema for published skill listing displayed on teacher profile."""

    id: int
    title: str
    description: str
    level: str
    price_amount: float
    currency: str = "INR"
    price_unit: str = "session"
    teaching_mode: str = "both"
    city: Optional[str] = None
    area: Optional[str] = None


class TeacherDetailSchema(TeacherCardSchema):
    """Comprehensive teacher profile schema for teacher detail page."""

    about: Optional[str] = None
    languages: List[str] = Field(default_factory=lambda: ["English", "Hindi"])
    qualifications: List[str] = Field(default_factory=list)
    reviews: List[TeacherReviewSchema] = Field(default_factory=list)
    faqs: List[TeacherFaqSchema] = Field(default_factory=list)
    listings: List[TeacherListingItemSchema] = Field(default_factory=list)


class TeacherEnquiryCreateSchema(BaseModel):
    """Request schema for student sending enquiry to a teacher."""

    teaching_mode: Optional[str] = Field(default="online")
    preferred_date: Optional[str] = Field(default=None)
    message: Optional[str] = Field(default=None, max_length=1000)
    skill_listing_id: Optional[int] = Field(default=None)


class TeacherEnquiryResponseSchema(BaseModel):
    """Response schema for created teacher enquiry."""

    id: int
    teacher_id: int
    student_id: Optional[int] = None
    teaching_mode: str
    preferred_date: Optional[str] = None
    message: str
    status: str = "pending"
    created_at: str

