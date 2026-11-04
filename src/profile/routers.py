from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.profile import controllers
from src.profile.dtos import (
    TeacherProfileCreateSchema,
    TeacherProfileUpdateSchema,
)
from src.utils.db import get_db

security = HTTPBearer()
profile_routes = APIRouter(prefix="/profile/teacher", tags=["Teacher Profile"])


@profile_routes.post("", status_code=status.HTTP_201_CREATED)
def create_profile(
    body: TeacherProfileCreateSchema,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Create own teacher profile if not created during onboarding."""
    token = credentials.credentials
    return controllers.create_teacher_profile(db, token, body)


@profile_routes.get("/me", status_code=status.HTTP_200_OK)
def get_my_profile(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Get own teacher profile."""
    token = credentials.credentials
    return controllers.get_my_teacher_profile(db, token)


@profile_routes.put("/me", status_code=status.HTTP_200_OK)
def update_my_profile(
    body: TeacherProfileUpdateSchema,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Update own teacher profile."""
    token = credentials.credentials
    return controllers.update_my_teacher_profile(db, token, body)


@profile_routes.get("/{user_id}", status_code=status.HTTP_200_OK)
def get_public_profile(
    user_id: int,
    db: Session = Depends(get_db),
):
    """View public teacher profile."""
    return controllers.get_teacher_public_profile(db, user_id)
