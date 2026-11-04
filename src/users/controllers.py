from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.users.dtos import (
    TokenResponseSchema,
    UpdateUserSchema,
    UserLoginSchema,
    UserReadSchema,
    UserRegisterSchema,
    UserWithRolesSchema,
)
from src.users.models import UserModel
from src.roles.models import RoleModel, UserRoleModel
from src.utils.auth import create_access_token, hash_password, require_active_session, revoke_token, verify_password
from src.utils.responses import ApiResponse


def register_user(db: Session, body: UserRegisterSchema) -> ApiResponse:
    """Register a new user and assign the default student role."""
    # Check if email already exists
    existing = db.query(UserModel).filter(UserModel.email == body.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    # Create user
    user = UserModel(
        name=body.name,
        email=body.email,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.flush()  # Get user.id before commit

    # Assign default student role
    student_role = db.query(RoleModel).filter(RoleModel.name == "student").first()
    if student_role is None:
        student_role = RoleModel(name="student")
        db.add(student_role)
        db.flush()

    user_role = UserRoleModel(user_id=user.id, role_id=student_role.id)
    db.add(user_role)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    db.refresh(user)
    return ApiResponse(
        status=status.HTTP_201_CREATED,
        message="User registered successfully",
        data=UserReadSchema.model_validate(user).model_dump(mode="json"),
    )


def login_user(db: Session, body: UserLoginSchema) -> ApiResponse:
    """Authenticate user and return JWT token."""
    user = db.query(UserModel).filter(UserModel.email == body.email).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    token = create_access_token(user.id)
    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Login successful",
        data=TokenResponseSchema(access_token=token).model_dump(mode="json"),
    )


def get_current_user(db: Session, token: str) -> ApiResponse:
    """Get current authenticated user with roles."""
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

    # Get user roles
    roles = (
        db.query(RoleModel.name)
        .join(UserRoleModel, RoleModel.id == UserRoleModel.role_id)
        .filter(UserRoleModel.user_id == user.id)
        .all()
    )
    role_names = [r[0] for r in roles]

    data = UserWithRolesSchema(
        id=user.id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        is_active=user.is_active,
        roles=role_names,
        created_at=user.created_at,
        updated_at=user.updated_at,
    ).model_dump(mode="json")

    return ApiResponse(
        status=status.HTTP_200_OK,
        message="User profile fetched successfully",
        data=data,
    )


def update_current_user(db: Session, token: str, body: UpdateUserSchema) -> ApiResponse:
    """Update current authenticated user's profile fields."""
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

    update_data = body.model_dump(exclude_unset=True)
    if "name" in update_data:
        user.name = update_data["name"]
    if "phone" in update_data:
        user.phone = update_data["phone"]

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Update failed due to a constraint violation",
        )

    db.refresh(user)
    return ApiResponse(
        status=status.HTTP_200_OK,
        message="User profile updated successfully",
        data=UserReadSchema.model_validate(user).model_dump(mode="json"),
    )


def logout_user(db: Session, token: str) -> ApiResponse:
    """Revoke the current token."""
    revoke_token(token, db)
    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Logged out successfully",
        data=None,
    )


def become_teacher(db: Session, token: str) -> ApiResponse:
    """Add teacher role and create teacher profile atomically."""
    from src.profile.models import TeacherProfileModel

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

    # Check if already a teacher
    teacher_role = db.query(RoleModel).filter(RoleModel.name == "teacher").first()
    if teacher_role is None:
        teacher_role = RoleModel(name="teacher")
        db.add(teacher_role)
        db.flush()

    existing_user_role = (
        db.query(UserRoleModel)
        .filter(UserRoleModel.user_id == user_id, UserRoleModel.role_id == teacher_role.id)
        .first()
    )
    if existing_user_role is not None:
        # Already a teacher, return existing profile
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
        from src.profile.dtos import TeacherProfileReadSchema
        return ApiResponse(
            status=status.HTTP_200_OK,
            message="User is already a teacher",
            data=TeacherProfileReadSchema.model_validate(profile).model_dump(mode="json"),
        )

    # Add teacher role
    user_role = UserRoleModel(user_id=user_id, role_id=teacher_role.id)
    db.add(user_role)

    # Create teacher profile
    profile = TeacherProfileModel(user_id=user_id)
    db.add(profile)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Failed to activate teacher role",
        )

    db.refresh(profile)
    from src.profile.dtos import TeacherProfileReadSchema
    return ApiResponse(
        status=status.HTTP_201_CREATED,
        message="Teacher role activated and profile created successfully",
        data=TeacherProfileReadSchema.model_validate(profile).model_dump(mode="json"),
    )
