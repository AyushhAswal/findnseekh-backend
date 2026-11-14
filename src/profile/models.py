from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.utils.db import Base


class TeacherProfileModel(Base):
    """SQLAlchemy model representing the teacher_profile_table schema mapping."""

    __tablename__ = "teacher_profile_table"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_table.id"), nullable=False, unique=True, index=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    qualification: Mapped[str | None] = mapped_column(String(150), nullable=True)
    skills: Mapped[list[str] | None] = mapped_column(JSON, nullable=True, default=list)
    experience_years: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    teaching_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="both")
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
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
    user = relationship("UserModel", back_populates="teacher_profile")


class StudentProfileModel(Base):
    """SQLAlchemy model representing the student_profile_table schema mapping."""

    __tablename__ = "student_profile_table"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_table.id"), nullable=False, unique=True, index=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    learning_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="both")
    learning_level: Mapped[str] = mapped_column(String(20), nullable=False, default="beginner")
    learning_goals: Mapped[str | None] = mapped_column(Text, nullable=True)
    skills_to_learn: Mapped[list[str] | None] = mapped_column(JSON, nullable=True, default=list)
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
    user = relationship("UserModel", back_populates="student_profile")
