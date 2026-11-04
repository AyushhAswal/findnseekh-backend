# FindNSeekh Backend --- Project Implementation Instructions

> **Purpose:** Keep this file in the FindNSeekh backend repository as
> `FINDNSEEKH_BACKEND_GUIDE.md`. Every developer or AI coding assistant
> must read it before creating or changing APIs, models, schemas,
> controllers, or migrations.

## 1. Required reference documents

FindNSeekh uses two complementary references:

1.  **`FastAPI_Backend_Pattern.md` --- architecture and coding-pattern
    reference.** It defines the FastAPI folder structure, feature-driven
    layers, naming conventions, synchronous SQLAlchemy sessions,
    Pydantic v2 DTOs, `ApiResponse`, JWT/HTTPBearer authentication,
    Argon2 password hashing, error handling, settings, Alembic
    integration, and coding style. Treat it as the source of truth for
    **how code is structured and implemented**.
2.  **`FindNSeekh_Backend_Architecture_Blueprint.pdf` --- product and
    domain reference.** It defines FindNSeekh's marketplace requirements,
    roles, database entities, relationships, API inventory, workflows,
    permissions, validation rules, and MVP scope. Treat it as the source
    of truth for **what the product must do**.

### Conflict resolution

-   For folder structure, file naming, coding style, SQLAlchemy usage,
    DTO style, response formatting, authentication implementation and
    migrations, follow `FastAPI_Backend_Pattern.md`.
-   For FindNSeekh features, tables, business rules, endpoint purposes,
    request lifecycle and MVP boundaries, follow
    `FindNSeekh_Backend_Architecture_Blueprint.pdf`.
-   Implement FindNSeekh requirements using the architecture pattern; do
    not copy the reference app's meme-specific features.
-   If the documents conflict in a way that changes a database or API
    contract, security rule or product behavior, explain the conflict
    and ask for approval. Do not silently choose.
-   Do not invent unrelated features or endpoints.

## 2. Product definition and MVP decisions

FindNSeekh is a two-sided skill-sharing marketplace: teachers publish
skills they can teach; learners discover skills and send learning
requests.

Core flow:

`Register → activate teacher capability (optional) → publish skill → discover skill → send learning request → teacher accepts/rejects`

Unless explicitly changed by the product owner:

-   One account can have both `student` and `teacher` roles.
-   New users receive the `student` role by default.
-   A user activates teacher capability through teacher onboarding.
-   Online and offline teaching are supported.
-   Learning requests are the initial connection mechanism.
-   Listings may be free or paid. Paid listings must specify currency
    and price unit.
-   Payments, live video, in-app chat, subscriptions, AI recommendations
    and complex calendar booking are outside the initial MVP.
-   Do not expose private phone numbers or exact residential addresses
    publicly.
-   Enable reviews only after a trustworthy completed-learning/session
    workflow exists. An accepted request does not prove a lesson was
    completed.

## 3. Required technology and implementation pattern

Use this stack unless the product owner approves a change:

-   Python, FastAPI, Uvicorn
-   SQLAlchemy 2.0 using the **synchronous ORM/session pattern**
-   PostgreSQL
-   Pydantic v2 and `pydantic-settings`
-   Alembic
-   PyJWT
-   `pwdlib[argon2]`

Follow `FastAPI_Backend_Pattern.md`:

-   Feature-driven modules live under `src/`.
-   A feature generally contains `routers.py`, `controllers.py`,
    `dtos.py`, and `models.py` where applicable.
-   Routers define endpoints, bind parameters, validate DTOs and inject
    dependencies.
-   Controllers contain business logic, DB queries, ownership/role
    checks, transaction handling and `ApiResponse` construction.
-   DTOs contain request/response contracts and validation.
-   Models contain SQLAlchemy mappings and relationships.
-   Do not add a repository layer by default; ordinary queries belong in
    controllers.
-   Use strict type hints and descriptive `snake_case` functions.
-   ORM classes use `PascalCase` and end in `Model`; DTO classes end in
    `Schema`.
