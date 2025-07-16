from pathlib import Path
from uuid import UUID

import logfire
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import JSONResponse

from backend.api.routes.auth import get_current_user
from backend.core.config import get_settings
from backend.core.dependencies import get_project_service
from backend.models.auth import User
from backend.models.documents import (
    DocumentCreate,
    DocumentError,
    DocumentList,
    DocumentProcessing,
    DocumentResponse,
    DocumentUploadResponse,
)
from backend.services.document_service import document_service
from backend.services.project_service import ProjectService

router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
    settings = Depends(get_settings),
):
    """Upload a document for processing.
    
    Args:
        file: The uploaded file.
        settings: Application settings.
        
    Returns:
        DocumentUploadResponse with upload result.
        
    Raises:
        HTTPException: If upload fails.
    """
    with logfire.span("upload_document") as span:
        span.set_attribute("filename", file.filename)
        span.set_attribute("content_type", file.content_type)
        span.set_attribute("user_id", current_user.uid)
        
        # Check if user has a project
        project = await project_service.get_user_project(current_user.uid)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please create a project first"
            )
        
        # Check document limit (5 documents per project)
        document_count = await document_service.count_documents_by_project(project.id)
        if document_count >= 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document limit reached (5 documents per project)"
            )
        
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No filename provided"
            )
        
        # Check file extension
        file_path = Path(file.filename)
        file_extension = file_path.suffix.lower()
        allowed_extensions = settings.allowed_extensions.split(",")
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file_extension} not supported. Allowed: {allowed_extensions}"
            )
        
        # Check file size
        content = await file.read()
        file_size = len(content)
        
        if file_size > settings.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size {file_size} exceeds maximum {settings.max_file_size}"
            )
        
        # Save file to uploads directory
        uploads_dir = Path(settings.upload_path)
        uploads_dir.mkdir(exist_ok=True)
        
        file_save_path = uploads_dir / file.filename
        
        with open(file_save_path, "wb") as f:
            f.write(content)
        
        try:
            # Create document data
            document_data = DocumentCreate(
                name=file.filename,
                original_format=file_extension,
                file_path=str(file_save_path),
                file_size=file_size,
                project_id=project.id,
            )
            
            # Process document
            result = await document_service.create_document(document_data)
            
            span.set_attribute("document_id", str(result.document_id))
            span.set_attribute("processing_status", result.processing_status)
            
            return result
            
        except DocumentError as e:
            # Clean up uploaded file on error
            if file_save_path.exists():
                file_save_path.unlink()
            
            logfire.error(
                "Document upload failed",
                filename=file.filename,
                error=e.message,
                error_type=e.error_type,
            )
            
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=e.message
            )
        
        except Exception as e:
            # Clean up uploaded file on error
            if file_save_path.exists():
                file_save_path.unlink()
            
            logfire.error(
                "Unexpected error during upload",
                filename=file.filename,
                error=str(e),
            )
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during upload"
            )


@router.get("/", response_model=DocumentList)
async def list_documents(
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
):
    """List all documents with pagination.
    
    Args:
        page: Page number (starts from 1).
        per_page: Number of documents per page.
        
    Returns:
        DocumentList with paginated documents.
        
    Raises:
        HTTPException: If listing fails.
    """
    with logfire.span("list_documents") as span:
        span.set_attribute("page", page)
        span.set_attribute("per_page", per_page)
        span.set_attribute("user_id", current_user.uid)
        
        # Get user's project
        project = await project_service.get_user_project(current_user.uid)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please create a project first"
            )
        
        try:
            result = await document_service.list_documents_by_project(project.id, page, per_page)
            return result
            
        except DocumentError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=e.message
            )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: UUID):
    """Get document by ID.
    
    Args:
        document_id: Document UUID.
        
    Returns:
        DocumentResponse with document data.
        
    Raises:
        HTTPException: If document not found.
    """
    with logfire.span("get_document") as span:
        span.set_attribute("document_id", str(document_id))
        
        try:
            result = await document_service.get_document(document_id)
            return result
            
        except DocumentError as e:
            if e.error_type == "not_found":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=e.message
                )
            
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=e.message
            )


@router.get("/{document_id}/processing", response_model=DocumentProcessing)
async def get_processing_status(document_id: UUID):
    """Get document processing status.
    
    Args:
        document_id: Document UUID.
        
    Returns:
        DocumentProcessing with current status.
        
    Raises:
        HTTPException: If document not found.
    """
    with logfire.span("get_processing_status") as span:
        span.set_attribute("document_id", str(document_id))
        
        try:
            result = await document_service.get_processing_status(document_id)
            return result
            
        except DocumentError as e:
            if e.error_type == "not_found":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=e.message
                )
            
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=e.message
            )


@router.delete("/{document_id}")
async def delete_document(document_id: UUID):
    """Delete document by ID.
    
    Args:
        document_id: Document UUID.
        
    Returns:
        Success message.
        
    Raises:
        HTTPException: If deletion fails.
    """
    with logfire.span("delete_document") as span:
        span.set_attribute("document_id", str(document_id))
        
        try:
            await document_service.delete_document(document_id)
            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"message": f"Document {document_id} deleted successfully"}
            )
            
        except DocumentError as e:
            if e.error_type == "not_found":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=e.message
                )
            
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=e.message
            )