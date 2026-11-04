# FastAPI Backend Pattern Blueprint

This document serves as a complete, precise, and reusable architecture blueprint for building FastAPI backends. It is designed to be fully readable by AI systems (and human developers) to replicate the exact folder structure, naming conventions, coding style, database interactions, and API design of the reference codebase.

---

## 1. Project Overview
* **Purpose:** This backend serves a social media application focused on user-generated memes, categories, tags, profile management, and AI meme generation.
* **Tech Stack:**
  * **FastAPI** (API routing, request validation, middleware, dependency injection)
  * **SQLAlchemy >= 2.0** (Sync ORM mapping, relationships, transactions)
  * **Pydantic >= 2** (Data serialization, schema validation, configuration settings)
  * **Pydantic-Settings** (Environment management)
  * **Alembic** (Database schema migrations)
  * **PyJWT** & **pwdlib[argon2]** (Authentication token parsing and password hashing)
  * **Uvicorn** (ASGI server runner)
  * **Supabase Python SDK / HTTP API Client** (File uploads, object storage)
  * **Groq SDK** & **OpenAI SDK** & **Replicate SDK** (AI generation utilities)
* **Entry Point:** The application is bootstrapped from `/main.py` at the root of the backend directory. This file builds the FastAPI application instance, registers routers, handles global lifespan events (such as directory setup and temporary file cleanup), and exposes the ASGI server app.

---

## 2. Directory Structure
The backend utilizes a modular, feature-based directory layout where all core application files live under the `src/` directory.

```
Pub_Meme_backend/
├── alembic/                      # Alembic migration configuration and scripts
│   ├── env.py                    # Migration environment and metadata imports
│   ├── script.py.mako            # Template for generating new migrations
│   └── versions/                 # Folder containing auto-generated migration history files
├── src/                          # Application source directory
│   ├── ai/                       # AI utilities, generation services, and endpoints
│   │   ├── controllers.py        # Controller logic mapping AI requests to API services
│   │   ├── dtos.py               # Request/Response schemas for AI operations
│   │   ├── routers.py            # AI router endpoint registrations
│   │   ├── services/             # Upstream API integrations
│   │   │   ├── groq_meme_service.py
│   │   │   ├── meme_service.py
│   │   │   ├── openai_caption_service.py
│   │   │   ├── openai_image_service.py
│   │   │   └── replicate_image_service.py
│   │   └── utils/                # Helper files for image processing and moderation
│   ├── category/                 # Category feature
│   │   ├── controllers.py        # Business logic for categories
│   │   ├── dtos.py               # Pydantic schemas for Category models
│   │   ├── models.py             # SQLAlchemy Category ORM model
│   │   └── routers.py            # Router mapping category REST endpoints
│   ├── posts/                    # Posts feature
│   │   ├── controllers.py
│   │   ├── dtos.py
│   │   ├── models.py
│   │   └── routers.py
│   ├── profile/                  # User profile feature
│   │   ├── controllers.py
│   │   ├── dtos.py
│   │   ├── models.py
│   │   └── routers.py
│   ├── tags/                     # Tags feature
│   │   ├── controllers.py
│   │   ├── dtos.py
│   │   ├── models.py
│   │   └── routers.py
│   ├── users/                    # User account & auth feature
│   │   ├── controllers.py
│   │   ├── dtos.py
│   │   ├── models.py
│   │   └── routers.py
│   └── utils/                    # Global utility functions and shared middleware
│       ├── auth.py               # Token creation, verification, and password hashing
│       ├── db.py                 # SQLAlchemy session setup and database dependency
│       ├── helpers.py            # Utility functions
│       ├── responses.py          # Unified standard JSON response envelope
│       ├── settings.py           # Pydantic-Settings environment loader
│       └── token_revocation.py   # JWT revocation validation
├── .env                          # Local environment variable configuration
├── alembic.ini                   # Alembic database target configuration
├── main.py                       # App factory and gateway bootstrapping file
└── requirements.txt              # Standard package requirements definition
```

---

