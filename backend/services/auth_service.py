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
                    return AuthResponse(
                        success=False,
                        message=error_data.get("error", {}).get("message", "Sign up failed")
                    )
                
                data = orjson.loads(response.content)
                user = User(
                    uid=data["localId"],
                    email=data["email"],
                    email_verified=data.get("emailVerified", False)
                )
                
                await self._store_user(user)
                
                return AuthResponse(
                    success=True,
                    message="Account created successfully",
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
                user = User(
                    uid=data["localId"],
                    email=data["email"],
                    email_verified=data.get("emailVerified", False)
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