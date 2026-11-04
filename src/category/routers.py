from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.category import controllers
from src.utils.db import get_db

category_routes = APIRouter(prefix="/categories", tags=["Category"])


@category_routes.get("", status_code=status.HTTP_200_OK)
def list_categories(db: Session = Depends(get_db)):
    """List all active categories."""
    return controllers.list_categories(db)


@category_routes.get("/{category_id}", status_code=status.HTTP_200_OK)
def get_category(category_id: int, db: Session = Depends(get_db)):
    """Get category details by ID."""
    return controllers.get_category(db, category_id)
