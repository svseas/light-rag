from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ChunkBase(BaseModel):
    content: str = Field(..., description="The text content of the chunk")
    chunk_index: int = Field(..., ge=0, description="The index of this chunk within the document")
    tokens: int | None = Field(None, ge=0, description="Number of tokens in the chunk")


class ChunkCreate(ChunkBase):
    doc_id: UUID = Field(..., description="The ID of the document this chunk belongs to")


class ChunkUpdate(BaseModel):
    content: str | None = Field(None, description="Updated content of the chunk")
    tokens: int | None = Field(None, ge=0, description="Updated token count")


class ChunkResponse(ChunkBase):
    id: UUID = Field(..., description="The unique identifier of the chunk")
    doc_id: UUID = Field(..., description="The ID of the document this chunk belongs to")
    created_at: datetime = Field(..., description="Timestamp when the chunk was created")
    embedding: list[float] | None = Field(None, description="Vector embedding of the chunk")

    class Config:
        from_attributes = True


class ChunkList(BaseModel):
    chunks: list[ChunkResponse]
    total: int = Field(..., ge=0, description="Total number of chunks")
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, description="Number of chunks per page")
    has_next: bool = Field(..., description="Whether there are more chunks available")


class ChunkingRequest(BaseModel):
    doc_id: UUID = Field(..., description="The ID of the document to chunk")
    chunk_size: int | None = Field(512, ge=100, le=4096, description="Maximum tokens per chunk")
    overlap: int | None = Field(50, ge=0, le=200, description="Token overlap between chunks")
    force_rechunk: bool | None = Field(False, description="Force re-chunking even if chunks exist")


class ChunkingStatus(BaseModel):
    doc_id: UUID = Field(..., description="The ID of the document being chunked")
    status: str = Field(..., description="Current chunking status")
    chunks_created: int = Field(..., ge=0, description="Number of chunks created")
    total_tokens: int = Field(..., ge=0, description="Total tokens processed")
    error_message: str | None = Field(None, description="Error message if chunking failed")
    started_at: datetime = Field(..., description="When chunking started")
    completed_at: datetime | None = Field(None, description="When chunking completed")