-   Use SQLAlchemy 2.0 `Mapped[...]` and `mapped_column(...)`.
-   Read DTOs use `model_config = {"from_attributes": True}`.
-   Successful API responses use the existing `ApiResponse` wrapper.
-   Use `Depends(get_db)` for synchronous DB sessions.
-   Use `HTTPBearer` for protected routes.
-   Handle transaction failures with rollback; handle uniqueness
    conflicts such as `IntegrityError`.
-   Use UTC `created_at` and `updated_at` timestamps.
-   Register every ORM model module in `alembic/env.py`.

## 4. Recommended project structure

``` text
findnseekh-backend/
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── src/
│   ├── users/
│   │   ├── routers.py
│   │   ├── controllers.py
│   │   ├── dtos.py
│   │   └── models.py
│   ├── roles/
│   │   ├── routers.py
│   │   ├── controllers.py
│   │   ├── dtos.py
│   │   └── models.py
│   ├── profile/
│   ├── category/
│   ├── skills/
│   ├── requests/
│   ├── reviews/
│   └── utils/
│       ├── auth.py
│       ├── db.py
│       ├── responses.py
│       ├── settings.py
│       └── helpers.py
├── .env
├── .env.example
├── .gitignore
├── alembic.ini
├── main.py
└── requirements.txt
```

Notes: - `roles/` can be a separate module or be implemented within
`users/` if that better matches the existing repository; the role tables
and multi-role behavior remain required. - `profile/` owns
teacher-profile APIs. - `requests/` means learning requests. -
Root-level `main.py` is the application entry point. - Inspect the
actual repository before creating files; do not duplicate existing
infrastructure.

## 5. Database design contract

Use PostgreSQL relational tables, foreign keys, indexes, unique
constraints and check constraints. Table names use singular `snake_case`
plus `_table`, matching the architecture reference.

### 5.1 `user_table`

Account identity and private authentication data:

-   `id`: primary key.
-   `name`: required display name.
-   `email`: required, unique, normalized to lowercase.
-   `password_hash`: required Argon2 hash; never store plaintext.
-   `phone`: optional; do not expose publicly by default.
-   `is_active`: boolean, default true.
-   `is_email_verified`: boolean, default false.
-   `created_at`, `updated_at`: UTC timestamps.

### 5.2 `role_table`

-   `id`: primary key.
-   `name`: unique role name; initially `student` and `teacher`.
-   `created_at`: timestamp.

### 5.3 `user_role_table`

Many-to-many user/role mapping:

-   `id`: primary key.
-   `user_id`: FK to `user_table.id`.
-   `role_id`: FK to `role_table.id`.
-   `created_at`: timestamp.
-   Unique constraint on `(user_id, role_id)`.

**Reason:** one person can teach and learn using the same account. Do
not use a single mutually exclusive role column on `user_table`.

### 5.4 `teacher_profile_table`

One optional public teaching profile per teacher:

-   `id`: primary key.
-   `user_id`: FK to `user_table.id`, unique.
-   `bio`: optional text.
-   `experience_years`: non-negative integer, default 0.
-   `city`, `state`: optional location fields.
-   `teaching_mode`: `online`, `offline`, or `both`.
-   `is_verified`: boolean, default false; do not claim verification
    without a real process.
-   `created_at`, `updated_at`.

### 5.5 `category_table`

-   `id`: primary key.
-   `name`: unique, required.
-   `slug`: unique, required.
-   `description`: optional.
-   `is_active`: boolean, default true.
-   `created_at`, `updated_at`.

Initial categories may include Technology, Academic Tuition, Music,
Design, Fitness, Languages, Cooking and Professional Skills.

### 5.6 `skill_listing_table`

Central marketplace listing; one teacher can publish multiple listings:

