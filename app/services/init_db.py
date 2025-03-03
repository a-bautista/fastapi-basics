# app/services/init_db.py
from sqlalchemy.orm import Session

from app import crud, schemas
from app.models.base import Base, engine


def init_db(db: Session) -> None:
    """Initialize database with tables and sample data."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Check if there are users already
    user = crud.user.get_by_username(db, username="admin")
    if user:
        return  # Database already initialized
    
    # Create a sample admin user
    user_in = schemas.UserCreate(
        username="admin",
        email="admin@example.com",
        #full_name="Admin User",
        password="adminpassword",
        is_active=True
    )
    
    crud.user.create(db, obj_in=user_in)