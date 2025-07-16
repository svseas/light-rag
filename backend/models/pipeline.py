from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class PipelineStage(str, Enum):
    """Pipeline processing stages."""
    
    DOCUMENT_PROCESSING = "document_processing"
    CHUNKING = "chunking"
    EMBEDDING_GENERATION = "embedding_generation"
    ENTITY_EXTRACTION = "entity_extraction"
    RELATIONSHIP_EXTRACTION = "relationship_extraction"
    GRAPH_CONSTRUCTION = "graph_construction"


class PipelineStatus(str, Enum):
    """Pipeline execution status."""
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PipelineStageStatus(BaseModel):
    """Status tracking for individual pipeline stages."""
    
    stage: PipelineStage
    status: PipelineStatus = PipelineStatus.PENDING
    progress: float = Field(0.0, ge=0.0, le=1.0)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    result_data: dict | None = None


class PipelineExecution(BaseModel):
    """Top-level pipeline execution tracking."""
    
    id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    project_id: UUID
    status: PipelineStatus = PipelineStatus.PENDING
    current_stage: PipelineStage | None = None
    stages: list[PipelineStageStatus] = Field(default_factory=list)
    
    # Overall progress (0.0 to 1.0)
    overall_progress: float = Field(0.0, ge=0.0, le=1.0)
    
    # Timestamps
    started_at: datetime | None = None
    completed_at: datetime | None = None
    
    # Configuration
    config: dict = Field(default_factory=dict)
    
    # Metrics
    total_processing_time: float | None = None
    stage_timings: dict[str, float] = Field(default_factory=dict)
    
    # Error handling
    error_message: str | None = None
    failed_stage: PipelineStage | None = None
    retry_count: int = 0
    max_retries: int = 3
    
    class Config:
        from_attributes = True


class PipelineConfiguration(BaseModel):
    """Configuration for document processing pipeline."""
    
    # Chunking configuration
    chunk_size: int = 1000
    chunk_overlap: int = 100
    
    # Entity extraction configuration
    entity_confidence_threshold: float = 0.7
    max_entities_per_chunk: int = 50
    
    # Relationship extraction configuration
    relationship_confidence_threshold: float = 0.8
    max_relationships_per_document: int = 200
    
    # Embedding configuration
    embedding_batch_size: int = 10
    
    # Pipeline behavior
    enable_parallel_processing: bool = True
    enable_retry_on_failure: bool = True
    stage_timeout_seconds: int = 300
    
    class Config:
        from_attributes = True


class PipelineRequest(BaseModel):
    """Request model for starting pipeline processing."""
    
    document_id: UUID
    config: PipelineConfiguration | None = None
    priority: int = Field(0, ge=0, le=10)
    force_reprocess: bool = False


class PipelineResponse(BaseModel):
    """Response model for pipeline operations."""
    
    execution_id: UUID
    document_id: UUID
    status: PipelineStatus
    current_stage: PipelineStage | None = None
    overall_progress: float
    message: str
    estimated_completion_time: datetime | None = None


class PipelineSummary(BaseModel):
    """Summary of completed pipeline execution."""
    
    execution_id: UUID
    document_id: UUID
    status: PipelineStatus
    
    # Processing results
    chunks_created: int = 0
    entities_extracted: int = 0
    relationships_extracted: int = 0
    embeddings_generated: int = 0
    
    # Performance metrics
    total_processing_time: float
    stage_timings: dict[str, float]
    
    # Quality metrics
    average_entity_confidence: float | None = None
    average_relationship_confidence: float | None = None
    
    # Timestamps
    started_at: datetime
    completed_at: datetime


class PipelineError(Exception):
    """Pipeline-specific error with stage and retry information."""
    
    def __init__(
        self,
        message: str,
        stage: PipelineStage | None = None,
        execution_id: UUID | None = None,
        retryable: bool = True
    ):
        self.message = message
        self.stage = stage
        self.execution_id = execution_id
        self.retryable = retryable
        super().__init__(message)