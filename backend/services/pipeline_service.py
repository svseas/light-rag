import asyncio
from datetime import datetime
from time import time
from typing import Any
from uuid import UUID

import asyncpg
import logfire

from backend.core.config import get_settings
from backend.models.pipeline import (
    PipelineConfiguration,
    PipelineError,
    PipelineExecution,
    PipelineResponse,
    PipelineStage,
    PipelineStageStatus,
    PipelineStatus,
    PipelineSummary,
)
from backend.services.chunking_service import ChunkingService
from backend.services.document_service import DocumentService
from backend.services.embedding_generation_service import EmbeddingGenerationService
from backend.services.entity_extraction_service import EntityExtractionService
from backend.services.relationship_extraction_service import RelationshipExtractionService


class PipelineService:
    """Service for orchestrating document processing pipeline."""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.settings = get_settings()
        self.active_executions: dict[UUID, PipelineExecution] = {}
        
    async def _get_db_connection(self) -> asyncpg.Connection:
        """Get database connection."""
        return await self.db_pool.acquire()
    
    async def start_pipeline(
        self, 
        document_id: UUID, 
        project_id: UUID,
        config: PipelineConfiguration | None = None
    ) -> PipelineResponse:
        """Start complete document processing pipeline.
        
        Args:
            document_id: Document to process.
            project_id: Project containing the document.
            config: Pipeline configuration.
            
        Returns:
            PipelineResponse with execution details.
        """
        with logfire.span("pipeline_service.start_pipeline") as span:
            span.set_attribute("document_id", str(document_id))
            span.set_attribute("project_id", str(project_id))
            
            # Use default config if none provided
            if config is None:
                config = PipelineConfiguration()
            
            # Create pipeline execution
            execution = PipelineExecution(
                document_id=document_id,
                project_id=project_id,
                config=config.model_dump(),
                started_at=datetime.utcnow()
            )
            
            # Initialize all pipeline stages
            stages = [
                PipelineStageStatus(stage=PipelineStage.DOCUMENT_PROCESSING),
                PipelineStageStatus(stage=PipelineStage.CHUNKING),
                PipelineStageStatus(stage=PipelineStage.EMBEDDING_GENERATION),
                PipelineStageStatus(stage=PipelineStage.ENTITY_EXTRACTION),
                PipelineStageStatus(stage=PipelineStage.RELATIONSHIP_EXTRACTION),
                PipelineStageStatus(stage=PipelineStage.GRAPH_CONSTRUCTION),
            ]
            execution.stages = stages
            
            # Save execution to database
            await self._save_execution(execution)
            
            # Store in active executions
            self.active_executions[execution.id] = execution
            
            # Start processing asynchronously
            asyncio.create_task(self._execute_pipeline(execution, config))
            
            return PipelineResponse(
                execution_id=execution.id,
                document_id=document_id,
                status=PipelineStatus.RUNNING,
                current_stage=PipelineStage.DOCUMENT_PROCESSING,
                overall_progress=0.0,
                message="Pipeline started successfully"
            )
    
    async def _execute_pipeline(
        self, 
        execution: PipelineExecution,
        config: PipelineConfiguration
    ) -> None:
        """Execute the complete pipeline."""
        with logfire.span("pipeline_service._execute_pipeline") as span:
            span.set_attribute("execution_id", str(execution.id))
            
            try:
                execution.status = PipelineStatus.RUNNING
                await self._save_execution(execution)
                
                # Execute stages in sequence
                await self._execute_stage(execution, PipelineStage.DOCUMENT_PROCESSING, config)
                await self._execute_stage(execution, PipelineStage.CHUNKING, config)
                await self._execute_stage(execution, PipelineStage.EMBEDDING_GENERATION, config)
                await self._execute_stage(execution, PipelineStage.ENTITY_EXTRACTION, config)
                await self._execute_stage(execution, PipelineStage.RELATIONSHIP_EXTRACTION, config)
                await self._execute_stage(execution, PipelineStage.GRAPH_CONSTRUCTION, config)
                
                # Mark as completed
                execution.status = PipelineStatus.COMPLETED
                execution.completed_at = datetime.utcnow()
                execution.overall_progress = 1.0
                execution.current_stage = None
                
                # Calculate total processing time
                if execution.started_at and execution.completed_at:
                    execution.total_processing_time = (
                        execution.completed_at - execution.started_at
                    ).total_seconds()
                
                await self._save_execution(execution)
                
                logfire.info(
                    "Pipeline completed successfully",
                    execution_id=str(execution.id),
                    document_id=str(execution.document_id),
                    processing_time=execution.total_processing_time
                )
                
            except Exception as e:
                # Handle pipeline failure
                execution.status = PipelineStatus.FAILED
                execution.error_message = str(e)
                execution.completed_at = datetime.utcnow()
                
                # Determine failed stage
                current_stage = execution.current_stage
                if current_stage:
                    execution.failed_stage = current_stage
                    # Update stage status
                    stage_status = self._get_stage_status(execution, current_stage)
                    if stage_status:
                        stage_status.status = PipelineStatus.FAILED
                        stage_status.error_message = str(e)
                        stage_status.completed_at = datetime.utcnow()
                
                await self._save_execution(execution)
                
                logfire.error(
                    "Pipeline failed",
                    execution_id=str(execution.id),
                    document_id=str(execution.document_id),
                    error=str(e),
                    failed_stage=current_stage
                )
            
            finally:
                # Remove from active executions
                self.active_executions.pop(execution.id, None)
    
    async def _execute_stage(
        self,
        execution: PipelineExecution,
        stage: PipelineStage,
        config: PipelineConfiguration
    ) -> None:
        """Execute a single pipeline stage."""
        with logfire.span(f"pipeline_service._execute_stage.{stage}") as span:
            span.set_attribute("execution_id", str(execution.id))
            span.set_attribute("stage", stage)
            
            # Update execution status
            execution.current_stage = stage
            stage_status = self._get_stage_status(execution, stage)
            
            if stage_status:
                stage_status.status = PipelineStatus.RUNNING
                stage_status.started_at = datetime.utcnow()
            
            await self._save_execution(execution)
            
            # Record start time for metrics
            start_time = time()
            
            try:
                # Execute the specific stage
                await self._execute_stage_logic(execution, stage, config)
                
                # Mark stage as completed
                if stage_status:
                    stage_status.status = PipelineStatus.COMPLETED
                    stage_status.progress = 1.0
                    stage_status.completed_at = datetime.utcnow()
                
                # Update overall progress
                completed_stages = sum(
                    1 for s in execution.stages 
                    if s.status == PipelineStatus.COMPLETED
                )
                execution.overall_progress = completed_stages / len(execution.stages)
                
                # Record timing
                stage_time = time() - start_time
                execution.stage_timings[stage] = stage_time
                
                await self._save_execution(execution)
                
                logfire.info(
                    f"Stage {stage} completed",
                    execution_id=str(execution.id),
                    stage_time=stage_time
                )
                
            except Exception as e:
                # Mark stage as failed
                if stage_status:
                    stage_status.status = PipelineStatus.FAILED
                    stage_status.error_message = str(e)
                    stage_status.completed_at = datetime.utcnow()
                
                await self._save_execution(execution)
                raise PipelineError(
                    f"Stage {stage} failed: {str(e)}",
                    stage=stage,
                    execution_id=execution.id
                )
    
    async def _execute_stage_logic(
        self,
        execution: PipelineExecution,
        stage: PipelineStage,
        config: PipelineConfiguration
    ) -> None:
        """Execute the actual logic for each stage."""
        document_id = execution.document_id
        
        if stage == PipelineStage.DOCUMENT_PROCESSING:
            # Wait for document processing to complete
            from backend.services.document_service import DocumentService
            document_service = DocumentService()
            
            # Poll for document processing completion
            max_retries = 30  # 30 * 2 seconds = 60 seconds max wait
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    doc = await document_service.get_document(document_id)
                    if doc.content_md and doc.content_md.strip():
                        logfire.info(f"Document processing completed for {document_id}")
                        break
                    else:
                        logfire.info(f"Waiting for document processing... (attempt {retry_count + 1})")
                        await asyncio.sleep(2)
                        retry_count += 1
                except Exception as e:
                    logfire.error(f"Error checking document status: {e}")
                    await asyncio.sleep(2)
                    retry_count += 1
            
            if retry_count >= max_retries:
                raise PipelineError("Document processing did not complete within timeout")
                
        elif stage == PipelineStage.CHUNKING:
            # Create chunks from document content
            # Get document content again for chunking stage
            from backend.services.document_service import DocumentService
            from backend.agents.chunking import ChunkingAgent
            document_service = DocumentService()
            doc = await document_service.get_document(document_id)
            chunking_service = ChunkingService(self.db_pool, ChunkingAgent())
            from backend.models.chunks import ChunkingRequest
            request = ChunkingRequest(
                doc_id=document_id,
                chunk_size=1024,
                # No chunk_overlap parameter to trigger SemanticChunker
            )
            await chunking_service.create_chunks_for_document(document_id, doc.content_md, request)
            
        elif stage == PipelineStage.EMBEDDING_GENERATION:
            # Generate embeddings for all chunks
            embedding_service = EmbeddingGenerationService(self.db_pool)
            await embedding_service.generate_embeddings_for_document(document_id)
            
        elif stage == PipelineStage.ENTITY_EXTRACTION:
            # Extract entities from chunks
            from backend.agents.entity_extraction import EntityExtractionAgent
            entity_service = EntityExtractionService(self.db_pool, EntityExtractionAgent())
            await entity_service.extract_entities_for_document(document_id)
            
        elif stage == PipelineStage.RELATIONSHIP_EXTRACTION:
            # Extract relationships from entities
            relationship_service = RelationshipExtractionService(self.db_pool)
            await relationship_service.extract_relationships_for_document_pipeline(document_id)
            
        elif stage == PipelineStage.GRAPH_CONSTRUCTION:
            # This could be where we build additional graph structures
            # For now, relationships are the graph edges
            pass
        
        else:
            raise PipelineError(f"Unknown pipeline stage: {stage}")
    
    def _get_stage_status(
        self, 
        execution: PipelineExecution, 
        stage: PipelineStage
    ) -> PipelineStageStatus | None:
        """Get stage status from execution."""
        for stage_status in execution.stages:
            if stage_status.stage == stage:
                return stage_status
        return None
    
    async def get_execution_status(self, execution_id: UUID) -> PipelineExecution | None:
        """Get current status of pipeline execution."""
        # First check active executions
        if execution_id in self.active_executions:
            return self.active_executions[execution_id]
        
        # Then check database
        conn = await self._get_db_connection()
        try:
            row = await conn.fetchrow(
                "SELECT execution_data FROM pipeline_executions WHERE id = $1",
                execution_id
            )
            if row:
                return PipelineExecution.model_validate_json(row['execution_data'])
            return None
        finally:
            await conn.close()
    
    async def get_executions_by_document(self, document_id: UUID) -> list[PipelineExecution]:
        """Get all pipeline executions for a document."""
        conn = await self._get_db_connection()
        try:
            rows = await conn.fetch(
                """
                SELECT execution_data FROM pipeline_executions 
                WHERE document_id = $1 
                ORDER BY started_at DESC
                """,
                document_id
            )
            return [
                PipelineExecution.model_validate_json(row['execution_data'])
                for row in rows
            ]
        finally:
            await conn.close()
    
    async def get_executions_by_project(self, project_id: UUID) -> list[PipelineExecution]:
        """Get all pipeline executions for a project."""
        conn = await self._get_db_connection()
        try:
            rows = await conn.fetch(
                """
                SELECT execution_data FROM pipeline_executions 
                WHERE project_id = $1 
                ORDER BY started_at DESC
                """,
                project_id
            )
            return [
                PipelineExecution.model_validate_json(row['execution_data'])
                for row in rows
            ]
        finally:
            await conn.close()
    
    async def _save_execution(self, execution: PipelineExecution) -> None:
        """Save pipeline execution to database."""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO pipeline_executions 
                (id, document_id, project_id, status, started_at, completed_at, execution_data)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (id) DO UPDATE SET
                    status = EXCLUDED.status,
                    completed_at = EXCLUDED.completed_at,
                    execution_data = EXCLUDED.execution_data
                """,
                execution.id,
                execution.document_id,
                execution.project_id,
                execution.status,
                execution.started_at,
                execution.completed_at,
                execution.model_dump_json()
            )


