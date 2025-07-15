from backend.core.database import get_db_pool
from backend.services.chunking_service import ChunkingService
from backend.services.entity_extraction_service import EntityExtractionService
from backend.services.relationship_extraction_service import RelationshipExtractionService
from backend.services.graph_service import GraphService
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