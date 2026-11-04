from decimal import Decimal
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.category.models import CategoryModel
from src.roles.models import RoleModel, UserRoleModel
from src.skills.dtos import (
    SkillListingCreateSchema,
    SkillListingPublicSchema,
    SkillListingReadSchema,
    SkillListingStatusSchema,
    SkillListingUpdateSchema,
)
from src.skills.models import SkillListingModel
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


def create_skill_listing(db: Session, token: str, body: SkillListingCreateSchema) -> ApiResponse:
    """Create a new skill listing for the authenticated teacher."""
    payload = require_active_session(token, db)
    user_id = payload.get("_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    _check_teacher_role(db, user_id)

    # Validate category exists and is active
    category = (
        db.query(CategoryModel)
        .filter(CategoryModel.id == body.category_id, CategoryModel.is_active == True)  # noqa: E712
        .first()
    )
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category not found or inactive",
        )

    listing = SkillListingModel(
        teacher_id=user_id,
        category_id=body.category_id,
        title=body.title,
        description=body.description,
        level=body.level,
        price_amount=body.price_amount,
        currency=body.currency,
        price_unit=body.price_unit,
        teaching_mode=body.teaching_mode,
        city=body.city,
        area=body.area,
        status="draft",
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)

    return ApiResponse(
        status=status.HTTP_201_CREATED,
        message="Skill listing created successfully",
        data=SkillListingReadSchema.model_validate(listing).model_dump(mode="json"),
    )


def list_skill_listings(
    db: Session,
    page: int = 1,
    page_size: int = 20,
) -> ApiResponse:
    """Browse published skill listings with pagination."""
    page_size = min(page_size, 50)
    offset = (page - 1) * page_size

    listings = (
        db.query(SkillListingModel)
        .filter(SkillListingModel.status == "published")
        .order_by(SkillListingModel.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    data = []
    for listing in listings:
        teacher = db.query(UserModel).filter(UserModel.id == listing.teacher_id).first()
        category = db.query(CategoryModel).filter(CategoryModel.id == listing.category_id).first()
        data.append(SkillListingPublicSchema(
            id=listing.id,
            teacher_id=listing.teacher_id,
            teacher_name=teacher.name if teacher else "Unknown",
            category_id=listing.category_id,
            category_name=category.name if category else "Unknown",
            title=listing.title,
            description=listing.description,
            level=listing.level,
            price_amount=listing.price_amount,
            currency=listing.currency,
            price_unit=listing.price_unit,
            teaching_mode=listing.teaching_mode,
            city=listing.city,
            area=listing.area,
            status=listing.status,
        ).model_dump(mode="json"))

    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Skill listings fetched successfully",
        data=data,
    )


def get_skill_listing(db: Session, skill_id: int) -> ApiResponse:
    """Get a single skill listing with safe teacher summary."""
    listing = db.query(SkillListingModel).filter(SkillListingModel.id == skill_id).first()
    if listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill listing not found",
        )

    teacher = db.query(UserModel).filter(UserModel.id == listing.teacher_id).first()
    category = db.query(CategoryModel).filter(CategoryModel.id == listing.category_id).first()

    data = SkillListingPublicSchema(
        id=listing.id,
        teacher_id=listing.teacher_id,
        teacher_name=teacher.name if teacher else "Unknown",
        category_id=listing.category_id,
        category_name=category.name if category else "Unknown",
        title=listing.title,
        description=listing.description,
        level=listing.level,
        price_amount=listing.price_amount,
        currency=listing.currency,
        price_unit=listing.price_unit,
        teaching_mode=listing.teaching_mode,
        city=listing.city,
        area=listing.area,
        status=listing.status,
    ).model_dump(mode="json")

    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Skill listing fetched successfully",
        data=data,
    )


def update_skill_listing(db: Session, token: str, skill_id: int, body: SkillListingUpdateSchema) -> ApiResponse:
    """Update an existing skill listing (owner only)."""
    payload = require_active_session(token, db)
    user_id = payload.get("_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    listing = db.query(SkillListingModel).filter(SkillListingModel.id == skill_id).first()
    if listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill listing not found",
        )

    if listing.teacher_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own listings",
        )

    update_data = body.model_dump(exclude_unset=True)
    if "category_id" in update_data and update_data["category_id"] is not None:
        category = (
            db.query(CategoryModel)
            .filter(CategoryModel.id == update_data["category_id"], CategoryModel.is_active == True)  # noqa: E712
            .first()
        )
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found or inactive",
            )

    for key, value in update_data.items():
        if value is not None:
            setattr(listing, key, value)

    db.commit()
    db.refresh(listing)

    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Skill listing updated successfully",
        data=SkillListingReadSchema.model_validate(listing).model_dump(mode="json"),
    )


def archive_skill_listing(db: Session, token: str, skill_id: int) -> ApiResponse:
    """Archive a skill listing (owner only)."""
    payload = require_active_session(token, db)
    user_id = payload.get("_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    listing = db.query(SkillListingModel).filter(SkillListingModel.id == skill_id).first()
    if listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill listing not found",
        )

    if listing.teacher_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only archive your own listings",
        )

    listing.status = "archived"
    db.commit()
    db.refresh(listing)

    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Skill listing archived successfully",
        data=SkillListingReadSchema.model_validate(listing).model_dump(mode="json"),
    )


