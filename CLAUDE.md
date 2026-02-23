# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
# Start both API and PostgreSQL containers
docker-compose up --build

# API will be available at http://localhost:8000
# PostgreSQL at localhost:5432
```

### Database Migrations
```bash
# Create a new migration after model changes
docker-compose exec api alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec api alembic upgrade head

# Rollback one migration
docker-compose exec api alembic downgrade -1

# View migration history
docker-compose exec api alembic history
```

### Accessing Services
```bash
# Access API container shell
docker-compose exec api bash

# Access PostgreSQL directly
docker-compose exec db psql -U postgres -d fastapi_db

# View API logs
docker-compose logs -f api

# View database logs
docker-compose logs -f db
```

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/api/v1/openapi.json

## Architecture Overview

### Layered Modular Monolith
The codebase follows a strict layered architecture with clear separation of concerns:

```
API Layer (endpoints/)
    ↓ calls
Business Logic (services/)
    ↓ calls
Data Access (crud/)
    ↓ uses
Models (models/) + Schemas (schemas/)
```

**Critical Rule**: Never bypass layers. API endpoints must not directly call models; they must go through CRUD layer.

### Key Architectural Patterns

**1. Repository Pattern (CRUD Layer)**
- `app/crud/base.py` provides `CRUDBase[ModelType, CreateSchemaType, UpdateSchemaType]` generic class
- All CRUD classes inherit from this base and add model-specific queries
- Example: `CRUDUser` extends `CRUDBase` with `get_by_username()` and `get_by_email()`

**2. Dependency Injection (Not Singletons)**
- As of v0.4.0, the project removed singleton pattern in favor of dependency injection
- Database sessions injected via `Depends(get_db)`
- CRUD instances injected as dependencies in endpoints
- Example in `app/api/v1/endpoints/users.py`:
  ```python
  def create_user(
      user_in: UserCreate,
      db: Session = Depends(get_db),
      user_crud: CRUDUser = Depends()  # Injected, not instantiated
  ):
  ```

**3. Data Transfer Objects (Pydantic Schemas)**
- Separate schemas for different operations: `ModelCreate`, `ModelUpdate`, `Model` (response)
- Request/response validation handled automatically by Pydantic
- Schemas in `app/schemas/` mirror models in `app/models/` but serve different purposes

**4. Relationship Management**
- Users → Prompts: One-to-many with cascade delete
- When adding new relationships, always define both sides and specify cascade behavior
- Use SQLAlchemy `relationship()` with `back_populates` for bidirectional access

## Important Implementation Details

### Database Connection
- Connection string built in `app/config.py:28` from environment variables
- SQLAlchemy engine and session factory in `app/models/base.py`
- Database initialization happens on startup (`main.py:90-100`) via `init_db()` service
- **Note**: Alembic stamps `initial_migration` on container startup (see `docker-compose.yml:22`)

### Migration System
- **Duplicate migration directories exist**: Both `/migrations/` and `/app/alembic/` contain migrations
- Active configuration uses `/migrations/` (see `alembic.ini:5`)
- When creating migrations, they will go to `/migrations/versions/`
- Database URL hardcoded in `alembic.ini:60` - must match `.env` credentials

### API Versioning
- All API routes prefixed with `/api/v1` (defined in `app/config.py:15`)
- Version included in router: `app.include_router(api_router, prefix=settings.API_V1_STR)` (`main.py:37`)
- OpenAPI JSON exposed at versioned path (`main.py:23`)

### Session Management
- Uses `itsdangerous.URLSafeSerializer` for cookie-based sessions
- SECRET_KEY hardcoded in `main.py:13` (TODO: move to settings)
- Login endpoints at `/login` (GET/POST), profile at `/profile`, logout at `/logout`
- Root `/` redirects based on session validity

### Password Handling
- **Current implementation is placeholder**: passwords are "hashed" by appending `"_hashed"` suffix
- This is intentional for development/demo purposes
- Planned enhancement: Use bcrypt or Argon2 for production

## Working with Models

### Adding a New Model
1. Create model in `app/models/your_model.py` inheriting from `Base`
2. Create schemas in `app/schemas/your_model.py` (Create, Update, Response)
3. Create CRUD in `app/crud/your_model.py` inheriting from `CRUDBase`
4. Create endpoints in `app/api/v1/endpoints/your_model.py`
5. Register router in `app/api/v1/router.py`
6. Generate migration: `docker-compose exec api alembic revision --autogenerate -m "add your_model table"`
7. Apply migration: `docker-compose exec api alembic upgrade head`

### Model Relationships
When defining foreign keys, follow this pattern from `app/models/prompt.py`:
```python
user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
owner = relationship("User", back_populates="prompts")
```

And the inverse in the parent model (`app/models/user.py`):
```python
prompts = relationship("Prompt", back_populates="owner", cascade="all, delete-orphan")
```

## Common Patterns in Codebase

### CRUD Operation Pattern
All CRUD classes follow this structure:
```python
from app.crud.base import CRUDBase
from app.models.your_model import YourModel
from app.schemas.your_model import YourModelCreate, YourModelUpdate

class CRUDYourModel(CRUDBase[YourModel, YourModelCreate, YourModelUpdate]):
    # Add model-specific queries here
    def get_by_custom_field(self, db: Session, *, field_value: str) -> Optional[YourModel]:
        return db.query(self.model).filter(self.model.custom_field == field_value).first()
```

### Endpoint Pattern
Endpoints use dependency injection for database access:
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.crud.your_model import crud_your_model

router = APIRouter()

@router.get("/")
def read_items(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    items = crud_your_model.get_multi(db, skip=skip, limit=limit)
    return items
```

### Schema Pattern
Three schemas per model:
```python
# Base with shared attributes
class YourModelBase(BaseModel):
    field: str

# For creating (may require additional fields)
class YourModelCreate(YourModelBase):
    required_field: str

# For updating (all fields optional)
class YourModelUpdate(BaseModel):
    field: Optional[str] = None

# For responses (includes DB fields like id, timestamps)
class YourModel(YourModelBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True  # Enables ORM mode
```

## Environment Configuration

Required environment variables in `.env`:
- `DB_USER`: PostgreSQL username (default: postgres)
- `DB_PASSWORD`: PostgreSQL password (default: postgres)
- `DB_HOST`: Database host (default: db for Docker, localhost for local)
- `DB_PORT`: Database port (default: 5432)
- `DB_NAME`: Database name (default: fastapi_db)

Settings loaded via `pydantic_settings.BaseSettings` in `app/config.py`.

## Known Limitations & TODOs

From the codebase comments and README:
- Password hashing is placeholder (needs bcrypt/Argon2)
- SECRET_KEY hardcoded in main.py (should be in settings/environment)
- No JWT authentication (session-based only)
- CORS allows all origins (`["*"]`) - needs restriction for production
- No rate limiting implemented
- No comprehensive logging system
- No test suite exists yet

## Deployment Notes

- Application runs on port 8000 (configurable in docker-compose.yml)
- Volume mount `./:/app` enables hot-reload during development
- PostgreSQL data persists in named volume `postgres_data`
- Health check endpoint: `/health` returns `{"status": "ok"}`
- Database health checked via `pg_isready` before API starts
