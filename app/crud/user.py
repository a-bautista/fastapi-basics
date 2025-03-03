# app/crud/user.py
from typing import Optional, Dict, Any, Union
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """CRUD operations for User model"""
    
    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        """
        Get a user by username.
        
        Args:
            db: Database session
            username: Username to look for
            
        Returns:
            User if found, None otherwise
        """
        return db.query(User).filter(User.username == username).first()
    
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """
        Get a user by email.
        
        Args:
            db: Database session
            email: Email to look for
            
        Returns:
            User if found, None otherwise
        """
        return db.query(User).filter(User.email == email).first()
    
    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """
        Create a new user with hashed password.
        
        Args:
            db: Database session
            obj_in: Data for creating the user
            
        Returns:
            The created user
        """
        # In a real app, we'd use proper password hashing
        hashed_password = obj_in.password + "_hashed"  # This is just a placeholder
        
        db_obj = User(
            username=obj_in.username,
            email=obj_in.email,
            #full_name=obj_in.full_name,
            hashed_password=hashed_password,
            is_active=obj_in.is_active
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self, db: Session, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        """
        Update a user, handling password hashing if needed.
        
        Args:
            db: Database session
            db_obj: User object to update
            obj_in: New data to update with
            
        Returns:
            The updated user
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        
        # Handle password separately if it's being updated
        if "password" in update_data:
            # In a real app, we'd use proper password hashing
            hashed_password = update_data["password"] + "_hashed"  # This is just a placeholder
            update_data["hashed_password"] = hashed_password
            del update_data["password"]
        
        return super().update(db, db_obj=db_obj, obj_in=update_data)

# Create a singleton instance
user = CRUDUser(User)