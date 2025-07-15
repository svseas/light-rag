from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """Request for creating a project."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)


class ProjectUpdate(BaseModel):
    """Request for updating a project."""
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)


class Project(BaseModel):
    """Project information."""
    id: UUID
    user_id: str
    name: str
    description: str | None = None
    document_count: int = 0
    created_at: datetime
    updated_at: datetime


class ProjectStats(BaseModel):
    """Project statistics and limits."""
    document_count: int
    max_documents: int = 5
    total_size_mb: float
    max_size_mb: float = 25.0  # 5MB * 5 docs
    can_upload: bool
    remaining_slots: int