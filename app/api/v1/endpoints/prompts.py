# app/api/v1/endpoints/prompts.py
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

# Import main.py templates object
from main import templates

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

@router.post("/", response_class=RedirectResponse, status_code=303)
async def create_prompt_from_form(
    *,
    db: Session = Depends(get_db),
    prompt_crud: CRUDPrompt = Depends(get_prompt_crud),
    prompt: str = Form(...),
    user_id: int = Form(...)
) -> RedirectResponse:
    """
    Create a new prompt from HTML form data.
    Redirects to the new prompt's UI page upon successful creation.
    """
    # Optional: Check if the provided user_id actually exists
    # user_crud = CRUDUser(models.User) # Need to get user crud if checking
    # user = user_crud.get(db, id=user_id)
    # if not user:
    #     raise HTTPException(status_code=404, detail=f"User with id {user_id} not found. Cannot create prompt.")
        
    prompt_obj_in = schemas.PromptCreate(prompt=prompt)
    
    new_prompt = prompt_crud.create_with_owner(db=db, obj_in=prompt_obj_in, user_id=user_id)
    return RedirectResponse(url=f"/prompts/ui/{new_prompt.id}", status_code=303)

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


# UI Endpoints
@router.get("/ui/", response_class=HTMLResponse)
async def list_prompts_ui(
    request: Request,
    db: Session = Depends(get_db),
    prompt_crud: CRUDPrompt = Depends(get_prompt_crud),
    skip: int = 0, # Default to starting from the beginning
    limit: int = 100 # Default to fetching 100 prompts
):
    """
    Display a list of prompts in an HTML page.
    """
    prompts = prompt_crud.get_multi(db=db, skip=skip, limit=limit)
    return templates.TemplateResponse(
        "prompts/list_prompts.html", {"request": request, "prompts": prompts}
    )

@router.get("/ui/{prompt_id}", response_class=HTMLResponse)
async def view_prompt_ui(
    request: Request,
    prompt_id: int = Path(..., title="The ID of the prompt to get", ge=1),
    db: Session = Depends(get_db),
    prompt_crud: CRUDPrompt = Depends(get_prompt_crud),
):
    """
    Display a single prompt in an HTML page.
    """
    prompt = prompt_crud.get(db, id=prompt_id)
    if not prompt:
        # For a UI, it's often better to render a custom 404 page,
        # but HTTPException is fine for now and will be caught by FastAPI.
        raise HTTPException(status_code=404, detail="Prompt not found")
    return templates.TemplateResponse(
        "prompts/view_prompt.html", {"request": request, "prompt": prompt}
    )

@router.get("/ui/{prompt_id}/edit", response_class=HTMLResponse)
async def edit_prompt_ui(
    request: Request,
    prompt_id: int = Path(..., title="The ID of the prompt to edit", ge=1),
    db: Session = Depends(get_db),
    prompt_crud: CRUDPrompt = Depends(get_prompt_crud),
):
    """
    Display an HTML form for editing a prompt's response.
    """
    prompt = prompt_crud.get(db, id=prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return templates.TemplateResponse(
        "prompts/edit_prompt.html", {"request": request, "prompt": prompt}
    )

@router.post("/ui/{prompt_id}/edit", response_class=RedirectResponse, status_code=303)
async def handle_edit_prompt_form(
    *,
    db: Session = Depends(get_db),
    prompt_crud: CRUDPrompt = Depends(get_prompt_crud),
    prompt_id: int = Path(..., title="The ID of the prompt to update", ge=1),
    response: str = Form(...)
) -> RedirectResponse:
    """
    Handle the submission of the prompt edit form.
    Updates the prompt's response and redirects to the view page.
    """
    db_prompt = prompt_crud.get(db, id=prompt_id)
    if not db_prompt:
        raise HTTPException(status_code=404, detail="Prompt not found, cannot update.")

    # Ensure 'response' is not None if the schema requires it,
    # or handle optional updates appropriately.
    # For this case, we are updating the response field.
    update_data = schemas.PromptUpdate(response=response)

    prompt_crud.update(db=db, db_obj=db_prompt, obj_in=update_data)

    return RedirectResponse(url=f"/prompts/ui/{prompt_id}", status_code=303)