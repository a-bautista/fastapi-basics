# app/models/user.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from datetime import datetime
from sqlalchemy.orm import Session, relationship

from app.models.base import Base

class User(Base):
    """User database model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    #full_name = Column(String(100), nullable=True)
    hashed_password = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to Prompt
    prompts = relationship("Prompt", back_populates="owner", cascade="all, delete-orphan")
    # 'prompts' is how you'll access the list of prompts from a User object (e.g., my_user.prompts)
    # 'cascade="all, delete-orphan"' means if a user is deleted, their prompts are also deleted. Adjust if needed.