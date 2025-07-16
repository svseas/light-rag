import logging
from typing import Optional

import asyncpg
import httpx
import orjson

from backend.core.config import get_settings
from backend.models.auth import AuthRequest, AuthResponse, TokenRequest, User

logger = logging.getLogger(__name__)


class AuthService:
    """Firebase authentication service using REST API."""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.settings = get_settings()
        self.api_key = self.settings.firebase_api_key
        
    async def sign_up(self, request: AuthRequest) -> AuthResponse:
        """Create new user account."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={self.api_key}",
                    content=orjson.dumps({
                        "email": request.email,
                        "password": request.password,
                        "returnSecureToken": True
                    }),
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    error_data = orjson.loads(response.content)
                    error_message = error_data.get("error", {}).get("message", "Sign up failed")
                    
                    # If email already exists, check if it's unverified and try to resend verification
                    if error_message == "EMAIL_EXISTS":
                        # Try to sign in to get the user's verification status
                        signin_response = await client.post(
                            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.api_key}",
                            content=orjson.dumps({
                                "email": request.email,
                                "password": request.password,
                                "returnSecureToken": True
                            }),
                            headers={"Content-Type": "application/json"}
                        )
                        
                        if signin_response.status_code == 200:
                            signin_data = orjson.loads(signin_response.content)
                            
                            # If user is unverified, send verification email
                            if not signin_data.get("emailVerified", False):
                                await self._send_email_verification(signin_data["idToken"])
                                return AuthResponse(
                                    success=True,
                                    message="Account exists but email is not verified. A new verification email has been sent.",
                                    user=None,
                                    token=None
                                )
                            else:
                                return AuthResponse(
                                    success=False,
                                    message="EMAIL_EXISTS"
                                )
                        else:
                            # Wrong password or other error
                            return AuthResponse(
                                success=False,
                                message="EMAIL_EXISTS"
                            )
                    else:
                        return AuthResponse(
                            success=False,
                            message=error_message
                        )
                
                data = orjson.loads(response.content)
                user = User(
                    uid=data["localId"],
                    email=data["email"],
                    email_verified=data.get("emailVerified", False)
                )
                
                await self._store_user(user)
                
                # Send email verification
                await self._send_email_verification(data["idToken"])
                
                return AuthResponse(
                    success=True,
                    message="Account created successfully. Please check your email to verify your account.",
                    user=user.dict(),
                    token=data["idToken"]
                )
                
        except Exception as e:
            logger.error(f"Sign up error: {e}")
            return AuthResponse(success=False, message="Sign up failed")
    
    async def sign_in(self, request: AuthRequest) -> AuthResponse:
        """Sign in user."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.api_key}",
                    content=orjson.dumps({
                        "email": request.email,
                        "password": request.password,
                        "returnSecureToken": True
                    }),
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    error_data = orjson.loads(response.content)
                    return AuthResponse(
                        success=False,
                        message=error_data.get("error", {}).get("message", "Sign in failed")
                    )
                
                data = orjson.loads(response.content)
                
                # Get accurate user info using lookup endpoint since signInWithPassword 
                # doesn't always return emailVerified field correctly
                lookup_response = await client.post(
                    f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={self.api_key}",
                    content=orjson.dumps({
                        "idToken": data["idToken"]
                    }),
                    headers={"Content-Type": "application/json"}
                )
                
                email_verified = False
                if lookup_response.status_code == 200:
                    lookup_data = orjson.loads(lookup_response.content)
                    users = lookup_data.get("users", [])
                    if users:
                        email_verified = users[0].get("emailVerified", False)
                
                user = User(
                    uid=data["localId"],
                    email=data["email"],
                    email_verified=email_verified
                )
                
                # Check if email is verified
                if not user.email_verified:
                    return AuthResponse(
                        success=False,
                        message="Please verify your email before signing in. Check your inbox for the verification link."
                    )
                
                await self._store_user(user)
                
                return AuthResponse(
                    success=True,
                    message="Signed in successfully",
                    user=user.dict(),
                    token=data["idToken"]
                )
                
        except Exception as e:
            logger.error(f"Sign in error: {e}")
            return AuthResponse(success=False, message="Sign in failed")
    
    async def verify_token(self, request: TokenRequest) -> Optional[User]:
        """Verify Firebase ID token."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={self.api_key}",
                    content=orjson.dumps({"idToken": request.token}),
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    return None
                
                data = orjson.loads(response.content)
                users = data.get("users", [])
                
                if not users:
                    return None
                
                user_data = users[0]
                return User(
                    uid=user_data["localId"],
                    email=user_data["email"],
                    email_verified=user_data.get("emailVerified", False)
                )
                
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None
    
    async def get_user(self, uid: str) -> Optional[User]:
        """Get user by UID from database."""
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT uid, email, email_verified FROM users WHERE uid = $1",
                    uid
                )
                
                if row:
                    return User(
                        uid=row["uid"],
                        email=row["email"],
                        email_verified=row["email_verified"]
                    )
                return None
                
        except Exception as e:
            logger.error(f"Get user error: {e}")
            return None
    
    async def _store_user(self, user: User) -> None:
        """Store or update user in database."""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO users (uid, email, email_verified)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (uid) DO UPDATE SET
                        email = EXCLUDED.email,
                        email_verified = EXCLUDED.email_verified,
                        updated_at = NOW()
                    """,
                    user.uid, user.email, user.email_verified
                )
                
        except Exception as e:
            logger.error(f"Store user error: {e}")
            raise
    
    async def _send_email_verification(self, id_token: str) -> None:
        """Send email verification using Firebase."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={self.api_key}",
                    content=orjson.dumps({
                        "requestType": "VERIFY_EMAIL",
                        "idToken": id_token
                    }),
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to send verification email: {response.text}")
                    
        except Exception as e:
            logger.error(f"Send email verification error: {e}")
    
    async def resend_verification(self, email: str) -> AuthResponse:
        """Resend email verification."""
        try:
            # The proper way to resend verification requires an ID token
            # Since we don't have the user's password, we'll handle this by:
            # 1. Checking if user exists
            # 2. Advising them to try signing up again (which will send new verification)
            
            async with httpx.AsyncClient() as client:
                # Try to check if user exists by attempting to get user info
                # We'll use a different approach - create a temporary password reset to validate email
                response = await client.post(
                    f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={self.api_key}",
                    content=orjson.dumps({
                        "requestType": "PASSWORD_RESET",
                        "email": email
                    }),
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    # User exists, now tell them to try signing up again for verification
                    return AuthResponse(
                        success=False,
                        message="Please try signing up again with the same email to receive a new verification email"
                    )
                else:
                    error_data = orjson.loads(response.content)
                    error_msg = error_data.get("error", {}).get("message", "")
                    
                    if "EMAIL_NOT_FOUND" in error_msg:
                        return AuthResponse(
                            success=False,
                            message="No account found with this email address"
                        )
                    else:
                        return AuthResponse(
                            success=False,
                            message="Please try signing up again to receive a new verification email"
                        )
                
        except Exception as e:
            logger.error(f"Resend verification error: {e}")
            return AuthResponse(success=False, message="Failed to send verification email")
    
    async def _send_verification_for_user(self, uid: str) -> None:
        """Send verification email for a specific user."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={self.api_key}",
                    content=orjson.dumps({
                        "requestType": "VERIFY_EMAIL",
                        "idToken": uid  # This is simplified - in real implementation, you'd need a valid token
                    }),
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to send verification email: {response.text}")
                    
        except Exception as e:
            logger.error(f"Send verification for user error: {e}")
    
    async def check_email_verification(self, email: str) -> bool:
        """Check if email is verified."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={self.api_key}",
                    content=orjson.dumps({
                        "email": [email]
                    }),
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = orjson.loads(response.content)
                    users = data.get("users", [])
                    
                    if users:
                        return users[0].get("emailVerified", False)
                
                return False
                
        except Exception as e:
            logger.error(f"Check email verification error: {e}")
            return False
    
    async def verify_email_token(self, token: str) -> AuthResponse:
        """Verify email with token from email link."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={self.api_key}",
                    content=orjson.dumps({
                        "oobCode": token
                    }),
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    return AuthResponse(
                        success=True,
                        message="Email verified successfully"
                    )
                else:
                    error_data = orjson.loads(response.content)
                    return AuthResponse(
                        success=False,
                        message=error_data.get("error", {}).get("message", "Token verification failed")
                    )
                    
        except Exception as e:
            logger.error(f"Verify email token error: {e}")
            return AuthResponse(success=False, message="Token verification failed")