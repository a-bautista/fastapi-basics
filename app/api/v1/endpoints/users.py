# app/api/v1/endpoints/users.py
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app import crud, schemas
from app.crud.user import CRUDUser
from app.dependencies import get_db
from app.models.user import User

router = APIRouter()

def get_user_crud() -> CRUDUser: # dependency injection
    return CRUDUser(User)

@router.get("/", response_model=List[schemas.User])
def read_users(
    db: Session = Depends(get_db),
    user_crud: CRUDUser = Depends(get_user_crud),
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of users to return")
) -> Any:
    """
    Retrieve users.
    """
    users = user_crud.get_multi(db, skip=skip, limit=limit)
    return users
    #users = crud.user.get_multi(db, skip=skip, limit=limit)
    #return users

# When you hit the root level with the prefix with a post then you will be creating a new user
@router.post("/", response_model=schemas.User, status_code=201)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_crud: CRUDUser = Depends(get_user_crud),
    user_in: schemas.UserCreate
) -> Any:
    """
    Create new user.
    """
    # Check if username is taken
    user = user_crud.get_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The username is already taken"
        )
    
    # Check if email is taken
    user = user_crud.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The email is already registered"
        )
    
    # Create the user
    user = user_crud.create(db, obj_in=user_in)
    return user

@router.get("/{user_id}", response_model=schemas.User)
def read_user(
    *,
    db: Session = Depends(get_db),
    user_crud: CRUDUser = Depends(get_user_crud),
    user_id: int = Path(..., title="The ID of the user to get", ge=1)
) -> Any:
    """
    Get user by ID.
    """
    user = user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=schemas.User)
def update_user(
    *,
    db: Session = Depends(get_db),
    user_crud: CRUDUser = Depends(get_user_crud),
    user_id: int = Path(..., title="The ID of the user to update", ge=1),
    user_in: schemas.UserUpdate
) -> Any:
    """
    Update a user.
    """
    user = user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if username is taken (if being updated)
    if user_in.username and user_in.username != user.username:
        existing_user = user_crud.get_by_username(db, username=user_in.username)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="The username is already taken"
            )
    
    # Check if email is taken (if being updated)
    if user_in.email and user_in.email != user.email:
        existing_user = user_crud.get_by_email(db, email=user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="The email is already registered"
            )
    
    # Update the user
    user = user_crud.update(db, db_obj=user, obj_in=user_in)
    return user

@router.delete("/{user_id}", status_code=204, response_model=None)
def delete_user(
    *,
    db: Session = Depends(get_db),
    user_crud: CRUDUser = Depends(get_user_crud),
    user_id: int = Path(..., title="The ID of the user to delete", ge=1)
) -> None:
    """
    Delete a user.
    """
    user = user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    crud.user.remove(db, id=user_id)