from fastapi import APIRouter

from backend.api.routes.documents import router as documents_router
from backend.api.routes.chunks import router as chunks_router
from backend.api.routes.entities import router as entities_router
from backend.api.routes.relationships import router as relationships_router
from backend.api.routes.graph import router as graph_router
from backend.api.routes.health import router as health_router

# Main API router
api_router = APIRouter()

# Register route modules
api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
api_router.include_router(chunks_router, tags=["chunks"])
api_router.include_router(entities_router, tags=["entities"])
api_router.include_router(relationships_router, tags=["relationships"])
api_router.include_router(graph_router, tags=["graph"])
api_router.include_router(health_router, tags=["health"])

__all__ = ["api_router"]