# app/main.py
from fastapi import FastAPI, Request, Form, Response, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from itsdangerous import URLSafeSerializer, BadTimeSignature, SignatureExpired
from sqlalchemy.orm import Session

from app.api.v1.router import api_router
from app.config import settings
from app.models.base import Base, engine
from app.dependencies import get_db
from app.crud.user import CRUDUser
from app.crud.prompt import CRUDPrompt
from app.models.user import User
from app.models.prompt import Prompt

# Secret key for session management. TODO: Move to settings.
SECRET_KEY = "your-secret-key"
serializer = URLSafeSerializer(SECRET_KEY)

templates = Jinja2Templates(directory="app/templates")

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A scalable FastAPI application with PostgreSQL",
    version="0.4.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs"
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Root endpoint
@app.get("/")
async def root(request: Request):
    user = request.cookies.get("session")
    if user:
        try:
            serializer.loads(user)
            return RedirectResponse(url="/prompts")
        except (BadTimeSignature, SignatureExpired):
            pass
    return RedirectResponse(url="/login")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def handle_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Validate credentials against database
    user_crud = CRUDUser(User)
    user = user_crud.get_by_username(db, username=username)

    # Check if user exists and password matches (using placeholder hashing)
    if user and user.hashed_password == password + "_hashed":
        session_data = {"username": username, "user_id": user.id}
        session_cookie = serializer.dumps(session_data)
        response = RedirectResponse(url="/prompts", status_code=302)
        response.set_cookie(key="session", value=session_cookie, httponly=True)
        return response
    else:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid username or password"})

@app.get("/profile", response_class=HTMLResponse)
async def profile(request: Request, db: Session = Depends(get_db)):
    session_cookie = request.cookies.get("session")
    if not session_cookie:
        return RedirectResponse(url="/login")
    try:
        user_data = serializer.loads(session_cookie)
        username = user_data["username"]

        # Fetch user details from database
        user_crud = CRUDUser(User)
        user = user_crud.get_by_username(db, username=username)

        if not user:
            return RedirectResponse(url="/login")

        # Get prompt count
        prompt_crud = CRUDPrompt(Prompt)
        prompts = prompt_crud.get_multi_by_owner(db, user_id=user.id)
        prompt_count = len(prompts)

        return templates.TemplateResponse(
            "profile.html",
            {
                "request": request,
                "username": username,
                "user": user,
                "prompt_count": prompt_count
            }
        )
    except (BadTimeSignature, SignatureExpired):
        return RedirectResponse(url="/login")

@app.get("/profile/edit", response_class=HTMLResponse)
async def edit_profile_form(request: Request, db: Session = Depends(get_db)):
    session_cookie = request.cookies.get("session")
    if not session_cookie:
        return RedirectResponse(url="/login")
    try:
        user_data = serializer.loads(session_cookie)
        username = user_data["username"]

        # Fetch user details from database
        user_crud = CRUDUser(User)
        user = user_crud.get_by_username(db, username=username)

        if not user:
            return RedirectResponse(url="/login")

        return templates.TemplateResponse(
            "edit_profile.html",
            {
                "request": request,
                "username": username,
                "user": user
            }
        )
    except (BadTimeSignature, SignatureExpired):
        return RedirectResponse(url="/login")

