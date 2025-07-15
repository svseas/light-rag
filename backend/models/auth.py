from pydantic import BaseModel, EmailStr


class AuthRequest(BaseModel):
    """Request for sign-up and sign-in."""
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    """Response for authentication operations."""
    success: bool
    message: str
    user: dict | None = None
    token: str | None = None


class TokenRequest(BaseModel):
    """Request for token validation."""
    token: str


class User(BaseModel):
    """User information."""
    uid: str
    email: str
    email_verified: bool = False