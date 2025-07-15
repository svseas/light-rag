from fastapi import APIRouter

from backend.api.routes.documents import router as documents_router
from backend.api.routes.health import router as health_router

# Main API router
api_router = APIRouter()

# Register route modules
api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
api_router.include_router(health_router, tags=["health"])

__all__ = ["api_router"]