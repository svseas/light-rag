from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from backend.api.routes.auth import get_current_user
from backend.core.dependencies import get_relationship_service, get_project_service
from backend.models.auth import User
from backend.models.relationships import (
    RelationshipExtractionRequest,
    RelationshipExtractionResult,
    RelationshipList,
    RelationshipResponse,
)
from backend.services.relationship_extraction_service import RelationshipExtractionService
from backend.services.project_service import ProjectService

router = APIRouter(prefix="/relationships", tags=["relationships"])


@router.post("/extract", response_model=RelationshipExtractionResult)
async def extract_relationships(
    request: RelationshipExtractionRequest,
    service: RelationshipExtractionService = Depends(get_relationship_service),
) -> RelationshipExtractionResult:
    """Extract relationships from entities in a document."""
    try:
        result = await service.extract_relationships_for_document(request.doc_id, request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract relationships: {str(e)}")


@router.get("/documents/{doc_id}", response_model=RelationshipList)
async def get_relationships_for_document(
    doc_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    service: RelationshipExtractionService = Depends(get_relationship_service),
) -> RelationshipList:
    """Get all relationships for a document with pagination."""
    try:
        return await service.get_relationships_for_document(doc_id, page, per_page)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get relationships: {str(e)}")


@router.get("/entities/{entity_id}", response_model=RelationshipList)
async def get_relationships_for_entity(
    entity_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    service: RelationshipExtractionService = Depends(get_relationship_service),
) -> RelationshipList:
    """Get all relationships for an entity with pagination."""
    try:
        return await service.get_relationships_for_entity(entity_id, page, per_page)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get relationships: {str(e)}")


@router.get("/{relationship_id}", response_model=RelationshipResponse)
async def get_relationship(
    relationship_id: UUID,
    service: RelationshipExtractionService = Depends(get_relationship_service),
) -> RelationshipResponse:
    """Get a specific relationship by ID."""
    try:
        relationship = await service.get_relationship_by_id(relationship_id)
        if not relationship:
            raise HTTPException(status_code=404, detail="Relationship not found")
        return relationship
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get relationship: {str(e)}")


@router.get("/project/{project_id}", response_model=RelationshipList)
async def get_relationships_by_project(
    project_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
    service: RelationshipExtractionService = Depends(get_relationship_service),
) -> RelationshipList:
    """Get all relationships for a project (for knowledge graph visualization)."""
    # Verify user owns the project
    user_project = await project_service.get_user_project(current_user.uid)
    if not user_project or user_project.id != project_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied to project"
        )
    
    # Get relationships for the project
    return await service.get_relationships_by_project(project_id, page, per_page)


@router.delete("/{relationship_id}")
async def delete_relationship(
    relationship_id: UUID,
    service: RelationshipExtractionService = Depends(get_relationship_service),
) -> JSONResponse:
    """Delete a relationship by ID."""
    try:
        deleted = await service.delete_relationship(relationship_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Relationship not found")
        return JSONResponse(content={"message": "Relationship deleted successfully"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete relationship: {str(e)}")