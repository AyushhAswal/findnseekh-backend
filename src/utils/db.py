from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from src.utils.settings import settings

# Base class instance that all entity models must inherit
Base = declarative_base()

# Lazy engine creation — avoids connecting at import time (important for tests)
_engine = None
_LocalSession = None


def get_engine():
    """Return the SQLAlchemy engine, creating it lazily on first call."""
    global _engine
    if _engine is None:
        _engine = create_engine(url=settings.DB_CONNECTION)
    return _engine


def get_session():
    """Return the session factory, creating it lazily on first call."""
    global _LocalSession
    if _LocalSession is None:
        _LocalSession = sessionmaker(bind=get_engine())
    return _LocalSession


# Keep backwards-compatible aliases
engine = None  # Not used at module level; use get_engine() instead
LocalSession = None  # Not used at module level; use get_session() instead


def get_db():
    """
    Generator function serving database sessions via FastAPI Depends injection.
    Automatically releases connection references in a finally block.
    """
    session = get_session()()
    try:
        yield session
    finally:
        session.close()
