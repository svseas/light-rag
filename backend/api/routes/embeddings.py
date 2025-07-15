from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from backend.core.dependencies import get_embedding_service
from backend.models.embeddings import (
    EmbeddingGenerationRequest,
    EmbeddingGenerationResponse,
    BatchEmbeddingRequest,
    BatchEmbeddingResponse,
    SimilaritySearchRequest,
    SimilaritySearchResponse,
    SemanticSearchRequest,
    SemanticSearchResponse,
    EmbeddingStatsResponse,
    EmbeddingType,
)
from backend.services.embedding_generation_service import EmbeddingGenerationService

router = APIRouter(prefix="/embeddings", tags=["embeddings"])


@router.post("/generate", response_model=EmbeddingGenerationResponse)
async def generate_embedding(
    request: EmbeddingGenerationRequest,
    service: EmbeddingGenerationService = Depends(get_embedding_service),
) -> EmbeddingGenerationResponse:
    """Generate embedding for a single content item."""
    try:
        return await service.generate_embedding(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate embedding: {str(e)}")


@router.post("/generate/batch", response_model=BatchEmbeddingResponse)
async def generate_embeddings_batch(
    request: BatchEmbeddingRequest,
    service: EmbeddingGenerationService = Depends(get_embedding_service),
) -> BatchEmbeddingResponse:
    """Generate embeddings for multiple content items."""
    try:
        return await service.generate_embeddings_batch(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate batch embeddings: {str(e)}")


@router.get("/entities/{entity_id}/generate", response_model=EmbeddingGenerationResponse)
async def generate_entity_embedding(
    entity_id: UUID,
    force_regenerate: bool = Query(False, description="Force regeneration even if embedding exists"),
    service: EmbeddingGenerationService = Depends(get_embedding_service),
) -> EmbeddingGenerationResponse:
    """Generate embedding for a specific entity."""
    try:
        request = EmbeddingGenerationRequest(
            content_type=EmbeddingType.ENTITY,
            content_id=entity_id,
            force_regenerate=force_regenerate
        )
        return await service.generate_embedding(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate entity embedding: {str(e)}")


@router.get("/chunks/{chunk_id}/generate", response_model=EmbeddingGenerationResponse)
async def generate_chunk_embedding(
    chunk_id: UUID,
    force_regenerate: bool = Query(False, description="Force regeneration even if embedding exists"),
    service: EmbeddingGenerationService = Depends(get_embedding_service),
) -> EmbeddingGenerationResponse:
    """Generate embedding for a specific chunk."""
    try:
        request = EmbeddingGenerationRequest(
            content_type=EmbeddingType.CHUNK,
            content_id=chunk_id,
            force_regenerate=force_regenerate
        )
        return await service.generate_embedding(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate chunk embedding: {str(e)}")


@router.post("/similarity", response_model=SimilaritySearchResponse)
async def similarity_search(
    request: SimilaritySearchRequest,
    service: EmbeddingGenerationService = Depends(get_embedding_service),
) -> SimilaritySearchResponse:
    """Find similar content items based on embedding similarity."""
    try:
        return await service.similarity_search(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to perform similarity search: {str(e)}")


@router.get("/entities/{entity_id}/similar", response_model=SimilaritySearchResponse)
async def find_similar_entities(
    entity_id: UUID,
    limit: int = Query(10, ge=1, le=100, description="Maximum number of similar entities to return"),
    min_similarity: float = Query(0.0, ge=0.0, le=1.0, description="Minimum similarity threshold"),
    service: EmbeddingGenerationService = Depends(get_embedding_service),
) -> SimilaritySearchResponse:
    """Find entities similar to the given entity."""
    try:
        request = SimilaritySearchRequest(
            content_type=EmbeddingType.ENTITY,
            content_id=entity_id,
            limit=limit,
            min_similarity=min_similarity,
            exclude_self=True
        )
        return await service.similarity_search(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find similar entities: {str(e)}")


@router.get("/chunks/{chunk_id}/similar", response_model=SimilaritySearchResponse)
async def find_similar_chunks(
    chunk_id: UUID,
    limit: int = Query(10, ge=1, le=100, description="Maximum number of similar chunks to return"),
    min_similarity: float = Query(0.0, ge=0.0, le=1.0, description="Minimum similarity threshold"),
    service: EmbeddingGenerationService = Depends(get_embedding_service),
) -> SimilaritySearchResponse:
    """Find chunks similar to the given chunk."""
    try:
        request = SimilaritySearchRequest(
            content_type=EmbeddingType.CHUNK,
            content_id=chunk_id,
            limit=limit,
            min_similarity=min_similarity,
            exclude_self=True
        )
        return await service.similarity_search(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find similar chunks: {str(e)}")


@router.post("/search", response_model=SemanticSearchResponse)
async def semantic_search(
    request: SemanticSearchRequest,
    service: EmbeddingGenerationService = Depends(get_embedding_service),
) -> SemanticSearchResponse:
    """Perform semantic search using text query."""
    try:
        return await service.semantic_search(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to perform semantic search: {str(e)}")


@router.get("/search", response_model=SemanticSearchResponse)
async def semantic_search_get(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    min_similarity: float = Query(0.0, ge=0.0, le=1.0, description="Minimum similarity threshold"),
    content_types: list[EmbeddingType] = Query(None, description="Content types to search"),
    doc_id: UUID = Query(None, description="Optional document ID filter"),
    service: EmbeddingGenerationService = Depends(get_embedding_service),
) -> SemanticSearchResponse:
    """Perform semantic search using GET request."""
    try:
        request = SemanticSearchRequest(
            query=q,
            limit=limit,
            min_similarity=min_similarity,
            content_types=content_types,
            doc_id=doc_id
        )
        return await service.semantic_search(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to perform semantic search: {str(e)}")


@router.get("/stats", response_model=EmbeddingStatsResponse)
async def get_embedding_stats(
    service: EmbeddingGenerationService = Depends(get_embedding_service),
) -> EmbeddingStatsResponse:
    """Get statistics about embeddings in the system."""
    try:
        return await service.get_embedding_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get embedding stats: {str(e)}")


@router.post("/entities/batch", response_model=BatchEmbeddingResponse)
async def generate_entity_embeddings_batch(
    entity_ids: list[UUID],
    force_regenerate: bool = Query(False, description="Force regeneration even if embeddings exist"),
    service: EmbeddingGenerationService = Depends(get_embedding_service),
) -> BatchEmbeddingResponse:
    """Generate embeddings for multiple entities."""
    try:
        request = BatchEmbeddingRequest(
            content_type=EmbeddingType.ENTITY,
            content_ids=entity_ids,
            force_regenerate=force_regenerate
        )
        return await service.generate_embeddings_batch(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate entity embeddings: {str(e)}")


@router.post("/chunks/batch", response_model=BatchEmbeddingResponse)
async def generate_chunk_embeddings_batch(
    chunk_ids: list[UUID],
    force_regenerate: bool = Query(False, description="Force regeneration even if embeddings exist"),
    service: EmbeddingGenerationService = Depends(get_embedding_service),
) -> BatchEmbeddingResponse:
    """Generate embeddings for multiple chunks."""
    try:
        request = BatchEmbeddingRequest(
            content_type=EmbeddingType.CHUNK,
            content_ids=chunk_ids,
            force_regenerate=force_regenerate
        )
        return await service.generate_embeddings_batch(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate chunk embeddings: {str(e)}")


@router.delete("/entities/{entity_id}")
async def delete_entity_embedding(
    entity_id: UUID,
    service: EmbeddingGenerationService = Depends(get_embedding_service),
) -> JSONResponse:
    """Delete embedding for a specific entity."""
    try:
        # Simple approach - just set embedding to NULL
        async with service.db_pool.acquire() as conn:
            result = await conn.execute("UPDATE entities SET embedding = NULL WHERE id = $1", entity_id)
            if "UPDATE 1" not in result:
                raise HTTPException(status_code=404, detail="Entity not found")
        
        return JSONResponse(content={"message": "Entity embedding deleted successfully"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete entity embedding: {str(e)}")


@router.delete("/chunks/{chunk_id}")
async def delete_chunk_embedding(
    chunk_id: UUID,
    service: EmbeddingGenerationService = Depends(get_embedding_service),
) -> JSONResponse:
    """Delete embedding for a specific chunk."""
    try:
        # Simple approach - just set embedding to NULL
        async with service.db_pool.acquire() as conn:
            result = await conn.execute("UPDATE chunks SET embedding = NULL WHERE id = $1", chunk_id)
            if "UPDATE 1" not in result:
                raise HTTPException(status_code=404, detail="Chunk not found")
        
        return JSONResponse(content={"message": "Chunk embedding deleted successfully"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete chunk embedding: {str(e)}")