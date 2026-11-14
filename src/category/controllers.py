from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.category.dtos import CategoryReadSchema
from src.category.models import CategoryModel
from src.utils.helpers import generate_slug
from src.utils.responses import ApiResponse


def list_categories(db: Session) -> ApiResponse:
    """Fetch all active categories sorted alphabetically."""
    rows = (
        db.query(CategoryModel)
        .filter(CategoryModel.is_active == True)  # noqa: E712
        .order_by(CategoryModel.name.asc())
        .all()
    )
    data = [CategoryReadSchema.model_validate(r).model_dump(mode="json") for r in rows]
    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Categories fetched successfully",
        data=data,
    )


def get_category(db: Session, category_id: int) -> ApiResponse:
    """Get a single category by ID."""
    category = db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Category fetched successfully",
        data=CategoryReadSchema.model_validate(category).model_dump(mode="json"),
    )


def seed_categories(db: Session) -> None:
    """Seed initial categories if they don't exist."""
    initial_categories = [
        ("Music", "music"),
        ("Dance", "dance"),
        ("Photography", "photography"),
        ("Art & Craft", "art-craft"),
        ("Fitness & Yoga", "fitness-yoga"),
        ("Cooking", "cooking"),
        ("Technology", "technology"),
        ("Languages", "languages"),
        ("Academic Tuition", "academic-tuition"),
        ("Design", "design"),
        ("Professional Skills", "professional-skills"),
    ]
    for name, slug in initial_categories:
        existing = (
            db.query(CategoryModel)
            .filter(CategoryModel.name == name)
            .first()
        )
        if existing is None:
            category = CategoryModel(name=name, slug=slug)
            db.add(category)
    db.commit()
