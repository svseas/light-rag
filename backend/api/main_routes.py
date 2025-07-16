from fastapi import APIRouter

from backend.api.routes.documents import router as documents_router
from backend.api.routes.chunks import router as chunks_router
from backend.api.routes.entities import router as entities_router
from backend.api.routes.relationships import router as relationships_router
from backend.api.routes.graph import router as graph_router
from backend.api.routes.embeddings import router as embeddings_router
from backend.api.routes.auth import router as auth_router
from backend.api.routes.health import router as health_router
from backend.api.routes.projects import router as projects_router
from backend.api.routes.pipeline import router as pipeline_router

# Main API router
api_router = APIRouter()

# Register route modules
api_router.include_router(auth_router, tags=["authentication"])
api_router.include_router(projects_router, tags=["projects"])
api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
api_router.include_router(chunks_router, tags=["chunks"])
api_router.include_router(entities_router, tags=["entities"])
api_router.include_router(relationships_router, tags=["relationships"])
api_router.include_router(graph_router, tags=["graph"])
api_router.include_router(embeddings_router, tags=["embeddings"])
api_router.include_router(pipeline_router, tags=["pipeline"])
api_router.include_router(health_router, tags=["health"])

__all__ = ["api_router"]