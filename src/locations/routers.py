from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.locations import controllers
from src.utils.db import get_db

locations_routes = APIRouter(prefix="/locations", tags=["Locations"])


@locations_routes.get("/suggestions", status_code=status.HTTP_200_OK)
def get_location_suggestions(
    query: Optional[str] = Query(None, alias="q"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Get location suggestions for search dropdown."""
    return controllers.get_location_suggestions(db, query, limit)