-   `id`: primary key.
-   `teacher_id`: FK to `user_table.id`, required and indexed.
-   `category_id`: FK to `category_table.id`, required and indexed.
-   `title`: required, max 140 characters.
-   `description`: required text.
-   `level`: `beginner`, `intermediate`, `advanced`, or `all_levels`.
-   `price_amount`: non-negative numeric amount.
-   `currency`: default `INR`.
-   `price_unit`: e.g. `session`, `hour`, or `course`.
-   `teaching_mode`: `online`, `offline`, or `both`.
-   `city`, `area`: optional offline discovery fields; never publish an
    exact home address.
-   `status`: `draft`, `published`, `paused`, or `archived`.
-   `created_at`, `updated_at`.

Set `teacher_id` from the authenticated user; never trust a
client-supplied teacher ID.

### 5.7 `learning_request_table`

Connects a student to a listing and its teacher:

-   `id`: primary key.
-   `skill_listing_id`: FK to `skill_listing_table.id`, required and
    indexed.
-   `student_id`: FK to `user_table.id`, required and indexed.
-   `teacher_id`: FK to `user_table.id`, required and indexed; derive
    from the listing.
-   `message`: required, max 1000 characters.
-   `status`: `pending`, `accepted`, `rejected`, or `cancelled`; default
    `pending`.
-   `teacher_response`: optional.
-   `responded_at`: optional timestamp.
-   `created_at`, `updated_at`.

Derive `student_id` from the authenticated user and `teacher_id` from
the listing. Never accept either identity from the request body.

### 5.8 `review_table` --- later phase

-   `id`: primary key.
-   `learning_request_id`: unique FK to `learning_request_table.id`.
-   `reviewer_id`: FK to `user_table.id`.
-   `teacher_id`: FK to `user_table.id`.
-   `rating`: integer with check constraint 1--5.
-   `comment`: optional, max 1000 characters.
-   `created_at`, `updated_at`.

Do not enable reviews until a completed-learning workflow exists.

### 5.9 Relationship summary

``` text
USER 1 ---- N USER_ROLE N ---- 1 ROLE
USER 1 ---- 0..1 TEACHER_PROFILE
USER 1 ---- N SKILL_LISTING (teacher)
CATEGORY 1 ---- N SKILL_LISTING
SKILL_LISTING 1 ---- N LEARNING_REQUEST
USER 1 ---- N LEARNING_REQUEST (student)
USER 1 ---- N LEARNING_REQUEST (teacher)
LEARNING_REQUEST 1 ---- 0..1 REVIEW (later, after completion workflow)
```

## 6. API contract

All routes use `/api/v1` as the base prefix. Use plural resource names
and the HTTP method conventions from the architecture reference.

### 6.1 Authentication and users

  -------------------------------------------------------------------------------
  Method            Endpoint                  Access            Purpose
  ----------------- ------------------------- ----------------- -----------------
  POST              `/users/register`         Public            Register; assign
                                                                student role by
                                                                default.

  POST              `/users/login`            Public            Verify password
                                                                and issue JWT.

  GET               `/users/me`               Authenticated     Get current
                                                                account and
                                                                roles.

  PUT               `/users/me`               Authenticated     Update allowed
                                                                account fields.

  POST              `/users/logout`           Authenticated     Revoke current
                                                                token if
                                                                revocation is
                                                                implemented.

  POST              `/users/become-teacher`   Authenticated     Add teacher role
                                                                and create
                                                                teacher profile
                                                                atomically.
  -------------------------------------------------------------------------------

### 6.2 Teacher profile

  ------------------------------------------------------------------------------------
  Method            Endpoint                       Access            Purpose
  ----------------- ------------------------------ ----------------- -----------------
  POST              `/profile/teacher`             Teacher           Create own
                                                                     profile if not
                                                                     created during
                                                                     onboarding.

  GET               `/profile/teacher/{user_id}`   Public            View public
                                                                     teacher profile.

  GET               `/profile/teacher/me`          Teacher           Get own teacher
                                                                     profile.

  PUT               `/profile/teacher/me`          Teacher           Update own
                                                                     profile.
  ------------------------------------------------------------------------------------

