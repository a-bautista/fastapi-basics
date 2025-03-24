# app/services/init_db.py
from fastapi import Depends
from sqlalchemy.orm import Session

from app import crud, schemas
from app.crud.user import CRUDUser
from app.models.user import User

def get_user_crud() -> CRUDUser:
    return CRUDUser(User)

def init_db(db: Session) -> None:
    """
    Initialize database with sample data.
    
    Note: No longer creates tables - this is now handled by Alembic migrations.
    Only seeds initial data if needed.
    """
    user_crud = get_user_crud()
    # Check if there are users already
    user = user_crud.get_by_username(db, username="admin")
    if user:
        return  # Database already initialized with sample data
    
    # Create a sample admin user
    user_in = schemas.UserCreate(
        username="admin",
        email="admin@example.com",
        #full_name="Admin User",
        password="adminpassword",
        is_active=True
    )
    
    user_crud.create(db, obj_in=user_in)