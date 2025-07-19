import asyncpg
import logfire
from typing import Optional

from backend.core.config import get_settings

_db_pool: Optional[asyncpg.Pool] = None


async def get_db_pool() -> asyncpg.Pool:
    """Get database connection pool."""
    global _db_pool
    
    if _db_pool is None:
        settings = get_settings()
        
        if not settings.database_url:
            raise RuntimeError("DATABASE_URL not configured")
        
        with logfire.span("creating_db_pool"):
            _db_pool = await asyncpg.create_pool(
                settings.database_url,
                min_size=2,
                max_size=10,
                command_timeout=60,
            )
            logfire.info("Database pool created", pool_size=_db_pool.get_size())
    
    return _db_pool


async def close_db_pool() -> None:
    """Close database connection pool."""
    global _db_pool
    
    if _db_pool:
        await _db_pool.close()
        _db_pool = None
        logfire.info("Database pool closed")


async def init_db_pool() -> None:
    """Initialize database pool on startup."""
    await get_db_pool()


async def get_db_connection() -> asyncpg.Connection:
    """Get a single database connection from the pool."""
    pool = await get_db_pool()
    return await pool.acquire()