## 3. Architectural Pattern
The application uses a **Feature-Driven Layered Architecture**. Instead of sorting code strictly by architectural concern globally (e.g., all controllers in one folder, all models in another), code is grouped by feature area, and layers exist inside each feature module:

```
[ HTTP Request ]
       │
       ▼
┌──────────────┐
│  Router      │  <-- Route definition, parameter binding, dependency extraction
└──────┬───────┘
       │  (Injects Session & Auth)
       ▼
┌──────────────┐
│  Controller  │  <-- Coordinates business operations, executes DB queries
└──────┬───────┘
       │  (SQLAlchemy Sessions)
       ▼
┌──────────────┐
│  Database    │  <-- Updates tables, commits transactions
└──────┬───────┘
       │  (ORM instances)
       ▼
┌──────────────┐
│  DTO Schema  │  <-- Maps ORM to validation schema (from_attributes=True)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  ApiResponse │  <-- Wraps and normalizes final standard JSON body
└──────────────┘
```

* **Data Flow Mechanics:**
  1. **Request:** The client hits an endpoint (e.g. `POST /tags`).
  2. **Router:** Validate payload formats using Pydantic DTO parameters. Inject the database session generator (`get_db`) and authorization dependencies via FastAPI `Depends()`.
  3. **Controller:** Perform business operations. Coordinate external service calls, check uniqueness constraints, interface with the DB via session queries, issue rollbacks on exception, and format data using target DTO classes.
  4. **Database (ORM Model):** Retrieve and save data. No separate Repository layer exists in the baseline codebase; the database query is written inside the controller function.
  5. **Response:** The data is serialized into Pydantic models and encapsulated inside a standard `ApiResponse` wrapper, returning a consistent JSON body back to the client.

---

## 4. Routing & Endpoint Conventions
* **Versioning:** All routes are defined in modular routers, grouped by prefix, and globally appended to the main FastAPI app context.
* **Naming Conventions:** Route prefixes and path components use lower-case `kebab-case` or `snake_case` (e.g., `/users/change-password`, `/posts/get-my-posts/{user_id}`).
* **APIRouter Registration:** Each feature module contains a `routers.py` file declaring an `APIRouter` with dedicated path prefixing and tags:
  ```python
  tag_routes = APIRouter(prefix="/tags", tags=["Tag"])
  ```
* **HTTP Method Mapping:**
  * `GET`: Fetch resources or query lists (e.g., `/tags`, `/tags/trending-tags`).
  * `POST`: Create new resources or perform actions requiring high payload confidentiality (e.g., `/tags`, `/users/login`, `/posts/{post_id}/like`).
  * `PUT`: Replace or update existing resources (e.g., `/tags/{tag_id}`, `/profile/update`).
  * `DELETE`: Remove resources (e.g., `/tags/{tag_id}`).

---

## 5. Models (SQLAlchemy / ORM)
* **Base Class:** All models inherit from a common `Base` instance imported from `src.utils.db`. This `Base` class is defined using SQLAlchemy's `declarative_base()`.
* **SQLAlchemy 2.0 Mapping Style:** Models use type annotations combined with `Mapped` and `mapped_column` to define constraints.
* **Table Naming:** Table names are explicitly declared using `__tablename__` and follow the singular `snake_case` suffix pattern with a `_table` postfix (e.g., `user_table`, `tag_table`, `post_table`).
* **Relationship Declarations:** Relationships are declared dynamically using `relationship()`, type-hinting target classes, and specifying `back_populates` and cascade parameters (e.g., `cascade="all, delete-orphan"`).
* **Common Timestamps:** Shared tables record audit trails (`created_at` and `updated_at`) mapping UTC server defaults via SQL function wrappers (`server_default=func.now()`).

---

## 6. Schemas (Pydantic / DTOs)
* **Filename:** Schemas are stored in `dtos.py` inside their respective feature module.
* **Schema Suffixes:** Schemas are categorized based on their roles:
  * `ResourceRegisterSchema` / `ResourceLoginSchema`: Specific schema models for user registration and authentication logic.
  * `ResourceCreateSchema`: Validation model used to construct new entries (strips whitespace, defines lengths).
  * `ResourceUpdateSchema`: Validation model used for editing existing entries.
  * `ResourceReadSchema`: Output serialization model containing database-assigned fields (`id`, `created_at`, `updated_at`).
