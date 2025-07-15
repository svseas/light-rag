from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from backend.api.routes.auth import get_current_user
from backend.core.dependencies import get_project_service
from backend.models.auth import User
from backend.models.projects import Project, ProjectCreate, ProjectUpdate, ProjectStats
from backend.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=Project)
async def create_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service)
) -> Project:
    """Create new project for user."""
    try:
        return await service.create_project(current_user.uid, data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/me", response_model=Project)
async def get_my_project(
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service)
) -> Project:
    """Get current user's project."""
    project = await service.get_user_project(current_user.uid)
    if not project:
        raise HTTPException(status_code=404, detail="No project found")
    return project


@router.put("/{project_id}", response_model=Project)
async def update_project(
    project_id: UUID,
    data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service)
) -> Project:
    """Update project."""
    try:
        return await service.update_project(project_id, current_user.uid, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{project_id}")
async def delete_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service)
) -> dict:
    """Delete project."""
    success = await service.delete_project(project_id, current_user.uid)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project deleted successfully"}


@router.get("/{project_id}/stats", response_model=ProjectStats)
async def get_project_stats(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service)
) -> ProjectStats:
    """Get project statistics."""
    try:
        return await service.get_project_stats(project_id, current_user.uid)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))