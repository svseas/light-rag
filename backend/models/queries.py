"""Query processing models for request/response validation."""

from uuid import UUID
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class QueryType(str, Enum):
    """Types of user queries."""
    FACTUAL = "factual"
    ANALYTICAL = "analytical"
    COMPARATIVE = "comparative"
    SUMMARIZATION = "summarization"
    EXPLORATORY = "exploratory"


class SearchScope(str, Enum):
    """Search scope for query processing."""
    ALL_DOCUMENTS = "all_documents"
    SPECIFIC_DOCUMENTS = "specific_documents"
    ENTITIES = "entities"
    RELATIONSHIPS = "relationships"
    MIXED = "mixed"


class SubQuery(BaseModel):
    """Individual sub-query extracted from complex query."""
    text: str = Field(..., description="Sub-query text")
    type: QueryType = Field(..., description="Type of sub-query")
    entities: list[str] = Field(default=[], description="Entities in sub-query")
    priority: float = Field(default=1.0, description="Priority weight")


class QueryDecomposition(BaseModel):
    """Result of query decomposition analysis."""
    original_query: str = Field(..., description="Original user query")
    intent: QueryType = Field(..., description="Primary query intent")
    sub_queries: list[SubQuery] = Field(default=[], description="Decomposed sub-queries")
    entities: list[str] = Field(default=[], description="Extracted entities")
    temporal_constraints: list[str] = Field(default=[], description="Time-based constraints")
    scope: SearchScope = Field(..., description="Determined search scope")
    confidence: float = Field(default=1.0, description="Decomposition confidence")


class SearchResult(BaseModel):
    """Individual search result."""
    id: str = Field(..., description="Result identifier")
    content: str = Field(..., description="Result content")
    source: str = Field(..., description="Source identifier")
    score: float = Field(..., description="Relevance score")
    metadata: dict = Field(default={}, description="Additional metadata")


class SearchResults(BaseModel):
    """Collection of search results from multiple sources."""
    query: str = Field(..., description="Original query")
    keyword_results: list[SearchResult] = Field(default=[], description="Keyword search results")
    semantic_results: list[SearchResult] = Field(default=[], description="Semantic search results")
    graph_results: list[SearchResult] = Field(default=[], description="Knowledge graph results")
    total_results: int = Field(default=0, description="Total number of results")


class ContextItem(BaseModel):
    """Individual context item for answer generation."""
    content: str = Field(..., description="Context content")
    source: str = Field(..., description="Source document/entity")
    relevance: float = Field(..., description="Relevance score")
    type: str = Field(..., description="Context type (text, entity, relationship)")


class QueryContext(BaseModel):
    """Assembled context for answer generation."""
    query: str = Field(..., description="Original query")
    items: list[ContextItem] = Field(default=[], description="Context items")
    total_tokens: int = Field(default=0, description="Total context tokens")
    sources: list[str] = Field(default=[], description="Source documents")


class QueryResponse(BaseModel):
    """Final response to user query."""
    query: str = Field(..., description="Original query")
    answer: str = Field(..., description="Generated answer")
    sources: list[str] = Field(default=[], description="Source references")
    confidence: float = Field(default=1.0, description="Answer confidence")
    metadata: dict = Field(default={}, description="Additional response metadata")


class QueryProcessingRequest(BaseModel):
    """Request for query processing."""
    query: str = Field(..., min_length=1, description="User query text")
    user_id: UUID | None = Field(None, description="User identifier")
    project_id: UUID | None = Field(None, description="Project context")
    document_ids: list[UUID] | None = Field(None, description="Specific documents to search")
    max_results: int = Field(default=10, description="Maximum results to return")
    include_sources: bool = Field(default=True, description="Include source references")


class QueryProcessingResponse(BaseModel):
    """Response from query processing."""
    id: UUID = Field(..., description="Query processing ID")
    query: str = Field(..., description="Original query")
    answer: str = Field(..., description="Generated answer")
    sources: list[str] = Field(default=[], description="Source references")
    processing_time: float = Field(..., description="Processing time in seconds")
    confidence: float = Field(default=1.0, description="Overall confidence")
    metadata: dict = Field(default={}, description="Processing metadata")
    created_at: datetime = Field(..., description="Response timestamp")


class QueryHistory(BaseModel):
    """Query history record."""
    id: UUID = Field(..., description="Query ID")
    user_id: UUID | None = Field(None, description="User identifier")
    project_id: UUID | None = Field(None, description="Project context")
    query_text: str = Field(..., description="Original query")
    response_text: str = Field(..., description="Generated response")
    context_used: dict = Field(default={}, description="Context metadata")
    metadata: dict = Field(default={}, description="Additional metadata")
    created_at: datetime = Field(..., description="Query timestamp")