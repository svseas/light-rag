import asyncio
from pathlib import Path
from typing import Any

import logfire
from markitdown import MarkItDown
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext

from backend.core.config import get_model_config, get_openai_client, get_settings
from backend.models.documents import DocumentCreate, DocumentError


class DocumentProcessorDeps(BaseModel):
    """Dependencies for document processor agent."""
    
    upload_path: str
    max_file_size: int
    allowed_extensions: str


class DocumentProcessorResult(BaseModel):
    """Result from document processing."""
    
    content_md: str
    metadata: dict[str, Any]
    token_count: int
    processing_time: float


class DocumentProcessorAgent:
    """PydanticAI agent for document processing and conversion."""
    
    def __init__(self) -> None:
        """Initialize the document processor agent."""
        self.settings = get_settings()
        self.model_config = get_model_config()
        self.markitdown = MarkItDown()
        
        # Configure the agent with OpenAI model (uses env vars)
        self.agent = Agent(
            model=f"openai:{self.settings.default_model}",
            result_type=DocumentProcessorResult,
            system_prompt=self._get_system_prompt(),
        )
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for document processing."""
        return """
        You are a document processing agent that helps convert documents 
        to markdown format and extract metadata.
        
        Your responsibilities:
        1. Process the converted markdown content
        2. Extract key metadata like title, author, creation date
        3. Count tokens and estimate processing metrics
        4. Provide structured output for downstream processing
        
        Always provide accurate token counts and meaningful metadata.
        Focus on extracting structured information that will be useful
        for RAG applications.
        """
    
    async def process_document(self, document: DocumentCreate) -> DocumentProcessorResult:
        """Process a document and convert it to markdown.
        
        Args:
            document: Document creation model with file information.
            
        Returns:
            DocumentProcessorResult with processed content and metadata.
            
        Raises:
            DocumentError: If processing fails.
        """
        with logfire.span("document_processor.process_document") as span:
            span.set_attribute("document_name", document.name)
            span.set_attribute("document_format", document.original_format)
            
            try:
                # Validate file
                self._validate_document(document)
                
                # Convert to markdown
                content_md = await self._convert_to_markdown(document.file_path)
                
                # Process with AI agent
                deps = DocumentProcessorDeps(
                    upload_path=self.settings.upload_path,
                    max_file_size=self.settings.max_file_size,
                    allowed_extensions=self.settings.allowed_extensions,
                )
                
                result = await self.agent.run(
                    f"Process this markdown content: {content_md[:1000]}...",
                    deps=deps,
                )
                
                # Update result with actual content
                result.data.content_md = content_md
                
                span.set_attribute("token_count", result.data.token_count)
                span.set_attribute("processing_time", result.data.processing_time)
                
                return result.data
                
            except Exception as e:
                logfire.error(
                    "Document processing failed",
                    document_name=document.name,
                    error=str(e),
                )
                raise DocumentError(
                    error_type="processing_error",
                    message=f"Failed to process document: {str(e)}",
                    details={"document_name": document.name},
                )
    
    def _validate_document(self, document: DocumentCreate) -> None:
        """Validate document before processing.
        
        Args:
            document: Document to validate.
            
        Raises:
            DocumentError: If validation fails.
        """
        # Check file size
        if document.file_size > self.settings.max_file_size:
            raise DocumentError(
                error_type="file_too_large",
                message=f"File size {document.file_size} exceeds maximum {self.settings.max_file_size}",
            )
        
        # Check file extension
        allowed_extensions = self.settings.allowed_extensions.split(",")
        if document.original_format not in allowed_extensions:
            raise DocumentError(
                error_type="unsupported_format",
                message=f"Format {document.original_format} not supported",
            )
        
        # Check file exists
        if not Path(document.file_path).exists():
            raise DocumentError(
                error_type="file_not_found",
                message=f"File not found: {document.file_path}",
            )
    
    async def _convert_to_markdown(self, file_path: str) -> str:
        """Convert document to markdown using markitdown.
        
        Args:
            file_path: Path to the document file.
            
        Returns:
            Markdown content as string.
            
        Raises:
            DocumentError: If conversion fails.
        """
        try:
            # Run markitdown in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.markitdown.convert,
                file_path,
            )
            
            if not result or not result.text_content:
                raise DocumentError(
                    error_type="conversion_failed",
                    message="Failed to extract text content from document",
                )
            
            return result.text_content
            
        except Exception as e:
            raise DocumentError(
                error_type="conversion_error",
                message=f"Document conversion failed: {str(e)}",
            )


# Global instance
document_processor = DocumentProcessorAgent()