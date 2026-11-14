from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.utils.db import Base


class UserModel(Base):
    """SQLAlchemy model representing the user_table schema mapping."""

    __tablename__ = "user_table"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
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
    user_roles = relationship("UserRoleModel", back_populates="user", cascade="all, delete-orphan")
    teacher_profile = relationship("TeacherProfileModel", back_populates="user", uselist=False, cascade="all, delete-orphan")
    student_profile = relationship("StudentProfileModel", back_populates="user", uselist=False, cascade="all, delete-orphan")
    skill_listings = relationship("SkillListingModel", back_populates="teacher", cascade="all, delete-orphan")
    learning_requests_as_student = relationship("LearningRequestModel", foreign_keys="LearningRequestModel.student_id", back_populates="student")
    learning_requests_as_teacher = relationship("LearningRequestModel", foreign_keys="LearningRequestModel.teacher_id", back_populates="teacher")


class RevokedTokenModel(Base):
    """SQLAlchemy model for storing revoked JWT token hashes."""

    __tablename__ = "revoked_token_table"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
