from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.home import controllers
from src.utils.db import get_db

home_routes = APIRouter(prefix="/home", tags=["Home"])


@home_routes.get("/overview", status_code=status.HTTP_200_OK)
def get_home_overview(db: Session = Depends(get_db)):
    """Fetch complete aggregated home page data with ETag support."""
    return controllers.get_home_overview(db)

