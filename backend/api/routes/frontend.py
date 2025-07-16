from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from backend.api.routes.auth import get_current_user
from backend.models.auth import User
from backend.services.project_service import ProjectService
from backend.core.dependencies import get_project_service

router = APIRouter(tags=["frontend"])

# Initialize templates
templates = Jinja2Templates(directory="frontend/templates")

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main app page - redirects to login if not authenticated."""
    # Redirect to login page - let users authenticate first
    return RedirectResponse(url="/login", status_code=302)

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Signup page."""
    return templates.TemplateResponse("signup.html", {"request": request})

@router.get("/verify-email", response_class=HTMLResponse)
async def verify_email_page(request: Request):
    """Email verification page."""
    return templates.TemplateResponse("verify-email.html", {"request": request})

@router.get("/create-project", response_class=HTMLResponse)
async def create_project_page(request: Request):
    """Project creation page."""
    return templates.TemplateResponse("create-project.html", {"request": request})

@router.get("/main", response_class=HTMLResponse)
async def main_page(request: Request):
    """Main app page - requires authentication."""
    return templates.TemplateResponse("main.html", {"request": request})

# Protected route example
@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """User profile page - requires authentication."""
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": current_user
    })