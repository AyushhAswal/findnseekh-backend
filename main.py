from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter
from fastapi import status

from src.utils.db import get_session
from src.category.controllers import seed_categories
from src.roles.models import RoleModel


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Seed initial data on startup."""
    db = get_session()()
    try:
        seed_categories(db)
        # Seed initial roles if they don't exist
        for role_name in ("student", "teacher"):
            existing = db.query(RoleModel).filter(RoleModel.name == role_name).first()
            if existing is None:
                db.add(RoleModel(name=role_name))
            db.commit()
    finally:
        db.close()
    yield


app = FastAPI(
    title="FindNSeekh API",
    description="Skill Sharing and Learning Platform",
    version="1.0.0",
    lifespan=lifespan,
)

from src.utils.etag import ETagMiddleware
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["ETag", "Cache-Control"],
)
app.add_middleware(ETagMiddleware)


# API v1 router prefix
api_v1_router = APIRouter(prefix="/api/v1")


@api_v1_router.get("/", status_code=status.HTTP_200_OK)
def home():
    return {"message": "Welcome to FindNSeekh API", "status": "running"}


@api_v1_router.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "healthy"}


# Register feature routers here
from src.users import routers as user_routers
from src.profile import routers as profile_routers
from src.category import routers as category_routers
from src.skills import routers as skills_routers
from src.requests import routers as request_routers
from src.teachers import routers as teacher_routers
from src.locations import routers as location_routers
from src.home import routers as home_routers

api_v1_router.include_router(user_routers.user_routes)
api_v1_router.include_router(profile_routers.profile_routes)
api_v1_router.include_router(category_routers.category_routes)
api_v1_router.include_router(skills_routers.skills_routes)
api_v1_router.include_router(request_routers.request_routes)
api_v1_router.include_router(teacher_routers.teachers_routes)
api_v1_router.include_router(location_routers.locations_routes)
api_v1_router.include_router(home_routers.home_routes)


app.include_router(api_v1_router)