@app.post("/profile/edit")
async def edit_profile_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    new_password: str = Form(""),
    confirm_password: str = Form(""),
    db: Session = Depends(get_db)
):
    session_cookie = request.cookies.get("session")
    if not session_cookie:
        return RedirectResponse(url="/login")

    try:
        user_data = serializer.loads(session_cookie)
        current_username = user_data["username"]

        # Fetch current user
        user_crud = CRUDUser(User)
        user = user_crud.get_by_username(db, username=current_username)

        if not user:
            return RedirectResponse(url="/login")

        # Validation: check if username is taken by another user
        if username != current_username:
            existing_user = user_crud.get_by_username(db, username=username)
            if existing_user:
                return templates.TemplateResponse(
                    "edit_profile.html",
                    {
                        "request": request,
                        "username": current_username,
                        "user": user,
                        "error": "Username already taken"
                    }
                )

        # Validation: check if email is taken by another user
        if email != user.email:
            existing_email = user_crud.get_by_email(db, email=email)
            if existing_email and existing_email.id != user.id:
                return templates.TemplateResponse(
                    "edit_profile.html",
                    {
                        "request": request,
                        "username": current_username,
                        "user": user,
                        "error": "Email already in use"
                    }
                )

        # Validation: check if passwords match
        if new_password and new_password != confirm_password:
            return templates.TemplateResponse(
                "edit_profile.html",
                {
                    "request": request,
                    "username": current_username,
                    "user": user,
                    "error": "Passwords do not match"
                }
            )

        # Prepare update data
        update_data = {
            "username": username,
            "email": email
        }

        # Add password to update if provided
        if new_password:
            update_data["password"] = new_password

        # Update user
        user_crud.update(db, db_obj=user, obj_in=update_data)

        # Update session with new username if changed
        if username != current_username:
            session_data = {"username": username, "user_id": user.id}
            session_cookie_new = serializer.dumps(session_data)
            response = RedirectResponse(url="/profile", status_code=302)
            response.set_cookie(key="session", value=session_cookie_new, httponly=True)
            return response

        return RedirectResponse(url="/profile", status_code=302)

    except (BadTimeSignature, SignatureExpired):
        return RedirectResponse(url="/login")

@app.get("/prompts", response_class=HTMLResponse)
async def prompts_list(
    request: Request,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 10
):
    session_cookie = request.cookies.get("session")
    if not session_cookie:
        return RedirectResponse(url="/login")

    try:
        user_data = serializer.loads(session_cookie)
        username = user_data["username"]

        # Get user
        user_crud = CRUDUser(User)
        user = user_crud.get_by_username(db, username=username)

        if not user:
            return RedirectResponse(url="/login")

        # Get prompts with pagination
        prompt_crud = CRUDPrompt(Prompt)
        prompts = prompt_crud.get_multi_by_owner(db, user_id=user.id, skip=skip, limit=limit)

        # Get total count for pagination
        total_prompts = len(prompt_crud.get_multi_by_owner(db, user_id=user.id, skip=0, limit=10000))

        return templates.TemplateResponse(
            "prompts.html",
            {
                "request": request,
                "username": username,
                "prompts": prompts,
                "skip": skip,
                "limit": limit,
                "total_prompts": total_prompts
            }
        )
    except (BadTimeSignature, SignatureExpired):
        return RedirectResponse(url="/login")

@app.get("/prompts/new", response_class=HTMLResponse)
async def create_prompt_form(request: Request, db: Session = Depends(get_db)):
    session_cookie = request.cookies.get("session")
    if not session_cookie:
        return RedirectResponse(url="/login")

    try:
        user_data = serializer.loads(session_cookie)
        username = user_data["username"]

        return templates.TemplateResponse(
            "prompt_create.html",
            {
                "request": request,
                "username": username
            }
        )
    except (BadTimeSignature, SignatureExpired):
        return RedirectResponse(url="/login")

@app.post("/prompts/new")
async def create_prompt_submit(
    request: Request,
    prompt: str = Form(...),
    response: str = Form(""),
    db: Session = Depends(get_db)
):
    session_cookie = request.cookies.get("session")
    if not session_cookie:
        return RedirectResponse(url="/login")

    try:
        user_data = serializer.loads(session_cookie)
        username = user_data["username"]

        # Get user
        user_crud = CRUDUser(User)
        user = user_crud.get_by_username(db, username=username)

        if not user:
            return RedirectResponse(url="/login")

        # Create prompt
        from app.schemas.prompt import PromptCreate
        prompt_crud = CRUDPrompt(Prompt)
        prompt_data = PromptCreate(prompt=prompt)
        new_prompt = prompt_crud.create_with_owner(db, obj_in=prompt_data, user_id=user.id)

        # Update with response if provided
        if response:
            from app.schemas.prompt import PromptUpdate
            prompt_update = PromptUpdate(response=response)
            prompt_crud.update(db, db_obj=new_prompt, obj_in=prompt_update)

        return RedirectResponse(url=f"/prompts/{new_prompt.id}", status_code=302)

    except (BadTimeSignature, SignatureExpired):
        return RedirectResponse(url="/login")

