from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from backend.api.routes.auth import get_current_user
from backend.models.auth import User
from backend.models.entities import (
    EntityResponse, EntityList, EntityExtractionRequest, EntityExtractionStatus, EntityType
)
from backend.services.entity_extraction_service import EntityExtractionService
from backend.services.project_service import ProjectService
from backend.core.dependencies import get_entity_extraction_service, get_project_service

router = APIRouter(prefix="/entities", tags=["entities"])


@router.post("/chunks/{chunk_id}/entities", response_model=EntityExtractionStatus)
async def extract_entities_for_chunk(
    chunk_id: UUID,
    request: EntityExtractionRequest,
    service: EntityExtractionService = Depends(get_entity_extraction_service)
):
    """Extract entities from a chunk."""
    from backend.core.database import get_db_pool
    
    # Get chunk content from database
    db_pool = await get_db_pool()
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT content FROM chunks WHERE id = $1",
            chunk_id
        )
        
        if not row or not row['content']:
            raise HTTPException(status_code=404, detail="Chunk not found or has no content")
        
        chunk_content = row['content']
    
    # Update the request with the correct chunk_id
    request.chunk_id = chunk_id
    
    return await service.extract_entities_for_chunk(chunk_id, chunk_content, request)


@router.get("/chunks/{chunk_id}/entities", response_model=EntityList)
async def get_entities_by_chunk(
    chunk_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    service: EntityExtractionService = Depends(get_entity_extraction_service)
):
    """Get all entities for a chunk with pagination."""
    return await service.get_entities_by_chunk(chunk_id, page, per_page)


@router.get("/documents/{doc_id}/entities", response_model=EntityList)
async def get_entities_by_document(
    doc_id: UUID,
    entity_type: EntityType | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    service: EntityExtractionService = Depends(get_entity_extraction_service)
):
    """Get all entities for a document with optional filtering."""
    return await service.get_entities_by_document(doc_id, entity_type, page, per_page)


@router.get("/{entity_id}", response_model=EntityResponse)
async def get_entity_by_id(
    entity_id: UUID,
    service: EntityExtractionService = Depends(get_entity_extraction_service)
):
    """Get a specific entity by ID."""
    entity = await service.get_entity_by_id(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.delete("/{entity_id}")
async def delete_entity(
    entity_id: UUID,
    service: EntityExtractionService = Depends(get_entity_extraction_service)
):
    """Delete an entity by ID."""
    success = await service.delete_entity(entity_id)
    if not success:
        raise HTTPException(status_code=404, detail="Entity not found")
    return {"message": "Entity deleted successfully"}


@router.get("/project/{project_id}", response_model=EntityList)
async def get_entities_by_project(
    project_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
    service: EntityExtractionService = Depends(get_entity_extraction_service)
):
    """Get all entities for a project (for knowledge graph visualization)."""
    # Verify user owns the project
    user_project = await project_service.get_user_project(current_user.uid)
    if not user_project or user_project.id != project_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied to project"
        )
    
    # Get entities for the project
    return await service.get_entities_by_project(project_id, page, per_page)