* **ORM Compatibility:** Output/Read schemas must enable ORM conversion:
  ```python
  model_config = {"from_attributes": True}
  ```
* **Validation Guards:** Use `@field_validator` and `@model_validator` to implement logic checks (e.g., matching confirmation passwords, removing trailing whitespaces).

---

## 7. Services Layer
* **Baseline Controller Design:** For standard feature modules, the `controllers.py` file acts as the service layer. Controllers receive the database `Session` and Pydantic schema payloads from routers, run queries, handle transaction lifecycles (`commit`, `rollback`, `refresh`), and raise HTTP exceptions directly.
* **External Integrations:** Complex third-party integrations (e.g., OpenAI, Replicate, Groq) use dedicated helper wrappers in a `services/` directory under their feature folder (e.g., `src/ai/services/`). These service modules throw custom exceptions (e.g., `ImageGenerationError`), which are caught and converted into standard FastAPI `HTTPException` exceptions within the controller layer.

---

## 8. Repository / Database Layer
* **Direct Session Control:** To keep code straightforward and avoid over-engineering, standard queries are executed directly on the sync database session (`db.query()`, `db.execute()`) inside the feature's controller functions.
* **Database Connection Manager:** The `get_db()` dependency generator in `src/utils/db.py` initializes a sync connection using `sessionmaker(bind=engine)` and safely yields it, closing the session in a `finally` block:
  ```python
  def get_db():
      session = LocalSession()
      try:
          yield session
      finally:
          session.close()
  ```
* **ORM vs Raw Query:** Standard CRUD requests use ORM APIs (`db.query(UserModel)`). Specialized analytics queries (like listing tag counts over multi-table relations) utilize SQLAlchemy's programmatic select and SQL aggregation functions (`select`, `func.unnest`, `func.count`).

---

## 9. Dependency Injection (`Depends`)
* **Session Lifecycle Injection:** Endpoint paths inject database access using `db: Session = Depends(get_db)`.
* **Security Bearer Injections:** Protected endpoints intercept credentials using FastAPI's built-in `HTTPBearer` security wrapper:
  ```python
  security = HTTPBearer()
  credentials: HTTPAuthorizationCredentials = Depends(security)
  ```
* **No Global Dependency Bloat:** Common dependencies are kept granular and local to endpoint signatures rather than globally bound, making endpoint tests easier to mock.

---

