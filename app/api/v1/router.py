# app/api/v1/router.py
from fastapi import APIRouter

from app.api.v1.endpoints import users

# Create v1 router
api_router = APIRouter()

# Include routes from endpoint modules
api_router.include_router(users.router, prefix="/users", tags=["users"])

# Additional endpoint modules would be included here
# e.g. api_router.include_router(items.router, prefix="/items", tags=["items"])