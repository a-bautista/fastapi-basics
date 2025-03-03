# app/schemas/user.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

# Shared properties
class UserBase(BaseModel):
    """Base schema for shared User properties"""
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: str = Field(..., description="User's email address")
    #full_name: Optional[str] = Field(None, max_length=100, description="User's full name")
    is_active: Optional[bool] = Field(True, description="Whether the user is active")

# Properties to receive on user creation
class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8, description="User's password")
    
    class Config:
        schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "john.doe@example.com",
                #"full_name": "John Doe",
                "is_active": True,
                "password": "securepassword"
            }
        }

# Properties to receive on user update
class UserUpdate(BaseModel):
    """Schema for updating an existing user"""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Unique username")
    email: Optional[str] = Field(None, description="User's email address")
    #full_name: Optional[str] = Field(None, max_length=100, description="User's full name")
    is_active: Optional[bool] = Field(None, description="Whether the user is active")
    password: Optional[str] = Field(None, min_length=8, description="User's password")
    
    # class Config:
    #     schema_extra = {
    #         "example": {
    #             "full_name": "John M. Doe"
    #         }
    #     }

# Properties to return to client
class User(UserBase):
    """Schema for user responses"""
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