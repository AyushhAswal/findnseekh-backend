"""Shared fixtures for the FindNSeekh test suite.

Uses an in-memory SQLite database so tests run without a live PostgreSQL
server.  All tables are created fresh for each test and torn down afterwards.
"""
import sys
import os

# Ensure project root is on sys.path so `src.*` imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi import FastAPI, APIRouter, status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

# ---------------------------------------------------------------------------
# Import models to register their metadata with Base
# ---------------------------------------------------------------------------
from src.utils.db import Base, get_db  # noqa: F401

# Import all model modules so Alembic / metadata knows about every table
from src.users import models  # noqa: F401
from src.roles import models  # noqa: F401
from src.profile import models  # noqa: F401
from src.category import models  # noqa: F401
from src.skills import models  # noqa: F401
from src.requests import models  # noqa: F401

# ---------------------------------------------------------------------------
# SQLite file-based database for tests (in-memory doesn't work across threads)
# ---------------------------------------------------------------------------
import tempfile

_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False, prefix="findnseekh_test_")
_db_path = _db_file.name
_db_file.close()

sqlite_engine = create_engine(
    f"sqlite:///{_db_path}",
    connect_args={"check_same_thread": False},
)

event.listen(sqlite_engine, "connect", lambda conn, rec: conn.execute("PRAGMA foreign_keys=ON"))

TestingSessionLocal = sessionmaker(bind=sqlite_engine)


@pytest.fixture(autouse=True)
def _db_session():
    """Create all tables before a test and drop them afterwards."""
    Base.metadata.create_all(sqlite_engine)
    yield
    Base.metadata.drop_all(sqlite_engine)


def override_get_db():
    """Dependency override that yields a clean SQLite session per request."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Build a test-only FastAPI app (no lifespan, no PostgreSQL)
# ---------------------------------------------------------------------------
test_app = FastAPI(title="FindNSeekh Test API", version="1.0.0")

api_v1_router = APIRouter(prefix="/api/v1")


@api_v1_router.get("/", status_code=status.HTTP_200_OK)
def home():
    return {"message": "Welcome to FindNSeekh API", "status": "running"}


@api_v1_router.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "healthy"}


# Register feature routers
from src.users import routers as user_routers  # noqa: E402
from src.profile import routers as profile_routers  # noqa: E402
from src.category import routers as category_routers  # noqa: E402
from src.skills import routers as skills_routers  # noqa: E402
from src.requests import routers as request_routers  # noqa: E402

api_v1_router.include_router(user_routers.user_routes)
api_v1_router.include_router(profile_routers.profile_routes)
api_v1_router.include_router(category_routers.category_routes)
api_v1_router.include_router(skills_routers.skills_routes)
api_v1_router.include_router(request_routers.request_routes)

test_app.include_router(api_v1_router)
test_app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def db():
    """Return a raw database session for setup helpers."""
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def client():
    """Return a FastAPI TestClient bound to the test app."""
    with TestClient(test_app) as c:
        yield c