## 10. Authentication & Authorization
* **JWT Authentication Strategy:** Standard JSON Web Tokens (JWT) are signed and verified using a configuration secret.
* **Token Content:** Token payloads contain a unique identifier (`_id` mapping to the user's primary key) and an expiration claim (`exp`). Expirations are validated automatically by the JWT library.
* **Route Protection Pattern:** Protected routes extract the bearer token string using the HTTP security helper, decode it, and assert the token has not been revoked (checking against a database revocation table).
  ```python
  # router.py
  @user_routes.post("/change-password")
  def change_password(body: ChangePasswordSchema, credentials = Depends(security), db = Depends(get_db)):
      token = credentials.credentials
      return controllers.change_password(db, token, body)
  
  # controllers.py / auth.py
  payload = require_active_session(token, db)
  user_id = payload.get("_id")
  ```
* **Password Hashing:** Passwords are encrypted using Argon2 via the `pwdlib` library before saving, and validated during logins using matching verification hooks.
* **Token Revocation (Logout):** When logging out, the token's SHA-256 hash is saved to the `revoked_token_table` along with its expiration date. Any subsequent validation check against that token hash will throw an unauthorized exception.

---

## 11. Error Handling
* **FastAPI Native Exceptions:** The application raises `HTTPException(status_code=..., detail=...)` directly from controller routines when errors are encountered.
* **Default Error Responses:** FastAPI automatically formats standard exceptions, raising them in the following layout:
  ```json
  {
    "detail": "Exception message or error details"
  }
  ```
* **Database Integrity Guards:** Operations susceptible to database constraints (e.g. unique email checks, concurrent updates) are wrapped in `try-except` blocks catching SQLAlchemy's `IntegrityError` to safely perform rollbacks and throw clean conflicts back to the user.

---

## 12. Configuration & Environment
* **Settings Engine:** Settings are loaded dynamically from environment files using Pydantic V2 Settings.
* **Configuration Definition:** Settings are defined in `src/utils/settings.py` inside a `Settings` class that inherits from `BaseSettings`.
* **Field Aliases:** Environment names can be mapped to multiple targets (e.g. using `AliasChoices` for mapping local `.env` values or production hosting fallbacks):
  ```python
  class Settings(BaseSettings):
      model_config = SettingsConfigDict(env_file=".env", extra="ignore")
      DB_CONNECTION: str
      SECRET_KEY: str
      ALGORITHM: str
      # ...
  ```
* **Singleton Export:** A single instance of this settings class is instantiated and shared across the application as a singleton import.

---

## 13. Database Migrations (Alembic)
* **Metadata Registration:** To support auto-generating migrations, all models must be imported in `alembic/env.py` to register them under `Base.metadata`:
  ```python
  from src.utils.db import Base
  import src.category.models
  import src.tags.models
  import src.posts.models
  import src.profile.models
  import src.users.models
  import src.utils.token_revocation
  ```
* **Database Target Binding:** The database URL option is set programmatically from the centralized configuration settings:
  ```python
  config.set_main_option("sqlalchemy.url", settings.DB_CONNECTION)
  ```
* **Auto-generation:** Migrations are created using command-line instructions specifying revision keys:
  ```bash
  alembic revision --autogenerate -m "description of migration"
  ```
* **Application Execution:** Apply pending migrations dynamically using the update command:
  ```bash
  alembic upgrade head
  ```

---

## 14. Middleware
* **Minimalist Approach:** The reference application relies on standard FastAPI settings. No custom middleware files or request logging filters are globally registered, ensuring low network processing overhead.
* **Temporary Resource Lifespan:** Temporary system contexts, like localized directories and cleanup of files generated during AI processes, are managed using FastAPI's standard startup/shutdown lifespan generator (`@asynccontextmanager`).

---

## 15. Code Style & Conventions
* **Language Rules:** Strictly type-hint all function signatures, parameters, and return types.
* **Function Naming:** Use `snake_case` named descriptively starting with action verbs (e.g., `create_tag`, `check_email_exists`).
* **Class Naming:** Use `PascalCase` with specific suffix indicators:
  * Database Models: Ends in `Model` (e.g., `UserModel`, `TagModel`).
  * DTO Schemas: Ends in `Schema` (e.g., `UserRegisterSchema`, `TagReadSchema`).
* **Import Grouping:** Standard packages go first, followed by third-party imports, and finally internal application modules (from `src.{feature}`).
* **Response Wrapper:** Every JSON body returned to the client on success must be wrapped in `ApiResponse`.

---

## 16. AI-Replication Instructions
When writing a new FastAPI project based on this pattern, the AI must strictly adhere to the following rules:

1. **Modular Directory Architecture:** Every feature must reside in a separate directory under `src/` containing at least `routers.py`, `controllers.py`, `dtos.py`, and `models.py` (if the feature has database mappings).
2. **Sync Database Connectivity:** Connect to the database using sync SQLAlchemy connections, managing sessions via a generator dependency `Depends(get_db)`.
3. **ORM Declarations:** Models must use SQLAlchemy 2.0 type mapping conventions (`Mapped[type] = mapped_column()`) and declare explicit singular table names suffixed with `_table`.
4. **Pydantic Serialization Suffixes:** Pydantic DTO definitions must reside in `dtos.py`, follow the `Schema` class name suffix convention, and enable read serialization using `model_config = {"from_attributes": True}`.
5. **No Direct JSON Dumps:** Endpoints must map data to Pydantic objects first and return them inside the standard `ApiResponse` envelope.
6. **No Implicit Decodes:** Use the `HTTPBearer` authorization dependency. protected endpoints must receive the token string, decode user details, and assert that the token hasn't been revoked.
7. **Lifespan Cleanup Rules:** Define transient folders and execute automated maintenance operations inside an async lifespan context manager.
8. **Alembic Imports Mapping:** Whenever a model is created, its module must be explicitly imported inside `alembic/env.py` to ensure it is registered on the metadata catalog for schema generation.

---

## 17. Full Code Examples (Critical Section)
The following code snippets present the complete, copy-pasteable layout of a standard CRUD feature (in this case, "Tags") to show the exact pattern.

### ✅ A Complete Endpoint File
*File path: `/src/tags/routers.py`*
```python
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

# Import controller actions containing the core business/DB queries
from src.tags import controllers
# Import strict data contract schemas for payload validation
from src.tags.dtos import TagCreateSchema, TagUpdateSchema
# Inject database connection session dependency
from src.utils.db import get_db

# Initialize the router with clean prefixes and tag groups
tag_routes = APIRouter(prefix="/tags", tags=["Tag"])


@tag_routes.post("", status_code=status.HTTP_201_CREATED)
def create_tag(body: TagCreateSchema, db: Session = Depends(get_db)):
    """Create a new tag. Input validated by TagCreateSchema."""
    return controllers.create_tag(db, body)


@tag_routes.get("", status_code=status.HTTP_200_OK)
def get_tags(db: Session = Depends(get_db)):
    """Fetch all tags sorted alphabetically by name."""
    return controllers.list_tags(db)


@tag_routes.put("/{tag_id}", status_code=status.HTTP_200_OK)
def edit_tag(
    tag_id: int,
    body: TagUpdateSchema,
    db: Session = Depends(get_db),
):
    """Edit an existing tag's name. Path is validated via query arguments."""
    return controllers.update_tag(db, tag_id, body)


@tag_routes.delete("/{tag_id}", status_code=status.HTTP_200_OK)
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    """Delete a tag using its primary ID path identifier."""
    return controllers.delete_tag(db, tag_id)


@tag_routes.get('/trending-tags', status_code=status.HTTP_200_OK)
def get_trending_tags(
    limit: int = Query(20, ge=1, le=100, alias="limit"), 
    db: Session = Depends(get_db)
):
    """Fetch tags ordered by usage frequency count across posts."""
    return controllers.get_trending_tags(db, limit)
```

### ✅ A Complete Model File
*File path: `/src/tags/models.py`*
```python
from datetime import datetime
from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

# Import Base ORM meta descriptor class
from src.utils.db import Base


class TagModel(Base):
    """SQLAlchemy model representing the tag_table schema mapping."""
    
    # Explicit table naming with suffix format
    __tablename__ = "tag_table"

    # Strict type hints mapping auto-incrementing primary integer keys
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Core string constraint mappings including indexes and unique checks
    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)

    # Automated transaction audit logs using SQL native defaults
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
```

### ✅ A Complete Schema File (All Variants)
*File path: `/src/tags/dtos.py`*
```python
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class TagCreateSchema(BaseModel):
    """Validation schema used on resource creation endpoints."""
    name: str = Field(min_length=1, max_length=64)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        """Strip trailing whitespaces and assert tag name is not blank."""
        s = v.strip()
        if not s:
            raise ValueError("Tag name cannot be blank")
        return s


class TagUpdateSchema(BaseModel):
    """Validation schema used on edit resource endpoints."""
    name: str = Field(min_length=1, max_length=64)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        """Ensure updated name values are sanitized and not blank."""
        s = v.strip()
        if not s:
            raise ValueError("Tag name cannot be blank")
        return s


class TagReadSchema(BaseModel):
    """Output serialization schema representing retrieved database rows."""
    id: int
    name: str
    created_at: datetime
    updated_at: datetime

    # Enable direct conversion mapping from SQLAlchemy ORM entities
    model_config = {"from_attributes": True}


class TrendingTagSchema(BaseModel):
    """Custom view schema returning tag aggregation counts."""
    name: str
    usage_count: int
```

### ✅ A Complete Service / Controller File
*File path: `/src/tags/controllers.py`*
```python
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

# Import post models for unnesting join collections
from src.posts.models import PostModel
# Import feature schemas for request mappings
from src.tags.dtos import (
    TagCreateSchema,
    TagReadSchema,
    TagUpdateSchema,
    TrendingTagSchema,
)
# Import target database entity model class
from src.tags.models import TagModel
# Import standardized standard response envelope wrapper
from src.utils.responses import ApiResponse


def create_tag(db: Session, body: TagCreateSchema) -> ApiResponse:
    """Business transaction orchestrating new tag validation and database storage."""
    tag = TagModel(name=body.name)
    db.add(tag)
    try:
        # Commit to verify uniqueness constraints
        db.commit()
    except IntegrityError:
        # Rollback active transaction state on duplicate name conflicts
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tag with this name already exists",
        )

    db.refresh(tag)
    return ApiResponse(
        status=status.HTTP_201_CREATED,
        message="Tag created successfully",
        data=TagReadSchema.model_validate(tag).model_dump(mode="json"),
    )


def list_tags(db: Session) -> ApiResponse:
    """Fetch and return list of all tags alphabetically sorted."""
    rows = db.query(TagModel).order_by(TagModel.name.asc()).all()
    # Serialize collections safely using model validation wrappers
    data = [TagReadSchema.model_validate(r).model_dump(mode="json") for r in rows]
    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Tags fetched successfully",
        data=data,
    )


def update_tag(db: Session, tag_id: int, body: TagUpdateSchema) -> ApiResponse:
    """Edit resource properties in a transaction."""
    tag = db.query(TagModel).filter(TagModel.id == tag_id).first()
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    tag.name = body.name
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tag with this name already exists",
        )

    db.refresh(tag)
    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Tag updated successfully",
        data=TagReadSchema.model_validate(tag).model_dump(mode="json"),
    )


def delete_tag(db: Session, tag_id: int) -> ApiResponse:
    """Delete a database tag entity."""
    tag = db.query(TagModel).filter(TagModel.id == tag_id).first()
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    payload = TagReadSchema.model_validate(tag).model_dump(mode="json")
    db.delete(tag)
    db.commit()
    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Tag deleted successfully",
        data=payload,
    )


def get_trending_tags(db: Session, limit: int) -> ApiResponse:
    """Execute specialized aggregation query on unnested tag array collections."""
    # Subquery representing tags unnested from a standard string array column
    unnested = (
        select(
            func.unnest(PostModel.tags).label("tag"),
            PostModel.id.label("post_id"),
        )
        .select_from(PostModel)
        .where(func.cardinality(PostModel.tags) > 0)
        .subquery()
    )

    tag_key = func.lower(unnested.c.tag)

    rows = db.execute(
        select(
            func.max(unnested.c.tag).label("name"),
            func.count(unnested.c.post_id).label("usage_count"),
        )
        .group_by(tag_key)
        .order_by(func.count(unnested.c.post_id).desc())
        .limit(limit)
    ).all()

    data = [
        TrendingTagSchema(name=name, usage_count=usage_count).model_dump(mode="json")
        for name, usage_count in rows
    ]

    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Trending tags fetched successfully",
        data=data,
    )
```

### ✅ A Complete Repository File (Alternative Architecture Blueprint)
*File path: `/src/tags/repositories.py` (Mocked extension showing how to apply Repository layer if desired)*
```python
from typing import Sequence
from sqlalchemy.orm import Session
from src.tags.models import TagModel


class TagRepository:
    """
    Optional repository class encapsulating raw database access for tags.
    Injected into Controllers to decouple DB operations from orchestration logic.
    """
    
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, tag_id: int) -> TagModel | None:
        """Find a single tag model matching the primary identifier ID."""
        return self.db.query(TagModel).filter(TagModel.id == tag_id).first()

    def get_by_name(self, name: str) -> TagModel | None:
        """Find a tag matching the target name column exactly."""
        return self.db.query(TagModel).filter(TagModel.name == name).first()

    def list_all_alphabetical(self) -> Sequence[TagModel]:
        """Fetch all database rows alphabetically sorted by name."""
        return self.db.query(TagModel).order_by(TagModel.name.asc()).all()

    def save(self, tag: TagModel) -> TagModel:
        """Save new entity properties or persist updates to the database."""
        self.db.add(tag)
        self.db.flush()  # Populates model ID fields inside active transaction boundaries
        return tag

    def delete(self, tag: TagModel) -> None:
        """Remove model references from active context scopes."""
        self.db.delete(tag)
```

### ✅ A Dependency File
*File path: `/src/utils/db.py`*
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.utils.settings import settings

# Base class instance that all entity models must inherit
Base = declarative_base()

# Sync SQLAlchemy connection pool engine setup
engine = create_engine(url=settings.DB_CONNECTION)

# Session factory for starting local database transaction contexts
LocalSession = sessionmaker(bind=engine)


def get_db():
    """
    Generator function serving database sessions via FastAPI Depends injection.
    Automatically releases connection references in a finally block.
    """
    session = LocalSession()
    try:
        yield session
    finally:
        session.close()


---

## 15. API Caching Optimization (lastUpdated Pattern)

To optimize mobile/frontend data syncing, the backend implements a timestamp-based validation pattern using a `lastUpdated` query parameter. This allows the client to perform lightweight checks without pulling the entire dataset.

### Mechanics & Flow:
1. **Frontend Query:** The mobile app calls a GET API including a `lastUpdated` parameter containing the client's local cache timestamp.
2. **Backend Fetch:** The controller queries the maximum modification or creation timestamp of the corresponding model for that resource.
3. **Optimized Cache Hit:** If the client's `lastUpdated` matches the database's maximum timestamp, the API skips database retrieval, serialization, and network payload overhead, returning `data: null` inside the `ApiResponse` wrapper.
4. **Cache Miss / Fresh Load:** If `lastUpdated` is absent or does not match, the controller queries the full dataset, serializes the response, and includes the new `lastUpdated` timestamp in the response envelope.

### Controller Implementation Template:
```python
from sqlalchemy import func
from typing import Optional
from src.utils.responses import ApiResponse
from src.utils.auth import require_active_session

def get_resources_last_updated(user_id: int, db: Session) -> Optional[datetime]:
    """Retrieve the maximum updated_at / created_at timestamp for a resource."""
    return db.query(func.max(ResourceModel.updated_at)).filter(
        ResourceModel.user_id == user_id
    ).scalar()

def get_resources(db: Session, token: str, lastUpdated: Optional[str] = None) -> ApiResponse:
    """Fetch resources with optimized timestamp caching verification."""
    payload = require_active_session(token, db)
    user_id = payload.get("_id")
    
    # 1. Retrieve the latest update timestamp from the database
    db_last_updated = get_resources_last_updated(user_id, db)
    
    # 2. Check for cache hits
    if lastUpdated is not None:
        # If client timestamp matches the database, return data: null
        return ApiResponse(
            status=status.HTTP_200_OK,
            message="Resources last updated timestamp fetched successfully",
            data=None,
            lastUpdated=db_last_updated,
        )
        
    # 3. Cache miss: fetch and serialize the complete dataset
    rows = db.query(ResourceModel).filter(ResourceModel.user_id == user_id).all()
    data = [ResourceReadSchema.model_validate(r).model_dump(mode="json") for r in rows]
    
    return ApiResponse(
        status=status.HTTP_200_OK,
        message="Resources fetched successfully",
        data=data,
        lastUpdated=db_last_updated,
    )
```

### Router Implementation Template:
```python
@routes.get("/resources", status_code=status.HTTP_200_OK)
def list_resources(
    lastUpdated: Optional[str] = Query(None),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Retrieve resources, delegating caching logic to the controller."""
    token = credentials.credentials
    return controllers.get_resources(db, token, lastUpdated)
```

```
