import logging
from uuid import UUID

import asyncpg

from backend.models.projects import Project, ProjectCreate, ProjectUpdate, ProjectStats

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for managing user projects."""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.max_documents = 5
        self.max_size_mb = 5
    
    async def create_project(self, user_id: str, data: ProjectCreate) -> Project:
        """Create project for user."""
        if await self._user_has_project(user_id):
            raise ValueError("User already has a project")
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO projects (user_id, name, description)
                VALUES ($1, $2, $3)
                RETURNING *
                """,
                user_id, data.name, data.description
            )
            return self._row_to_project(row)
    
    async def get_user_project(self, user_id: str) -> Project | None:
        """Get user's project."""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM projects WHERE user_id = $1", user_id
            )
            if not row:
                return None
            
            project = self._row_to_project(row)
            project.document_count = await self._get_document_count(project.id)
            return project
    
    async def update_project(self, project_id: UUID, user_id: str, data: ProjectUpdate) -> Project:
        """Update project."""
        await self._verify_ownership(project_id, user_id)
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE projects 
                SET name = COALESCE($3, name),
                    description = COALESCE($4, description),
                    updated_at = NOW()
                WHERE id = $1 AND user_id = $2
                RETURNING *
                """,
                project_id, user_id, data.name, data.description
            )
            
            project = self._row_to_project(row)
            project.document_count = await self._get_document_count(project_id)
            return project
    
    async def delete_project(self, project_id: UUID, user_id: str) -> bool:
        """Delete project."""
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM projects WHERE id = $1 AND user_id = $2",
                project_id, user_id
            )
            return "DELETE 1" in result
    
    async def get_project_stats(self, project_id: UUID, user_id: str) -> ProjectStats:
        """Get project statistics."""
        await self._verify_ownership(project_id, user_id)
        
        async with self.db_pool.acquire() as conn:
            stats = await conn.fetchrow(
                """
                SELECT COUNT(*) as count,
                       COALESCE(SUM(LENGTH(content_md)), 0) as size
                FROM documents WHERE project_id = $1
                """,
                project_id
            )
            
            document_count = stats["count"]
            total_size_mb = round(stats["size"] / (1024 * 1024), 2)
            remaining_slots = max(0, self.max_documents - document_count)
            
            return ProjectStats(
                document_count=document_count,
                max_documents=self.max_documents,
                total_size_mb=total_size_mb,
                max_size_mb=self.max_documents * self.max_size_mb,
                can_upload=remaining_slots > 0,
                remaining_slots=remaining_slots
            )
    
    async def can_upload_documents(self, project_id: UUID, user_id: str, count: int = 1) -> bool:
        """Check if can upload documents."""
        stats = await self.get_project_stats(project_id, user_id)
        return stats.remaining_slots >= count
    
    async def _user_has_project(self, user_id: str) -> bool:
        """Check if user has project."""
        async with self.db_pool.acquire() as conn:
            return bool(await conn.fetchval(
                "SELECT 1 FROM projects WHERE user_id = $1", user_id
            ))
    
    async def _verify_ownership(self, project_id: UUID, user_id: str) -> None:
        """Verify user owns project."""
        async with self.db_pool.acquire() as conn:
            exists = await conn.fetchval(
                "SELECT 1 FROM projects WHERE id = $1 AND user_id = $2",
                project_id, user_id
            )
            if not exists:
                raise ValueError("Project not found")
    
    async def _get_document_count(self, project_id: UUID) -> int:
        """Get document count for project."""
        async with self.db_pool.acquire() as conn:
            return await conn.fetchval(
                "SELECT COUNT(*) FROM documents WHERE project_id = $1", project_id
            )
    
    def _row_to_project(self, row) -> Project:
        """Convert database row to Project model."""
        return Project(
            id=row["id"],
            user_id=row["user_id"],
            name=row["name"],
            description=row["description"],
            document_count=0,  # Set separately when needed
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )