# app/dependencies.py
from typing import Generator
from sqlalchemy.orm import Session
from app.models.base import SessionLocal

def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting a database session.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()