Avoid duplicate onboarding behavior. Recommended:
`POST /users/become-teacher` adds the role and creates the profile in
one transaction. If profile creation is separate, define the
intermediate state clearly.

### 6.3 Categories

  -----------------------------------------------------------------------------------
  Method            Endpoint                      Access            Purpose
  ----------------- ----------------------------- ----------------- -----------------
  GET               `/categories`                 Public            List active
                                                                    categories.

  GET               `/categories/{category_id}`   Public            Get category
                                                                    details.

  POST              `/categories`                 Admin, later      Create category.

  PUT               `/categories/{category_id}`   Admin, later      Update category.

  DELETE            `/categories/{category_id}`   Admin, later      Prefer
                                                                    deactivation over
                                                                    hard-delete.
  -----------------------------------------------------------------------------------

### 6.4 Skills

  -----------------------------------------------------------------------------------
  Method            Endpoint                      Access            Purpose
  ----------------- ----------------------------- ----------------- -----------------
  POST              `/skills`                     Teacher           Create own
                                                                    listing.

  GET               `/skills`                     Public            Browse published
                                                                    listings.

  GET               `/skills/{skill_id}`          Public            Get listing and
                                                                    safe teacher
                                                                    summary.

  PUT               `/skills/{skill_id}`          Listing owner     Update own
                                                                    listing.

  DELETE            `/skills/{skill_id}`          Listing owner     Archive own
                                                                    listing.

  GET               `/skills/my-skills`           Teacher           Get current
                                                                    user's listings.

  PATCH             `/skills/{skill_id}/status`   Listing owner     Publish, pause or
                                                                    archive listing.
  -----------------------------------------------------------------------------------

### 6.5 Search and discovery

  -------------------------------------------------------------------------------------------
  Method            Endpoint                             Access            Purpose
  ----------------- ------------------------------------ ----------------- ------------------
  GET               `/skills/search`                     Public            Search and filter
                                                                           published
                                                                           listings.

  GET               `/teachers/{user_id}/skills`         Public            List a teacher's
                                                                           published skills.

  GET               `/categories/{category_id}/skills`   Public            List published
                                                                           skills in a
                                                                           category.

  GET               `/teachers/featured`                 Public, later     Curated/featured
                                                                           teachers.
  -------------------------------------------------------------------------------------------

Recommended search parameters: `query`, `category_id`, `city`, `mode`,
`level`, `min_price`, `max_price`, `page`, `page_size`. Validate all
filters, paginate results and cap `page_size` (recommended maximum 50).
Public discovery returns only `published` listings.

### 6.6 Learning requests

  ---------------------------------------------------------------------------------------
  Method            Endpoint                          Access            Purpose
  ----------------- --------------------------------- ----------------- -----------------
  POST              `/requests`                       Authenticated     Send request for
                                                      student           a skill listing.

  GET               `/requests/sent`                  Student           List own sent
                                                                        requests.

  GET               `/requests/received`              Teacher           List requests
                                                                        received by
                                                                        current teacher.

  GET               `/requests/{request_id}`          Request           View if current
                                                      participant       user is the
                                                                        student or
                                                                        teacher.

  PATCH             `/requests/{request_id}/accept`   Recipient teacher Accept pending
                                                                        request.

  PATCH             `/requests/{request_id}/reject`   Recipient teacher Reject pending
                                                                        request.

  PATCH             `/requests/{request_id}/cancel`   Requesting        Cancel own
                                                      student           pending request.
  ---------------------------------------------------------------------------------------

Create request body:

``` json
{
  "skill_listing_id": 21,
  "message": "I want to learn Flutter from the basics."
}
```

Do not accept `student_id` or `teacher_id` from the client.

### 6.7 Reviews --- later

  -------------------------------------------------------------------------------------
  Method            Endpoint                        Access            Purpose
  ----------------- ------------------------------- ----------------- -----------------
  POST              `/reviews`                      Eligible student  Review eligible
                                                                      completed
                                                                      learning.

  GET               `/teachers/{user_id}/reviews`   Public            List teacher
                                                                      reviews.

  PUT               `/reviews/{review_id}`          Review owner      Update own
                                                                      review.

  DELETE            `/reviews/{review_id}`          Review            Delete under
                                                    owner/admin       moderation
                                                                      policy.
  -------------------------------------------------------------------------------------

