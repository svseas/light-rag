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
    request: dict,
    service: AuthService = Depends(get_auth_service)
) -> AuthResponse:
    """Create new user account."""
    auth_request = AuthRequest(email=request["email"], password=request["password"])
    return await service.sign_up(auth_request)


@router.post("/signin", response_model=AuthResponse)
async def sign_in(
    request: dict,
    service: AuthService = Depends(get_auth_service)
) -> AuthResponse:
    """Sign in user."""
    auth_request = AuthRequest(email=request["email"], password=request["password"])
    return await service.sign_in(auth_request)


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


@router.post("/resend-verification", response_model=AuthResponse)
async def resend_verification(
    request: dict,
    service: AuthService = Depends(get_auth_service)
) -> AuthResponse:
    """Resend email verification."""
    email = request.get("email")
    if not email:
        return AuthResponse(success=False, message="Email is required")
    return await service.resend_verification(email)


@router.post("/check-verification", response_model=dict)
async def check_verification(
    request: dict,
    service: AuthService = Depends(get_auth_service)
) -> dict:
    """Check if email is verified."""
    email = request.get("email")
    if not email:
        return {"verified": False, "error": "Email is required"}
    is_verified = await service.check_email_verification(email)
    return {"verified": is_verified}


@router.get("/verify-email-token")
async def verify_email_token(
    token: str,
    service: AuthService = Depends(get_auth_service)
) -> dict:
    """Verify email with token from email link."""
    result = await service.verify_email_token(token)
    if result.success:
        return {"message": "Email verified successfully", "success": True}
    else:
        raise HTTPException(status_code=400, detail=result.message)