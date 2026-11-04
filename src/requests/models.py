from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.utils.db import Base


class LearningRequestModel(Base):
    """SQLAlchemy model representing the learning_request_table schema mapping."""

    __tablename__ = "learning_request_table"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    skill_listing_id: Mapped[int] = mapped_column(Integer, ForeignKey("skill_listing_table.id"), nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_table.id"), nullable=False, index=True)
    teacher_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_table.id"), nullable=False, index=True)
    message: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    teacher_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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
    skill_listing = relationship("SkillListingModel", back_populates="learning_requests")
    student = relationship("UserModel", foreign_keys="LearningRequestModel.student_id", back_populates="learning_requests_as_student")
    teacher = relationship("UserModel", foreign_keys="LearningRequestModel.teacher_id", back_populates="learning_requests_as_teacher")
