# app/api/v1/endpoints/prompts.py
from typing import Any, List
# Import BaseModel and Field for the custom payload schema
from pydantic import BaseModel, Field 
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
from sqlalchemy.orm import Session

# Import CRUD operations, schemas, models, and dependencies
from app import crud, schemas, models 
from app.crud.prompt import CRUDPrompt
from app.models.prompt import Prompt
# No longer need models.User or get_current_active_user here
from app.dependencies import get_db 

router = APIRouter()

# Dependency function to get the CRUDPrompt instance (remains the same)
def get_prompt_crud() -> CRUDPrompt:
    """
    Dependency injector for CRUDPrompt.
    Returns a new instance of CRUDPrompt initialized with the Prompt model.
    """
    return CRUDPrompt(Prompt)

# Define a specific payload schema for prompt creation in this auth-less context
class PromptCreatePayload(schemas.PromptCreate):
    user_id: int = Field(..., description="The ID of the user creating the prompt")

    class Config:
        schema_extra = {
            "example": {
                "prompt": "How to optimize this query?",
                "user_id": 1 # Client must provide the user ID
            }
        }

@router.get("/", response_model=List[schemas.Prompt])
def read_prompts(
    db: Session = Depends(get_db),
    prompt_crud: CRUDPrompt = Depends(get_prompt_crud),
    skip: int = Query(0, ge=0, description="Number of prompts to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of prompts to return")
    # Optional: Add a user_id query parameter if you want to allow filtering
    # user_id: Optional[int] = Query(None, description="Filter prompts by user ID")
) -> Any:
    """
    Retrieve all prompts (no user filtering without authentication).
    
    NOTE: In a real application with authentication, this would typically
    be restricted or filtered to the current user's prompts.
    """
    # Use the generic get_multi to fetch all prompts
    prompts = prompt_crud.get_multi(db=db, skip=skip, limit=limit)
    # If filtering by optional user_id query param was added:
    # if user_id is not None:
    #     prompts = prompt_crud.get_multi_by_owner(db=db, user_id=user_id, skip=skip, limit=limit)
    # else:
    #     prompts = prompt_crud.get_multi(db=db, skip=skip, limit=limit)
    return prompts

@router.post("/", response_model=schemas.Prompt, status_code=201)
def create_prompt(
    *,
    db: Session = Depends(get_db),
    prompt_crud: CRUDPrompt = Depends(get_prompt_crud),
    # Use the combined payload schema requiring prompt and user_id
    payload: PromptCreatePayload = Body(...) 
) -> Any:
    """
    Create a new prompt. Requires specifying the user ID in the request body.
    
    NOTE: This requires the client to know and send the user_id.
    This will change when authentication is implemented.
    """
    # Optional: Check if the provided user_id actually exists
    # user_crud = CRUDUser(models.User) # Need to get user crud if checking
    # user = user_crud.get(db, id=payload.user_id)
    # if not user:
    #     raise HTTPException(status_code=404, detail=f"User with id {payload.user_id} not found")
        
    # Extract the prompt content into the standard PromptCreate schema
    prompt_obj_in = schemas.PromptCreate(prompt=payload.prompt)
    
    # Use the CRUD method that associates with the provided user_id
    prompt = prompt_crud.create_with_owner(db=db, obj_in=prompt_obj_in, user_id=payload.user_id)
    return prompt

@router.get("/{prompt_id}", response_model=schemas.Prompt)
def read_prompt(
    *,
    db: Session = Depends(get_db),
    prompt_crud: CRUDPrompt = Depends(get_prompt_crud),
    prompt_id: int = Path(..., title="The ID of the prompt to get", ge=1)
) -> Any:
    """
    Get a specific prompt by ID. (No authorization check).
    
    NOTE: Without authentication, any existing prompt ID can be accessed.
    """
    prompt = prompt_crud.get(db, id=prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    # No authorization check here in the auth-less version
    return prompt

@router.put("/{prompt_id}", response_model=schemas.Prompt)
def update_prompt(
    *,
    db: Session = Depends(get_db),
    prompt_crud: CRUDPrompt = Depends(get_prompt_crud),
    prompt_id: int = Path(..., title="The ID of the prompt to update", ge=1),
    prompt_in: schemas.PromptUpdate = Body(...) # Standard update schema
) -> Any:
    """
    Update a specific prompt. (No authorization check).
    
    NOTE: Without authentication, any existing prompt can be updated.
    """
    db_prompt = prompt_crud.get(db, id=prompt_id)
    if not db_prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    # No authorization check here in the auth-less version
        
    # Use the generic update method from the base CRUD class
    prompt = prompt_crud.update(db=db, db_obj=db_prompt, obj_in=prompt_in)
    return prompt

@router.delete("/{prompt_id}", status_code=204, response_model=None)
def delete_prompt(
    *,
    db: Session = Depends(get_db),
    prompt_crud: CRUDPrompt = Depends(get_prompt_crud),
    prompt_id: int = Path(..., title="The ID of the prompt to delete", ge=1)
) -> None:
    """
    Delete a specific prompt. (No authorization check).
    
    NOTE: Without authentication, any existing prompt can be deleted.
    Returns HTTP 204 No Content on successful deletion.
    """
    db_prompt = prompt_crud.get(db, id=prompt_id)
    if not db_prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    # No authorization check here in the auth-less version
        
    # Use the injected prompt_crud instance to remove the prompt
    prompt_crud.remove(db=db, id=prompt_id)
    # No return value needed for HTTP 204