## 7. Business rules and authorization

Implement these rules in controllers and back them with DB constraints:

1.  Normalize email and enforce uniqueness.
2.  Assign the student role by default at registration.
3.  A user may have both student and teacher roles.
4.  Teacher activation adds the role and creates the profile in one
    transaction.
5.  Only teacher-role users may create/manage listings.
6.  Only a listing owner may edit, publish, pause or archive it.
7.  A listing's category must exist and be active.
8.  Public search returns only published listings.
9.  Only authenticated student-role users may create learning requests.
10. A student cannot request their own listing.
11. Requests require a published listing.
12. `student_id` comes from the token; `teacher_id` comes from the
    listing.
13. Only the intended teacher can accept or reject a request.
14. Only the requesting student can cancel a pending request.
15. Only pending requests may transition to accepted, rejected or
    cancelled.
16. Only the student or teacher participant may view a request.
17. Never return password hashes, tokens, private phone numbers or exact
    home addresses in public DTOs.

Request state transitions:

``` text
pending -> accepted
pending -> rejected
pending -> cancelled
```

These are terminal states in the initial MVP. Do not allow other
transitions through these endpoints.

## 8. Authentication and security

-   Hash passwords with `pwdlib[argon2]`; never store plaintext.
-   Sign and validate JWTs with PyJWT and a secret loaded from settings.
-   Include an expiry claim (`exp`) and a stable user identifier claim
    (`sub` or the reference pattern's `_id`). Pick one convention and
    use it consistently.
-   Use FastAPI `HTTPBearer` to extract credentials.
-   Validate the token and load the current user before protected
    operations.
-   Check role and resource ownership for every protected action.
-   If logout revocation is implemented, store a SHA-256 hash of the
    token plus expiry; do not store raw JWTs.
-   Keep `.env` out of Git; commit `.env.example` with placeholders
    only.
-   Never log passwords, tokens or sensitive personal data.
-   Use HTTPS in production, restrict CORS to known frontend origins,
    and add authentication rate limits before public launch.

## 9. Response, error and DTO conventions

### Success response

Use the existing `ApiResponse` wrapper required by
`FastAPI_Backend_Pattern.md`. Follow the actual class definition in the
repository; do not create a second response format.

Illustrative shape:

``` json
{
  "status": 200,
  "message": "Skills fetched successfully",
  "data": []
}
```

Use `lastUpdated` only for endpoints where the reference's
timestamp-cache pattern is intentionally implemented; do not add it
arbitrarily.

### Errors

-   `400`: invalid business operation.
-   `401`: missing, invalid or expired authentication.
-   `403`: authenticated user lacks permission.
-   `404`: resource not found.
-   `409`: uniqueness conflict or invalid state transition.
-   `422`: request validation failure.

Handle `IntegrityError` with `db.rollback()`. Do not expose SQL errors
or stack traces.

### DTO rules

-   DTOs live in each feature's `dtos.py`.
-   Use explicit Register/Login, Create, Update and Read schema names.
-   Use Pydantic v2 validators to trim strings and enforce allowed
    values.
-   ORM Read schemas use `model_config = {"from_attributes": True}`.
-   Never include sensitive columns in public response DTOs.
-   Do not return raw ORM instances as an undocumented API contract.

## 10. Alembic migrations

-   Use the shared `Base` from `src.utils.db`.
-   Import all model modules in `alembic/env.py` so metadata is
    registered.
-   Load the DB URL from centralized settings.
-   Generate migrations:

``` bash
alembic revision --autogenerate -m "create initial FindNSeekh tables"
```

-   Review generated migration code before applying.
-   Apply migrations:

``` bash
alembic upgrade head
```

-   Commit migration files. Do not manually change production schema
    outside migration history.
-   Coordinate migration ownership when multiple developers work in
    parallel.

## 11. Testing requirements

### Authentication

-   Valid registration succeeds; duplicate email is rejected.
-   Password is stored as a hash.
-   Correct login succeeds; incorrect password fails.
-   Protected routes reject missing, invalid and expired tokens.

### Roles and profiles

-   New user receives student role.
-   Teacher activation adds teacher role without removing student role.
-   Duplicate activation is handled safely.
-   Non-teacher cannot create a listing.

### Skills

-   Teacher can create/update own listing.
-   Another teacher cannot edit or archive it.
-   Invalid category and negative price are rejected.
-   Draft, paused and archived listings are hidden from public search.

### Learning requests

-   Student can request a published listing.
-   Student cannot request own or unpublished listing.
-   Client-supplied student/teacher IDs are not trusted.
-   Only intended teacher can accept/reject.
-   Only requesting student can cancel.
-   Invalid state transitions are rejected.

### Privacy

-   Public responses never expose password hashes, JWTs, private phone
    numbers or exact residential addresses.

## 12. Development sequence

1.  Project skeleton, requirements, settings and environment
    configuration.
2.  SQLAlchemy Base, database engine and `get_db`.
3.  `ApiResponse`, authentication utilities and common error
    conventions.
4.  User and role models.
5.  Teacher profile and category models.
6.  Skill listing and learning request models.
7.  Alembic initial migration; review and apply.
8.  Registration, login, `/users/me` and JWT dependencies.
9.  Teacher activation and teacher profile APIs.
10. Category read APIs and seed initial categories.
11. Skill listing CRUD and ownership checks.
12. Search, filters and pagination.
13. Learning request creation, inbox, accept/reject/cancel.
14. Integration tests, API docs and staging deployment.
15. Reviews only after a completed-learning workflow is defined.

## 13. Instructions for AI coding assistants

Before changing code:

1.  Inspect the repository and read `FastAPI_Backend_Pattern.md` and
    this file.
2.  Check existing files before creating new ones; do not duplicate
    settings, DB, auth, response or model infrastructure.
3.  Identify the feature module responsible for the change.
4.  For multi-file work, state the files to create/modify and why.
5.  Follow the existing imports, naming conventions, response wrapper
    and synchronous SQLAlchemy pattern.
6.  Do not make unrelated refactors or add unrequested packages.
7.  For every new model, update Alembic model imports and explain the
    migration required.
8.  For protected APIs, implement authentication, role checks and
    ownership checks.
9.  For DB writes, handle commit, refresh, rollback and integrity
    conflicts.
10. Add/update tests for success, validation, authorization and failure
    cases.
11. Explain how to run and verify the endpoint.
12. If a requirement is unclear or conflicts with these rules, ask a
    focused question before making a breaking assumption.

Before implementing a new API, identify its purpose, method/path, access
level, request/response DTOs, affected tables, business rules, failure
cases and files to change.

## 14. MVP definition of done

The backend MVP is ready for a pilot when:

-   A user can register and log in.
-   One account can have both teacher and student roles.
-   A teacher can create a profile and publish skill listings.
-   A learner can browse and filter published listings.
-   A learner can view a teacher's public profile.
-   A learner can send a learning request.
-   The correct teacher can accept or reject the request.
-   Both participants can view their request history and status.
-   Authentication, authorization, ownership checks, validation, DB
    constraints and integration tests work.

------------------------------------------------------------------------

## Final implementation rule

**Use `FastAPI_Backend_Pattern.md` for implementation patterns and this
`FINDNSEEKH_BACKEND_GUIDE.md` for FindNSeekh's product, database and API
requirements. Use `FindNSeekh_Backend_Architecture_Blueprint.pdf` as the
detailed planning document. Keep all three aligned when decisions
change.**

Adding these documents to a repository does not automatically create or
update APIs. The developer or AI coding assistant must read them and
implement the routers, controllers, DTOs, models, migrations and tests.
