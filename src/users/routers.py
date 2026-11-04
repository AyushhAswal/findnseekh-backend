from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.users import controllers
from src.users.dtos import UpdateUserSchema, UserLoginSchema, UserRegisterSchema
from src.utils.db import get_db

security = HTTPBearer()
user_routes = APIRouter(prefix="/users", tags=["User"])


@user_routes.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: UserRegisterSchema, db: Session = Depends(get_db)):
    """Register a new user and assign the default student role."""
    return controllers.register_user(db, body)


@user_routes.post("/login", status_code=status.HTTP_200_OK)
def login(body: UserLoginSchema, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""
    return controllers.login_user(db, body)


@user_routes.get("/me", status_code=status.HTTP_200_OK)
def get_me(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Get current authenticated user profile with roles."""
    token = credentials.credentials
    return controllers.get_current_user(db, token)


@user_routes.put("/me", status_code=status.HTTP_200_OK)
def update_me(
    body: UpdateUserSchema,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Update current authenticated user profile fields."""
    token = credentials.credentials
    return controllers.update_current_user(db, token, body)


@user_routes.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Revoke current token and log out."""
    token = credentials.credentials
    return controllers.logout_user(db, token)


@user_routes.post("/become-teacher", status_code=status.HTTP_201_CREATED)
def become_teacher(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Activate teacher role and create teacher profile atomically."""
    token = credentials.credentials
    return controllers.become_teacher(db, token)
