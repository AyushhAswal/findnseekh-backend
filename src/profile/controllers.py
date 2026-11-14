from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.profile.dtos import (
    StudentProfileReadSchema,
    StudentProfileUpdateSchema,
    TeacherProfileCreateSchema,
    TeacherProfileReadSchema,
    TeacherProfileUpdateSchema,
    TeacherPublicProfileSchema,
)
from src.profile.models import StudentProfileModel, TeacherProfileModel
from src.roles.models import RoleModel, UserRoleModel
from src.users.models import UserModel
from src.utils.auth import require_active_session
from src.utils.responses import ApiResponse


def _check_teacher_role(db: Session, user_id: int) -> None:
    """Verify the user has the teacher role."""
    teacher_role = db.query(RoleModel).filter(RoleModel.name == "teacher").first()
    if teacher_role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher role not available",
        )
    user_role = (
        db.query(UserRoleModel)
        .filter(UserRoleModel.user_id == user_id, UserRoleModel.role_id == teacher_role.id)
        .first()
    )
    if user_role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a teacher to perform this action",
        )


def create_teacher_profile(db: Session, token: str, body: TeacherProfileCreateSchema) -> ApiResponse:
    """Create a teacher profile for the authenticated user."""
    payload = require_active_session(token, db)
    user_id = payload.get("_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    _check_teacher_role(db, user_id)

    # Check if profile already exists
    existing = (
        db.query(TeacherProfileModel)
        .filter(TeacherProfileModel.user_id == user_id)
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Teacher profile already exists. Use PUT to update.",
        )

    profile = TeacherProfileModel(
        user_id=user_id,
        bio=body.bio,
        qualification=body.qualification,
        skills=body.skills or [],
        experience_years=body.experience_years,
        city=body.city,
        state=body.state,
        teaching_mode=body.teaching_mode,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    return ApiResponse(
        status=status.HTTP_201_CREATED,
        message="Teacher profile created successfully",
        data=TeacherProfileReadSchema.model_validate(profile).model_dump(mode="json"),
    )


def get_my_teacher_profile(db: Session, token: str) -> ApiResponse:
    """Get the authenticated teacher's own profile."""
    payload = require_active_session(token, db)
    user_id = payload.get("_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    _check_teacher_role(db, user_id)

    profile = (
        db.query(TeacherProfileModel)
        .filter(TeacherProfileModel.user_id == user_id)
        .first()
    )
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found",
        )

    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Teacher profile fetched successfully",
        data=TeacherProfileReadSchema.model_validate(profile).model_dump(mode="json"),
    )


def update_my_teacher_profile(db: Session, token: str, body: TeacherProfileUpdateSchema) -> ApiResponse:
    """Update the authenticated teacher's own profile."""
    payload = require_active_session(token, db)
    user_id = payload.get("_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    _check_teacher_role(db, user_id)

    profile = (
        db.query(TeacherProfileModel)
        .filter(TeacherProfileModel.user_id == user_id)
        .first()
    )
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found",
        )

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(profile, key, value)

    db.commit()
    db.refresh(profile)

    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Teacher profile updated successfully",
        data=TeacherProfileReadSchema.model_validate(profile).model_dump(mode="json"),
    )


def get_teacher_public_profile(db: Session, user_id: int) -> ApiResponse:
    """Get a teacher's public profile by user_id."""
    profile = (
        db.query(TeacherProfileModel)
        .filter(TeacherProfileModel.user_id == user_id)
        .first()
    )
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found",
        )

    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    data = TeacherPublicProfileSchema(
        id=profile.id,
        user_id=profile.user_id,
        name=user.name,
        bio=profile.bio,
        qualification=profile.qualification,
        skills=profile.skills or [],
        experience_years=profile.experience_years,
        city=profile.city,
        state=profile.state,
        teaching_mode=profile.teaching_mode,
        is_verified=profile.is_verified,
    ).model_dump(mode="json")

    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Teacher public profile fetched successfully",
        data=data,
    )


def get_my_student_profile(db: Session, token: str) -> ApiResponse:
    """Get the authenticated student's own profile."""
    payload = require_active_session(token, db)
    user_id = payload.get("_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    profile = (
        db.query(StudentProfileModel)
        .filter(StudentProfileModel.user_id == user_id)
        .first()
    )
    if profile is None:
        profile = StudentProfileModel(user_id=user_id, skills_to_learn=[])
        db.add(profile)
        db.commit()
        db.refresh(profile)

    dto = StudentProfileReadSchema.model_validate(profile)
    dto.phone = user.phone
    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Student profile fetched successfully",
        data=dto.model_dump(mode="json"),
    )


def update_my_student_profile(db: Session, token: str, body: StudentProfileUpdateSchema) -> ApiResponse:
    """Update the authenticated student's own profile."""
    payload = require_active_session(token, db)
    user_id = payload.get("_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    profile = (
        db.query(StudentProfileModel)
        .filter(StudentProfileModel.user_id == user_id)
        .first()
    )
    if profile is None:
        profile = StudentProfileModel(user_id=user_id, skills_to_learn=[])
        db.add(profile)
        db.flush()

    update_data = body.model_dump(exclude_unset=True)
    if "phone" in update_data:
        phone_val = update_data.pop("phone")
        user.phone = phone_val

    for key, value in update_data.items():
        if value is not None:
            setattr(profile, key, value)

    db.commit()
    db.refresh(profile)
    db.refresh(user)

    dto = StudentProfileReadSchema.model_validate(profile)
    dto.phone = user.phone

    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Student profile updated successfully",
        data=dto.model_dump(mode="json"),
    )