@app.get("/prompts/{prompt_id}", response_class=HTMLResponse)
async def prompt_detail(
    request: Request,
    prompt_id: int,
    db: Session = Depends(get_db)
):
    session_cookie = request.cookies.get("session")
    if not session_cookie:
        return RedirectResponse(url="/login")

    try:
        user_data = serializer.loads(session_cookie)
        username = user_data["username"]

        # Get user
        user_crud = CRUDUser(User)
        user = user_crud.get_by_username(db, username=username)

        if not user:
            return RedirectResponse(url="/login")

        # Get prompt
        prompt_crud = CRUDPrompt(Prompt)
        prompt = prompt_crud.get(db, id=prompt_id)

        if not prompt or prompt.user_id != user.id:
            return RedirectResponse(url="/prompts")

        return templates.TemplateResponse(
            "prompt_detail.html",
            {
                "request": request,
                "username": username,
                "prompt": prompt
            }
        )
    except (BadTimeSignature, SignatureExpired):
        return RedirectResponse(url="/login")

@app.get("/prompts/{prompt_id}/edit", response_class=HTMLResponse)
async def edit_prompt_form(
    request: Request,
    prompt_id: int,
    db: Session = Depends(get_db)
):
    session_cookie = request.cookies.get("session")
    if not session_cookie:
        return RedirectResponse(url="/login")

    try:
        user_data = serializer.loads(session_cookie)
        username = user_data["username"]

        # Get user
        user_crud = CRUDUser(User)
        user = user_crud.get_by_username(db, username=username)

        if not user:
            return RedirectResponse(url="/login")

        # Get prompt
        prompt_crud = CRUDPrompt(Prompt)
        prompt = prompt_crud.get(db, id=prompt_id)

        if not prompt or prompt.user_id != user.id:
            return RedirectResponse(url="/prompts")

        return templates.TemplateResponse(
            "prompt_edit.html",
            {
                "request": request,
                "username": username,
                "prompt": prompt
            }
        )
    except (BadTimeSignature, SignatureExpired):
        return RedirectResponse(url="/login")

@app.post("/prompts/{prompt_id}/edit")
async def edit_prompt_submit(
    request: Request,
    prompt_id: int,
    prompt: str = Form(...),
    response: str = Form(""),
    db: Session = Depends(get_db)
):
    session_cookie = request.cookies.get("session")
    if not session_cookie:
        return RedirectResponse(url="/login")

    try:
        user_data = serializer.loads(session_cookie)
        username = user_data["username"]

        # Get user
        user_crud = CRUDUser(User)
        user = user_crud.get_by_username(db, username=username)

        if not user:
            return RedirectResponse(url="/login")

        # Get prompt
        prompt_crud = CRUDPrompt(Prompt)
        existing_prompt = prompt_crud.get(db, id=prompt_id)

        if not existing_prompt or existing_prompt.user_id != user.id:
            return RedirectResponse(url="/prompts")

        # Update prompt
        from app.schemas.prompt import PromptUpdate
        prompt_update = PromptUpdate(prompt=prompt, response=response if response else None)
        prompt_crud.update(db, db_obj=existing_prompt, obj_in=prompt_update)

        return RedirectResponse(url=f"/prompts/{prompt_id}", status_code=302)

    except (BadTimeSignature, SignatureExpired):
        return RedirectResponse(url="/login")

@app.post("/prompts/{prompt_id}/delete")
async def delete_prompt(
    request: Request,
    prompt_id: int,
    db: Session = Depends(get_db)
):
    session_cookie = request.cookies.get("session")
    if not session_cookie:
        return RedirectResponse(url="/login")

    try:
        user_data = serializer.loads(session_cookie)
        username = user_data["username"]

        # Get user
        user_crud = CRUDUser(User)
        user = user_crud.get_by_username(db, username=username)

        if not user:
            return RedirectResponse(url="/login")

        # Get and delete prompt
        prompt_crud = CRUDPrompt(Prompt)
        prompt = prompt_crud.get(db, id=prompt_id)

        if prompt and prompt.user_id == user.id:
            prompt_crud.remove(db, id=prompt_id)

        return RedirectResponse(url="/prompts", status_code=302)

    except (BadTimeSignature, SignatureExpired):
        return RedirectResponse(url="/login")

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie(key="session")
    return response

# Initialize the database with sample data
@app.on_event("startup")
async def startup():
    # Add sample data only (tables are created by Alembic)
    from app.models.base import SessionLocal
    from app.services.init_db import init_db
    
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()

# Run the server if this file is executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)