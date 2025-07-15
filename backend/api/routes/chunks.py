from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from backend.models.chunks import (
    ChunkResponse, ChunkList, ChunkingRequest, ChunkingStatus
)
from backend.services.chunking_service import ChunkingService
from backend.core.dependencies import get_chunking_service

router = APIRouter(prefix="/chunks", tags=["chunks"])


@router.post("/documents/{doc_id}/chunks", response_model=ChunkingStatus)
async def create_chunks_for_document(
    doc_id: UUID,
    request: ChunkingRequest,
    service: ChunkingService = Depends(get_chunking_service)
):
    """Create chunks for a document."""
    # Get document content from database
    from backend.core.database import get_db_pool
    
    db_pool = await get_db_pool()
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT content_md FROM documents WHERE id = $1",
            doc_id
        )
        
        if not row or not row['content_md']:
            raise HTTPException(status_code=404, detail="Document not found or has no content")
        
        content = row['content_md']
    
    # Update the request with the correct doc_id
    request.doc_id = doc_id
    
    return await service.create_chunks_for_document(doc_id, content, request)


@router.get("/documents/{doc_id}/chunks", response_model=ChunkList)
async def get_chunks_by_document(
    doc_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    service: ChunkingService = Depends(get_chunking_service)
):
    """Get all chunks for a document with pagination."""
    return await service.get_chunks_by_document(doc_id, page, per_page)


@router.get("/{chunk_id}", response_model=ChunkResponse)
async def get_chunk_by_id(
    chunk_id: UUID,
    service: ChunkingService = Depends(get_chunking_service)
):
    """Get a specific chunk by ID."""
    chunk = await service.get_chunk_by_id(chunk_id)
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found")
    return chunk


@router.delete("/{chunk_id}")
async def delete_chunk(
    chunk_id: UUID,
    service: ChunkingService = Depends(get_chunking_service)
):
    """Delete a chunk by ID."""
    success = await service.delete_chunk(chunk_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chunk not found")
    return {"message": "Chunk deleted successfully"}