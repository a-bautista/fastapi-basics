# main.py
from fastapi import FastAPI, HTTPException, Path, Query, Depends
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uvicorn
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
from datetime import datetime

# Database configuration - read from environment variables or use defaults
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "db")  # 'db' is the service name in docker-compose
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "fastapi_db")

# Create SQLAlchemy connection
SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define SQLAlchemy model for User
class UserModel(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(100), nullable=False)  # In production, use proper password hashing
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Initialize FastAPI app
app = FastAPI(
    title="Demo App",
    description="A demo API with FastAPI",
    version="0.3.0"
)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Define Pydantic models for API validation
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: str = Field(..., description="User's email address")
    #full_name: Optional[str] = Field(None, max_length=100, description="User's full name")
    is_active: Optional[bool] = Field(True, description="Whether the user is active")

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="User's password")

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Unique username")
    email: Optional[str] = Field(None, description="User's email address")
    #full_name: Optional[str] = Field(None, max_length=100, description="User's full name")
    is_active: Optional[bool] = Field(None, description="Whether the user is active")
    password: Optional[str] = Field(None, min_length=8, description="User's password")

class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "username": "johndoe",
                "email": "john.doe@example.com",
                #"full_name": "John Doe",
                "is_active": True,
                "created_at": "2023-01-15T10:30:00",
                "updated_at": "2023-01-15T10:30:00"
            }
        }

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the API in FastAPI"}

# GET all users
@app.get("/users/", response_model=List[User], tags=["Users"])
async def get_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of users to return"),
    db: Session = Depends(get_db)
):
    users = db.query(UserModel).offset(skip).limit(limit).all()
    return users

# GET a specific user by ID
@app.get("/users/{user_id}", response_model=User, tags=["Users"])
async def get_user(
    user_id: int = Path(..., title="ID of the user to get", ge=1),
    db: Session = Depends(get_db)
):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# POST a new user
@app.post("/users/", response_model=User, status_code=201, tags=["Users"])
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if username already exists
    db_user = db.query(UserModel).filter(UserModel.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email already exists
    db_user = db.query(UserModel).filter(UserModel.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # In a real application, we would hash the password
    hashed_password = user.password + "_hashed"  # This is just a placeholder
    
    db_user = UserModel(
        username=user.username,
        email=user.email,
        #full_name=user.full_name,
        hashed_password=hashed_password,
        is_active=user.is_active
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# PUT (update) an existing user
@app.put("/users/{user_id}", response_model=User, tags=["Users"])
async def update_user(
    user_id: int = Path(..., title="ID of the user to update", ge=1),
    user: UserUpdate = None,
    db: Session = Depends(get_db)
):
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update username if provided and not already taken
    if user.username is not None:
        existing_user = db.query(UserModel).filter(UserModel.username == user.username).first()
        if existing_user and existing_user.id != user_id:
            raise HTTPException(status_code=400, detail="Username already taken")
        db_user.username = user.username
    
    # Update email if provided and not already taken
    if user.email is not None:
        existing_user = db.query(UserModel).filter(UserModel.email == user.email).first()
        if existing_user and existing_user.id != user_id:
            raise HTTPException(status_code=400, detail="Email already taken")
        db_user.email = user.email
    
    # Update other fields if provided
    #if user.full_name is not None:
    #    db_user.full_name = user.full_name
    
    if user.is_active is not None:
        db_user.is_active = user.is_active
    
    # Update password if provided
    if user.password is not None:
        # In a real application, we would hash the password
        db_user.hashed_password = user.password + "_hashed"  # This is just a placeholder
    
    # The updated_at field will be automatically updated due to onupdate=datetime.utcnow
    
    db.commit()
    db.refresh(db_user)
    return db_user

# DELETE a user
@app.delete("/users/{user_id}", status_code=204, tags=["Users"])
async def delete_user(
    user_id: int = Path(..., title="ID of the user to delete", ge=1),
    db: Session = Depends(get_db)
):
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(db_user)
    db.commit()
    return None

# Initialize the database
@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)
    
    # Add sample data if the database is empty
    db = SessionLocal()
    if db.query(UserModel).count() == 0:
        # In a real application, we would hash the password
        db_user = UserModel(
            username="admin",
            email="admin@example.com",
            #full_name="Admin User",
            hashed_password="admin_password_hashed",  # This is just a placeholder
            is_active=True
        )
        db.add(db_user)
        db.commit()
    db.close()

# Run the server if this file is executed directly
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)