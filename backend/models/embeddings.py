from datetime import datetime
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field


class EmbeddingType(str, Enum):
    """Types of content that can have embeddings."""
    ENTITY = "entity"
    CHUNK = "chunk"


class EmbeddingGenerationRequest(BaseModel):
    """Request model for generating embeddings."""
    content_type: EmbeddingType = Field(..., description="Type of content to generate embedding for")
    content_id: UUID = Field(..., description="ID of the content (entity or chunk)")
    force_regenerate: bool = Field(False, description="Force regeneration even if embedding exists")


class EmbeddingGenerationResponse(BaseModel):
    """Response model for embedding generation."""
    content_type: EmbeddingType = Field(..., description="Type of content processed")
    content_id: UUID = Field(..., description="ID of the content processed")
    embedding_generated: bool = Field(..., description="Whether embedding was generated")
    embedding_dimension: int = Field(..., description="Dimension of the embedding vector")
    processing_time: float = Field(..., description="Time taken to process in seconds")
    error_message: str | None = Field(None, description="Error message if generation failed")


class BatchEmbeddingRequest(BaseModel):
    """Request model for batch embedding generation."""
    content_type: EmbeddingType = Field(..., description="Type of content to generate embeddings for")
    content_ids: list[UUID] = Field(..., min_length=1, max_length=100, description="List of content IDs")
    force_regenerate: bool = Field(False, description="Force regeneration even if embeddings exist")


class BatchEmbeddingResponse(BaseModel):
    """Response model for batch embedding generation."""
    content_type: EmbeddingType = Field(..., description="Type of content processed")
    total_requested: int = Field(..., description="Total number of items requested")
    total_processed: int = Field(..., description="Total number of items processed")
    total_generated: int = Field(..., description="Total number of embeddings generated")
    total_skipped: int = Field(..., description="Total number of items skipped")
    total_failed: int = Field(..., description="Total number of items failed")
    processing_time: float = Field(..., description="Total processing time in seconds")
    results: list[EmbeddingGenerationResponse] = Field(default_factory=list, description="Individual results")


class SimilaritySearchRequest(BaseModel):
    """Request model for similarity search."""
    content_type: EmbeddingType = Field(..., description="Type of content to search")
    content_id: UUID = Field(..., description="ID of the content to find similar items for")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of similar items to return")
    min_similarity: float = Field(0.0, ge=0.0, le=1.0, description="Minimum similarity threshold")
    exclude_self: bool = Field(True, description="Exclude the query item from results")


class SimilarityResult(BaseModel):
    """Individual similarity search result."""
    content_type: EmbeddingType = Field(..., description="Type of similar content")
    content_id: UUID = Field(..., description="ID of the similar content")
    similarity_score: float = Field(..., description="Similarity score (0.0 to 1.0)")
    content_preview: str | None = Field(None, description="Preview of the content")


class SimilaritySearchResponse(BaseModel):
    """Response model for similarity search."""
    query_content_type: EmbeddingType = Field(..., description="Type of query content")
    query_content_id: UUID = Field(..., description="ID of query content")
    total_results: int = Field(..., description="Total number of similar items found")
    results: list[SimilarityResult] = Field(default_factory=list, description="Similar items")
    processing_time: float = Field(..., description="Search processing time in seconds")


class SemanticSearchRequest(BaseModel):
    """Request model for semantic search."""
    query: str = Field(..., min_length=1, max_length=1000, description="Search query text")
    content_types: list[EmbeddingType] | None = Field(None, description="Types of content to search")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results to return")
    min_similarity: float = Field(0.0, ge=0.0, le=1.0, description="Minimum similarity threshold")
    doc_id: UUID | None = Field(None, description="Optional document ID to filter results")


class SemanticSearchResponse(BaseModel):
    """Response model for semantic search."""
    query: str = Field(..., description="Original search query")
    total_results: int = Field(..., description="Total number of results found")
    results: list[SimilarityResult] = Field(default_factory=list, description="Search results")
    processing_time: float = Field(..., description="Search processing time in seconds")


class EmbeddingStats(BaseModel):
    """Statistics about embeddings in the system."""
    total_entities: int = Field(..., description="Total number of entities")
    entities_with_embeddings: int = Field(..., description="Number of entities with embeddings")
    total_chunks: int = Field(..., description="Total number of chunks")
    chunks_with_embeddings: int = Field(..., description="Number of chunks with embeddings")
    embedding_dimension: int = Field(..., description="Dimension of embedding vectors")
    last_updated: datetime | None = Field(None, description="When embeddings were last updated")


class EmbeddingStatsResponse(BaseModel):
    """Response model for embedding statistics."""
    stats: EmbeddingStats = Field(..., description="Embedding statistics")
    processing_time: float = Field(..., description="Time taken to gather stats")