def get_my_skill_listings(db: Session, token: str) -> ApiResponse:
    """Get current teacher's skill listings."""
    payload = require_active_session(token, db)
    user_id = payload.get("_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    _check_teacher_role(db, user_id)

    listings = (
        db.query(SkillListingModel)
        .filter(SkillListingModel.teacher_id == user_id)
        .order_by(SkillListingModel.created_at.desc())
        .all()
    )

    data = [
        SkillListingReadSchema.model_validate(l).model_dump(mode="json") for l in listings
    ]

    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Your skill listings fetched successfully",
        data=data,
    )


def update_skill_listing_status(db: Session, token: str, skill_id: int, body: SkillListingStatusSchema) -> ApiResponse:
    """Update listing status (owner only)."""
    payload = require_active_session(token, db)
    user_id = payload.get("_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    listing = db.query(SkillListingModel).filter(SkillListingModel.id == skill_id).first()
    if listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill listing not found",
        )

    if listing.teacher_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own listings",
        )

    listing.status = body.status
    db.commit()
    db.refresh(listing)

    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Skill listing status updated successfully",
        data=SkillListingReadSchema.model_validate(listing).model_dump(mode="json"),
    )


def search_skill_listings(
    db: Session,
    query: Optional[str] = None,
    category_id: Optional[int] = None,
    city: Optional[str] = None,
    mode: Optional[str] = None,
    level: Optional[str] = None,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    page: int = 1,
    page_size: int = 20,
) -> ApiResponse:
    """Search and filter published skill listings."""
    page_size = min(page_size, 50)
    offset = (page - 1) * page_size

    q = db.query(SkillListingModel).filter(SkillListingModel.status == "published")

    if query:
        search_term = f"%{query}%"
        q = q.filter(
            or_(
                SkillListingModel.title.ilike(search_term),
                SkillListingModel.description.ilike(search_term),
            )
        )

    if category_id:
        q = q.filter(SkillListingModel.category_id == category_id)

    if city:
        q = q.filter(SkillListingModel.city.ilike(f"%{city}%"))

    if mode:
        q = q.filter(SkillListingModel.teaching_mode == mode)

    if level:
        q = q.filter(SkillListingModel.level == level)

    if min_price is not None:
        q = q.filter(SkillListingModel.price_amount >= min_price)

    if max_price is not None:
        q = q.filter(SkillListingModel.price_amount <= max_price)

    listings = q.order_by(SkillListingModel.created_at.desc()).offset(offset).limit(page_size).all()

    data = []
    for listing in listings:
        teacher = db.query(UserModel).filter(UserModel.id == listing.teacher_id).first()
        category = db.query(CategoryModel).filter(CategoryModel.id == listing.category_id).first()
        data.append(SkillListingPublicSchema(
            id=listing.id,
            teacher_id=listing.teacher_id,
            teacher_name=teacher.name if teacher else "Unknown",
            category_id=listing.category_id,
            category_name=category.name if category else "Unknown",
            title=listing.title,
            description=listing.description,
            level=listing.level,
            price_amount=listing.price_amount,
            currency=listing.currency,
            price_unit=listing.price_unit,
            teaching_mode=listing.teaching_mode,
            city=listing.city,
            area=listing.area,
            status=listing.status,
        ).model_dump(mode="json"))

    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Search results fetched successfully",
        data=data,
    )


def get_teacher_skills(db: Session, user_id: int) -> ApiResponse:
    """List a teacher's published skills."""
    teacher = db.query(UserModel).filter(UserModel.id == user_id).first()
    if teacher is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found",
        )

    listings = (
        db.query(SkillListingModel)
        .filter(SkillListingModel.teacher_id == user_id, SkillListingModel.status == "published")
        .order_by(SkillListingModel.created_at.desc())
        .all()
    )

    data = []
    for listing in listings:
        category = db.query(CategoryModel).filter(CategoryModel.id == listing.category_id).first()
        data.append(SkillListingPublicSchema(
            id=listing.id,
            teacher_id=listing.teacher_id,
            teacher_name=teacher.name,
            category_id=listing.category_id,
            category_name=category.name if category else "Unknown",
            title=listing.title,
            description=listing.description,
            level=listing.level,
            price_amount=listing.price_amount,
            currency=listing.currency,
            price_unit=listing.price_unit,
            teaching_mode=listing.teaching_mode,
            city=listing.city,
            area=listing.area,
            status=listing.status,
        ).model_dump(mode="json"))

    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Teacher skills fetched successfully",
        data=data,
    )


def get_category_skills(db: Session, category_id: int) -> ApiResponse:
    """List published skills in a category."""
    category = (
        db.query(CategoryModel)
        .filter(CategoryModel.id == category_id, CategoryModel.is_active == True)  # noqa: E712
        .first()
    )
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    listings = (
        db.query(SkillListingModel)
        .filter(SkillListingModel.category_id == category_id, SkillListingModel.status == "published")
        .order_by(SkillListingModel.created_at.desc())
        .all()
    )

    data = []
    for listing in listings:
        teacher = db.query(UserModel).filter(UserModel.id == listing.teacher_id).first()
        data.append(SkillListingPublicSchema(
            id=listing.id,
            teacher_id=listing.teacher_id,
            teacher_name=teacher.name if teacher else "Unknown",
            category_id=listing.category_id,
            category_name=category.name,
            title=listing.title,
            description=listing.description,
            level=listing.level,
            price_amount=listing.price_amount,
            currency=listing.currency,
            price_unit=listing.price_unit,
            teaching_mode=listing.teaching_mode,
            city=listing.city,
            area=listing.area,
            status=listing.status,
        ).model_dump(mode="json"))

    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Category skills fetched successfully",
        data=data,
    )
