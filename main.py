# app/main.py
from fastapi import FastAPI, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from itsdangerous import URLSafeSerializer, BadTimeSignature, SignatureExpired

from app.api.v1.router import api_router
from app.config import settings
from app.models.base import Base, engine

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
            return RedirectResponse(url="/profile")
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
async def handle_login(request: Request, username: str = Form(...), password: str = Form(...)):
    # Dummy user validation
    if username == username and password == password:
        session_data = {"username": username}
        session_cookie = serializer.dumps(session_data)
        response = RedirectResponse(url="/profile", status_code=302)
        response.set_cookie(key="session", value=session_cookie, httponly=True)
        return response
    else:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid username or password"})

@app.get("/profile", response_class=HTMLResponse)
async def profile(request: Request):
    session_cookie = request.cookies.get("session")
    if not session_cookie:
        return RedirectResponse(url="/login")
    try:
        user_data = serializer.loads(session_cookie)
        return templates.TemplateResponse("profile.html", {"request": request, "username": user_data["username"]})
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