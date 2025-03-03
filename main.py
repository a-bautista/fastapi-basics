from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import settings
from app.models.base import Base, engine

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A FastAPI application",
    version="0.4.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs"
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}!",
        "docs": "/docs",
        "api_base_url": settings.API_V1_STR
    }

# Initialize the database
@app.on_event("startup")
async def startup():
    # Create all tables
    Base.metadata.create_all(bind=engine)

# Run the server if this file is executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)