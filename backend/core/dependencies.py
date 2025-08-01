from backend.core.database import get_db_pool
from backend.services.chunking_service import ChunkingService
from backend.services.entity_extraction_service import EntityExtractionService
from backend.services.relationship_extraction_service import RelationshipExtractionService
from backend.services.graph_service import GraphService
from backend.services.embedding_generation_service import EmbeddingGenerationService
from backend.services.auth_service import AuthService
from backend.services.project_service import ProjectService
from backend.services.pipeline_service import PipelineService
from backend.agents.chunking import ChunkingAgent
from backend.agents.entity_extraction import EntityExtractionAgent


async def get_chunking_service() -> ChunkingService:
    """Get chunking service dependency."""
    db_pool = await get_db_pool()
    chunking_agent = ChunkingAgent()
    return ChunkingService(db_pool, chunking_agent)


async def get_entity_extraction_service() -> EntityExtractionService:
    """Get entity extraction service dependency."""
    db_pool = await get_db_pool()
    entity_extraction_agent = EntityExtractionAgent()
    return EntityExtractionService(db_pool, entity_extraction_agent)


async def get_relationship_service() -> RelationshipExtractionService:
    """Get relationship extraction service dependency."""
    db_pool = await get_db_pool()
    return RelationshipExtractionService(db_pool)


async def get_graph_service() -> GraphService:
    """Get graph service dependency."""
    db_pool = await get_db_pool()
    return GraphService(db_pool)


async def get_embedding_service() -> EmbeddingGenerationService:
    """Get embedding generation service dependency."""
    db_pool = await get_db_pool()
    return EmbeddingGenerationService(db_pool)


async def get_auth_service() -> AuthService:
    """Get authentication service dependency."""
    try:
        db_pool = await get_db_pool()
        return AuthService(db_pool)
    except Exception as e:
        import logging
        logging.error(f"Failed to create auth service: {e}")
        # Return a service with None pool - AuthService should handle this
        return AuthService(None)


async def get_project_service() -> ProjectService:
    """Get project service dependency."""
    db_pool = await get_db_pool()
    return ProjectService(db_pool)


async def get_pipeline_service() -> PipelineService:
    """Get pipeline service dependency."""
    db_pool = await get_db_pool()
    return PipelineService(db_pool)