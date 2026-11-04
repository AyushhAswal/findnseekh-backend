from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.skills import controllers
from src.skills.dtos import (
    SkillListingCreateSchema,
    SkillListingStatusSchema,
    SkillListingUpdateSchema,
)
from src.utils.db import get_db

security = HTTPBearer()
skills_routes = APIRouter(prefix="/skills", tags=["Skill Listing"])


@skills_routes.post("", status_code=status.HTTP_201_CREATED)
def create_skill(
    body: SkillListingCreateSchema,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Create a new skill listing (teacher only)."""
    token = credentials.credentials
    return controllers.create_skill_listing(db, token, body)


@skills_routes.get("", status_code=status.HTTP_200_OK)
def list_skills(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Browse published skill listings."""
    return controllers.list_skill_listings(db, page, page_size)


# Static routes must come before /{skill_id} to avoid path parameter conflicts

@skills_routes.get("/search", status_code=status.HTTP_200_OK)
def search_skills(
    query: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    city: Optional[str] = Query(None),
    mode: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    min_price: Optional[Decimal] = Query(None),
    max_price: Optional[Decimal] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Search and filter published skill listings."""
    return controllers.search_skill_listings(
        db, query, category_id, city, mode, level, min_price, max_price, page, page_size
    )


@skills_routes.get("/my-skills", status_code=status.HTTP_200_OK)
def get_my_skills(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Get current teacher's skill listings."""
    token = credentials.credentials
    return controllers.get_my_skill_listings(db, token)


@skills_routes.get("/teachers/{user_id}", status_code=status.HTTP_200_OK)
def get_teacher_skills(user_id: int, db: Session = Depends(get_db)):
    """List a teacher's published skills."""
    return controllers.get_teacher_skills(db, user_id)


@skills_routes.get("/categories/{category_id}", status_code=status.HTTP_200_OK)
def get_category_skills(category_id: int, db: Session = Depends(get_db)):
    """List published skills in a category."""
    return controllers.get_category_skills(db, category_id)


@skills_routes.get("/{skill_id}", status_code=status.HTTP_200_OK)
def get_skill(skill_id: int, db: Session = Depends(get_db)):
    """Get a single skill listing."""
    return controllers.get_skill_listing(db, skill_id)


@skills_routes.put("/{skill_id}", status_code=status.HTTP_200_OK)
def update_skill(
    skill_id: int,
    body: SkillListingUpdateSchema,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Update own skill listing."""
    token = credentials.credentials
    return controllers.update_skill_listing(db, token, skill_id, body)


@skills_routes.delete("/{skill_id}", status_code=status.HTTP_200_OK)
def archive_skill(
    skill_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Archive own skill listing."""
    token = credentials.credentials
    return controllers.archive_skill_listing(db, token, skill_id)


@skills_routes.patch("/{skill_id}/status", status_code=status.HTTP_200_OK)
def update_status(
    skill_id: int,
    body: SkillListingStatusSchema,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Update listing status (publish, pause, archive)."""
    token = credentials.credentials
    return controllers.update_skill_listing_status(db, token, skill_id, body)
