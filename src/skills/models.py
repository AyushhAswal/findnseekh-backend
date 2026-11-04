from datetime import datetime
from decimal import Decimal
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.utils.db import Base


class SkillListingModel(Base):
    """SQLAlchemy model representing the skill_listing_table schema mapping."""

    __tablename__ = "skill_listing_table"
    __table_args__ = (
        CheckConstraint("price_amount >= 0", name="chk_price_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    teacher_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_table.id"), nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("category_table.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(140), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    level: Mapped[str] = mapped_column(String(20), nullable=False, default="beginner")
    price_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="INR")
    price_unit: Mapped[str] = mapped_column(String(20), nullable=False, default="session")
    teaching_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="both")
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    area: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    teacher = relationship("UserModel", back_populates="skill_listings")
    category = relationship("CategoryModel", back_populates="skill_listings")
    learning_requests = relationship("LearningRequestModel", back_populates="skill_listing", cascade="all, delete-orphan")
