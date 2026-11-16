from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.teachers import controllers
from src.teachers.dtos import TeacherEnquiryCreateSchema
from src.utils.db import get_db

security = HTTPBearer(auto_error=False)
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
    min_price: Optional[Decimal] = Query(None),
    max_price: Optional[Decimal] = Query(None),
    min_rating: Optional[float] = Query(None),
    sort: Optional[str] = Query("recommended"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """List teachers with filtering, search, sorting and pagination."""
    return controllers.list_teachers(
        db=db,
        q=q,
        category=category,
        category_id=category_id,
        city=city,
        mode=mode,
        min_exp=min_exp,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        sort=sort,
        page=page,
        page_size=page_size,
    )


@teachers_routes.get("/{user_id}", status_code=status.HTTP_200_OK)
def get_teacher_detail(
    user_id: int,
    db: Session = Depends(get_db),
):
    """Get public teacher detail by user ID."""
    return controllers.get_teacher_detail(db, user_id)


@teachers_routes.post("/{user_id}/enquiry", status_code=status.HTTP_201_CREATED)
def send_teacher_enquiry(
    user_id: int,
    body: TeacherEnquiryCreateSchema,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
):
    """Send an enquiry or lesson request to a teacher."""
    token = credentials.credentials if credentials else None
    return controllers.send_teacher_enquiry(db, user_id, body, token)


