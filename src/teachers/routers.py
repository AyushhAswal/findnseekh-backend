from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.teachers import controllers
from src.utils.db import get_db

teachers_routes = APIRouter(prefix="/teachers", tags=["Teachers"])


@teachers_routes.get("/featured", status_code=status.HTTP_200_OK)
def get_featured_teachers(
    limit: int = Query(6, ge=1, le=20),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Get featured teachers for home page and category highlights."""
    return controllers.get_featured_teachers(db, limit, category)


@teachers_routes.get("", status_code=status.HTTP_200_OK)
def list_teachers(
    q: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    city: Optional[str] = Query(None),
    mode: Optional[str] = Query(None),
    min_exp: Optional[int] = Query(None),
    sort: Optional[str] = Query("recommended"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """List teachers with filtering, search and pagination."""
    return controllers.list_teachers(
        db, q, category, category_id, city, mode, min_exp, sort, page, page_size
    )


@teachers_routes.get("/{user_id}", status_code=status.HTTP_200_OK)
def get_teacher_detail(
    user_id: int,
    db: Session = Depends(get_db),
):
    """Get public teacher detail by user ID."""
    return controllers.get_teacher_detail(db, user_id)

