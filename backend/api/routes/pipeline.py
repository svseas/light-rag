from uuid import UUID

import logfire
from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.routes.auth import get_current_user
from backend.core.dependencies import get_project_service, get_pipeline_service
from backend.models.auth import User
from backend.models.pipeline import (
    PipelineConfiguration,
    PipelineRequest,
    PipelineResponse,
)
from backend.services.pipeline_service import PipelineService
from backend.services.project_service import ProjectService

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.post("/documents/{document_id}/process", response_model=PipelineResponse)
async def start_document_processing(
    document_id: UUID,
    config: PipelineConfiguration | None = None,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
    pipeline_service: PipelineService = Depends(get_pipeline_service)
) -> PipelineResponse:
    """Start processing pipeline for a document.
    
    Args:
        document_id: Document to process.
        config: Optional pipeline configuration.
        current_user: Authenticated user.
        project_service: Project service dependency.
        
    Returns:
        PipelineResponse with execution details.
        
    Raises:
        HTTPException: If document not found or access denied.
    """
    with logfire.span("start_document_processing") as span:
        span.set_attribute("document_id", str(document_id))
        span.set_attribute("user_id", current_user.uid)
        
        try:
            # Get user's project
            project = await project_service.get_user_project(current_user.uid)
            if not project:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User has no project"
                )
            
            # TODO: Verify document belongs to user's project
            # For now, we'll trust the project_id from the pipeline service
            
            # Start pipeline processing
            response = await pipeline_service.start_pipeline(
                document_id=document_id,
                project_id=project.id,
                config=config
            )
            
            return response
            
        except Exception as e:
            logfire.error(
                "Failed to start document processing",
                document_id=str(document_id),
                error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to start processing: {str(e)}"
            )


@router.get("/{execution_id}/status")
async def get_pipeline_status(
    execution_id: UUID,
    current_user: User = Depends(get_current_user),
    pipeline_service: PipelineService = Depends(get_pipeline_service)
):
    """Get current status of pipeline execution.
    
    Args:
        execution_id: Pipeline execution ID.
        current_user: Authenticated user.
        
    Returns:
        Current pipeline execution status.
        
    Raises:
        HTTPException: If execution not found or access denied.
    """
    with logfire.span("get_pipeline_status") as span:
        span.set_attribute("execution_id", str(execution_id))
        span.set_attribute("user_id", current_user.uid)
        
        try:
            execution = await pipeline_service.get_execution_status(execution_id)
            
            if not execution:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Pipeline execution not found"
                )
            
            # TODO: Verify user has access to this execution
            # For now, we'll return the execution status
            
            return execution
            
        except HTTPException:
            raise
        except Exception as e:
            logfire.error(
                "Failed to get pipeline status",
                execution_id=str(execution_id),
                error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get status: {str(e)}"
            )


@router.get("/project/{project_id}/executions")
async def get_project_executions(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
    pipeline_service: PipelineService = Depends(get_pipeline_service)
):
    """Get all pipeline executions for a project.
    
    Args:
        project_id: Project ID.
        current_user: Authenticated user.
        project_service: Project service dependency.
        
    Returns:
        List of pipeline executions for the project.
        
    Raises:
        HTTPException: If project not found or access denied.
    """
    with logfire.span("get_project_executions") as span:
        span.set_attribute("project_id", str(project_id))
        span.set_attribute("user_id", current_user.uid)
        
        try:
            # Verify user owns the project
            user_project = await project_service.get_user_project(current_user.uid)
            if not user_project or user_project.id != project_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to project"
                )
            
            executions = await pipeline_service.get_executions_by_project(project_id)
            return executions
            
        except HTTPException:
            raise
        except Exception as e:
            logfire.error(
                "Failed to get project executions",
                project_id=str(project_id),
                error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get executions: {str(e)}"
            )