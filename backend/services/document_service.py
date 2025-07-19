import asyncio
from pathlib import Path
from uuid import UUID

import asyncpg
import logfire

from backend.agents.document_processor import get_document_processor
from backend.core.config import get_settings
from backend.models.documents import (
    Document,
    DocumentCreate,
    DocumentError,
    DocumentList,
    DocumentProcessing,
    DocumentResponse,
    DocumentUploadResponse,
)


class DocumentService:
    """Service for document management and processing."""
    
    def __init__(self) -> None:
        """Initialize document service."""
        self._processor = None
        self.settings = get_settings()
    
    @property
    def processor(self):
        """Get document processor instance."""
        if self._processor is None:
            self._processor = get_document_processor()
        return self._processor
    
    async def _get_db_connection(self) -> asyncpg.Connection:
        """Get database connection."""
        return await asyncpg.connect(self.settings.database_url)
    
    async def create_document(self, document_data: DocumentCreate) -> DocumentUploadResponse:
        """Create a new document and start processing.
        
        Args:
            document_data: Document creation data.
            
        Returns:
            DocumentUploadResponse with document ID and status.
            
        Raises:
            DocumentError: If document creation fails.
        """
        with logfire.span("document_service.create_document") as span:
            span.set_attribute("document_name", document_data.name)
            
            try:
                document = Document(
                    name=document_data.name,
                    project_id=document_data.project_id,
                    original_format=document_data.original_format,
                )
                
                await self._save_document(document)
                
                asyncio.create_task(
                    self._process_document_async(document, document_data)
                )
                
                return DocumentUploadResponse(
                    document_id=document.id,
                    message=f"Document '{document.name}' uploaded successfully",
                    processing_status="pending",
                )
                
            except Exception as e:
                logfire.error(
                    "Document creation failed",
                    document_name=document_data.name,
                    error=str(e),
                )
                raise DocumentError(
                    error_type="creation_failed",
                    message=f"Failed to create document: {str(e)}",
                )
    
    async def get_document(self, document_id: UUID) -> DocumentResponse:
        """Get document by ID.
        
        Args:
            document_id: Document UUID.
            
        Returns:
            DocumentResponse with document data.
            
        Raises:
            DocumentError: If document not found.
        """
        with logfire.span("document_service.get_document") as span:
            span.set_attribute("document_id", str(document_id))
            
            try:
                document = await self._get_document_by_id(document_id)
                
                return DocumentResponse(
                    id=document.id,
                    name=document.name,
                    original_format=document.original_format,
                    content_md=document.content_md,
                    created_at=document.created_at,
                    updated_at=document.updated_at,
                )
                
            except Exception as e:
                logfire.error(
                    "Document retrieval failed",
                    document_id=str(document_id),
                    error=str(e),
                )
                raise DocumentError(
                    error_type="not_found",
                    message=f"Document {document_id} not found",
                    document_id=document_id,
                )
    
    async def delete_document(self, document_id: UUID) -> None:
        """Delete document by ID.
        
        Args:
            document_id: Document UUID.
            
        Raises:
            DocumentError: If deletion fails.
        """
        with logfire.span("document_service.delete_document") as span:
            span.set_attribute("document_id", str(document_id))
            
            try:
                await self._delete_document_by_id(document_id)
                
                logfire.info(
                    "Document deleted successfully",
                    document_id=str(document_id),
                )
                
            except Exception as e:
                logfire.error(
                    "Document deletion failed",
                    document_id=str(document_id),
                    error=str(e),
                )
                raise DocumentError(
                    error_type="deletion_failed",
                    message=f"Failed to delete document: {str(e)}",
                    document_id=document_id,
                )
    
    async def list_documents(self, page: int, per_page: int) -> DocumentList:
        """List documents with pagination.
        
        Args:
            page: Page number (starts from 1).
            per_page: Number of documents per page.
            
        Returns:
            DocumentList with paginated documents.
            
        Raises:
            DocumentError: If listing fails.
        """
        with logfire.span("document_service.list_documents") as span:
            span.set_attribute("page", page)
            span.set_attribute("per_page", per_page)
            
            try:
                conn = await self._get_db_connection()
                
                # Get total count
                total = await conn.fetchval("SELECT COUNT(*) FROM documents")
                
                # Calculate offset
                offset = (page - 1) * per_page
                
                # Get documents
                rows = await conn.fetch(
                    """
                    SELECT id, name, original_format, content_md, created_at, updated_at
                    FROM documents 
                    ORDER BY created_at DESC
                    LIMIT $1 OFFSET $2
                    """,
                    per_page,
                    offset
                )
                
                await conn.close()
                
                # Convert to response models
                documents = []
                for row in rows:
                    doc_response = DocumentResponse(
                        id=row['id'],
                        name=row['name'],
                        original_format=row['original_format'],
                        content_md=row['content_md'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at'],
                    )
                    documents.append(doc_response)
                
                # Calculate pagination info
                has_next = offset + per_page < total
                has_prev = page > 1
                
                return DocumentList(
                    documents=documents,
                    total=total,
                    page=page,
                    per_page=per_page,
                    has_next=has_next,
                    has_prev=has_prev,
                )
                
            except Exception as e:
                logfire.error(
                    "Document listing failed",
                    page=page,
                    per_page=per_page,
                    error=str(e),
                )
                raise DocumentError(
                    error_type="listing_failed",
                    message=f"Failed to list documents: {str(e)}",
                )
    
    async def get_processing_status(self, document_id: UUID) -> DocumentProcessing:
        """Get document processing status.
        
        Args:
            document_id: Document UUID.
            
        Returns:
            DocumentProcessing with current status.
        """
        with logfire.span("document_service.get_processing_status") as span:
            span.set_attribute("document_id", str(document_id))
            
            conn = await self._get_db_connection()
            try:
                row = await conn.fetchrow(
                    """
                    SELECT document_id, status, progress, error_message, 
                           started_at, completed_at
                    FROM document_processing 
                    WHERE document_id = $1
                    """,
                    document_id
                )
                
                if not row:
                    raise DocumentError(
                        error_type="not_found",
                        message=f"Processing status for document {document_id} not found",
                        document_id=document_id,
                    )
                
                return DocumentProcessing(
                    document_id=row['document_id'],
                    status=row['status'],
                    progress=row['progress'],
                    error_message=row['error_message'],
                    started_at=row['started_at'],
                    completed_at=row['completed_at'],
                )
                
            finally:
                await conn.close()
    
    async def _process_document_async(
        self, 
        document: Document, 
        document_data: DocumentCreate
    ) -> None:
        """Process document asynchronously.
        
        Args:
            document: Document model.
            document_data: Document creation data.
        """
        with logfire.span("document_service._process_document_async") as span:
            span.set_attribute("document_id", str(document.id))
            
            try:
                await self._update_processing_status(
                    document.id, "processing", 0.1
                )
                
                result = await self.processor.process_document(document_data)
                
                document.content_md = result.content_md
                await self._update_document_content(document)
                
                await self._update_processing_status(
                    document.id, "completed", 1.0
                )
                
                logfire.info(
                    "Document processing completed",
                    document_id=str(document.id),
                    token_count=result.token_count,
                    processing_time=result.processing_time,
                )
                
            except Exception as e:
                logfire.error(
                    "Document processing failed",
                    document_id=str(document.id),
                    error=str(e),
                )
                
                await self._update_processing_status(
                    document.id, "failed", 0.0, str(e)
                )
    
    async def _save_document(self, document: Document) -> None:
        """Save document to database.
        
        Args:
            document: Document to save.
        """
        conn = await self._get_db_connection()
        try:
            await conn.execute(
                """
                INSERT INTO documents (id, name, original_format, content_md, project_id, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                document.id,
                document.name,
                document.original_format,
                document.content_md,
                document.project_id,
                document.created_at,
                document.updated_at,
            )
            
            await conn.execute(
                """
                INSERT INTO document_processing (document_id, status, progress, started_at)
                VALUES ($1, $2, $3, $4)
                """,
                document.id,
                "pending",
                0.0,
                document.created_at,
            )
            
        finally:
            await conn.close()
    
    async def _get_document_by_id(self, document_id: UUID) -> Document:
        """Get document from database by ID.
        
        Args:
            document_id: Document UUID.
            
        Returns:
            Document model.
        """
        conn = await self._get_db_connection()
        try:
            row = await conn.fetchrow(
                """
                SELECT id, name, original_format, content_md, created_at, updated_at
                FROM documents 
                WHERE id = $1
                """,
                document_id
            )
            
            if not row:
                raise DocumentError(
                    error_type="not_found",
                    message=f"Document {document_id} not found",
                    document_id=document_id,
                )
            
            return Document(
                id=row['id'],
                name=row['name'],
                original_format=row['original_format'],
                content_md=row['content_md'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
            )
            
        finally:
            await conn.close()
    
    async def _delete_document_by_id(self, document_id: UUID) -> None:
        """Delete document from database by ID.
        
        Args:
            document_id: Document UUID.
        """
        conn = await self._get_db_connection()
        try:
            result = await conn.execute(
                "DELETE FROM documents WHERE id = $1",
                document_id
            )
            
            if result == "DELETE 0":
                raise DocumentError(
                    error_type="not_found",
                    message=f"Document {document_id} not found",
                    document_id=document_id,
                )
            
        finally:
            await conn.close()
    
    async def _update_processing_status(
        self, 
        document_id: UUID, 
        status: str, 
        progress: float, 
        error_message: str | None = None
    ) -> None:
        """Update document processing status.
        
        Args:
            document_id: Document UUID.
            status: Processing status.
            progress: Processing progress (0.0 to 1.0).
            error_message: Error message if status is failed.
        """
        conn = await self._get_db_connection()
        try:
            await conn.execute(
                """
                UPDATE document_processing 
                SET status = $2::text, 
                    progress = $3::float, 
                    error_message = $4::text,
                    completed_at = CASE WHEN $2::text IN ('completed', 'failed') 
                                       THEN NOW() ELSE completed_at END
                WHERE document_id = $1
                """,
                document_id,
                status,
                progress,
                error_message,
            )
            
        finally:
            await conn.close()
    
    async def _update_document_content(self, document: Document) -> None:
        """Update document content in database.
        
        Args:
            document: Document with updated content.
        """
        conn = await self._get_db_connection()
        try:
            await conn.execute(
                """
                UPDATE documents 
                SET content_md = $2, updated_at = $3
                WHERE id = $1
                """,
                document.id,
                document.content_md,
                document.updated_at,
            )
            
        finally:
            await conn.close()
    
    async def count_documents_by_project(self, project_id: UUID) -> int:
        """Count documents in a project.
        
        Args:
            project_id: Project UUID.
            
        Returns:
            Number of documents in the project.
        """
        conn = await self._get_db_connection()
        try:
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM documents WHERE project_id = $1",
                project_id
            )
            return count or 0
        finally:
            await conn.close()
    
    async def list_documents_by_project(
        self, project_id: UUID, page: int = 1, per_page: int = 10
    ) -> DocumentList:
        """List documents for a specific project with pagination.
        
        Args:
            project_id: Project UUID.
            page: Page number (starts from 1).
            per_page: Number of documents per page.
            
        Returns:
            DocumentList with paginated documents.
            
        Raises:
            DocumentError: If listing fails.
        """
        with logfire.span("document_service.list_documents_by_project") as span:
            span.set_attribute("project_id", str(project_id))
            span.set_attribute("page", page)
            span.set_attribute("per_page", per_page)
            
            try:
                conn = await self._get_db_connection()
                
                # Get total count for project
                total = await conn.fetchval(
                    "SELECT COUNT(*) FROM documents WHERE project_id = $1",
                    project_id
                )
                
                # Calculate offset
                offset = (page - 1) * per_page
                
                # Get documents for project
                rows = await conn.fetch(
                    """
                    SELECT id, name, original_format, content_md, created_at, updated_at
                    FROM documents 
                    WHERE project_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2 OFFSET $3
                    """,
                    project_id,
                    per_page,
                    offset
                )
                
                await conn.close()
                
                # Convert to response models
                documents = []
                for row in rows:
                    doc_response = DocumentResponse(
                        id=row['id'],
                        name=row['name'],
                        original_format=row['original_format'],
                        content_md=row['content_md'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at'],
                    )
                    documents.append(doc_response)
                
                total_count = total or 0
                total_pages = (total_count + per_page - 1) // per_page
                
                return DocumentList(
                    documents=documents,
                    total=total_count,
                    page=page,
                    per_page=per_page,
                    has_next=page < total_pages,
                    has_prev=page > 1,
                )
                
            except Exception as e:
                logfire.error(
                    "Error listing documents by project",
                    project_id=str(project_id),
                    error=str(e),
                )
                
                raise DocumentError(
                    error_type="database_error",
                    message=f"Failed to list documents: {str(e)}",
                )


document_service = DocumentService()