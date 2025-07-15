from fastapi import APIRouter, Depends, HTTPException, Header

from backend.core.dependencies import get_auth_service
from backend.models.auth import AuthRequest, AuthResponse, TokenRequest, User
from backend.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["authentication"])


def get_auth_token(authorization: str = Header(None)) -> str:
    """Extract token from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
        return token
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")


async def get_current_user(
    token: str = Depends(get_auth_token),
    service: AuthService = Depends(get_auth_service)
) -> User:
    """Get current authenticated user."""
    token_request = TokenRequest(token=token)
    user = await service.verify_token(token_request)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    return user


@router.post("/signup", response_model=AuthResponse)
async def sign_up(
    request: AuthRequest,
    service: AuthService = Depends(get_auth_service)
) -> AuthResponse:
    """Create new user account."""
    return await service.sign_up(request)


@router.post("/signin", response_model=AuthResponse)
async def sign_in(
    request: AuthRequest,
    service: AuthService = Depends(get_auth_service)
) -> AuthResponse:
    """Sign in user."""
    return await service.sign_in(request)


@router.post("/verify", response_model=User)
async def verify_token(
    request: TokenRequest,
    service: AuthService = Depends(get_auth_service)
) -> User:
    """Verify Firebase ID token."""
    user = await service.verify_token(request)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


@router.get("/profile", response_model=User)
async def get_profile(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user profile."""
    return current_user