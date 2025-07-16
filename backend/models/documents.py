from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class DocumentBase(BaseModel):
    """Base document model with common fields."""
    
    name: str = Field(..., min_length=1, max_length=255)
    original_format: str = Field(..., min_length=1, max_length=10)


class DocumentCreate(DocumentBase):
    """Document creation model for upload requests."""
    
    file_path: str = Field(..., min_length=1)
    file_size: int = Field(..., gt=0)
    project_id: UUID | None = None
    
    @field_validator('original_format')
    @classmethod
    def validate_format(cls, v: str) -> str:
        allowed_formats = ['.pdf', '.docx', '.txt', '.md']
        if v not in allowed_formats:
            raise ValueError(f'Format must be one of {allowed_formats}')
        return v


class DocumentProcessing(BaseModel):
    """Document processing status tracking."""
    
    document_id: UUID
    status: str = Field(..., pattern=r'^(pending|processing|completed|failed)$')
    progress: float = Field(0.0, ge=0.0, le=1.0)
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class DocumentMetadata(BaseModel):
    """Document metadata after processing."""
    
    doc_id: UUID
    summary: str | None = None
    recursive_summary: str | None = None
    entity_count: int = 0
    chunk_count: int = 0
    token_count: int = 0
    metadata_json: dict | None = None


class Document(DocumentBase):
    """Full document model with all fields."""
    
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID | None = None
    content_md: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    """Document response model for API responses."""
    
    id: UUID
    name: str
    original_format: str
    content_md: str | None = None
    created_at: datetime
    updated_at: datetime
    metadata: DocumentMetadata | None = None
    processing: DocumentProcessing | None = None


class DocumentList(BaseModel):
    """Paginated document list response."""
    
    documents: list[DocumentResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class DocumentUploadResponse(BaseModel):
    """Response model for document upload."""
    
    document_id: UUID
    message: str
    processing_status: str


class DocumentError(Exception):
    """Document error exception."""
    
    def __init__(
        self, 
        error_type: str, 
        message: str, 
        details: dict | None = None,
        document_id: UUID | None = None
    ):
        self.error_type = error_type
        self.message = message
        self.details = details
        self.document_id = document_id
        super().__init__(message)


class DocumentErrorResponse(BaseModel):
    """Document error response model."""
    
    error_type: str
    message: str
    details: dict | None = None
    document_id: UUID | None = None