from datetime import datetime
from uuid import UUID
import asyncpg
import logfire
import orjson

from backend.models.entities import (
    EntityCreate, EntityResponse, EntityList, EntityExtractionRequest, 
    EntityExtractionStatus, EntityType
)
from backend.agents.entity_extraction import EntityExtractionAgent


class EntityExtractionService:
    def __init__(self, db_pool: asyncpg.Pool, entity_extraction_agent: EntityExtractionAgent):
        self.db_pool = db_pool
        self.entity_extraction_agent = entity_extraction_agent
    
    def _parse_metadata(self, metadata_raw) -> dict | None:
        """Parse metadata from database format to dict (DRY principle)."""
        if isinstance(metadata_raw, str):
            try:
                return orjson.loads(metadata_raw)
            except (orjson.JSONDecodeError, TypeError):
                return None
        return metadata_raw
    
    def _serialize_metadata(self, metadata: dict | None) -> str | None:
        """Serialize metadata to database format (DRY principle)."""
        return orjson.dumps(metadata).decode() if metadata else None
    
    def _create_entity_response(self, row) -> EntityResponse:
        """Create EntityResponse from database row (DRY principle)."""
        return EntityResponse(
            id=row['id'],
            chunk_id=row['chunk_id'],
            entity_type=EntityType(row['entity_type']),
            entity_name=row['entity_name'],
            confidence=row['confidence'],
            metadata=self._parse_metadata(row['metadata']),
            created_at=row['created_at']
        )
    
    async def extract_entities_for_chunk(self, chunk_id: UUID, chunk_content: str, request: EntityExtractionRequest) -> EntityExtractionStatus:
        """Extract entities from a chunk using the entity extraction agent."""
        started_at = datetime.utcnow()
        
        try:
            with logfire.span("extracting_entities", chunk_id=str(chunk_id)):
                # Check if entities already exist
                if not request.force_reextract:
                    existing_status = await self._check_existing_entities(chunk_id, started_at)
                    if existing_status:
                        return existing_status
                
                # Extract entities
                extraction_result = await self.entity_extraction_agent.extract_entities(
                    chunk_content, request.entity_types, request.confidence_threshold
                )
                
                # Save entities to database
                entities_created = await self._save_entities(chunk_id, extraction_result.entities, request.force_reextract)
                
                return EntityExtractionStatus(
                    chunk_id=chunk_id,
                    status="completed",
                    entities_extracted=entities_created,
                    entity_types_found=extraction_result.entity_types_found,
                    started_at=started_at,
                    completed_at=datetime.utcnow()
                )
        
        except Exception as e:
            logfire.error("Entity extraction failed", chunk_id=str(chunk_id), error=str(e))
            return self._create_error_status(chunk_id, str(e), started_at)
    
    async def _check_existing_entities(self, chunk_id: UUID, started_at: datetime) -> EntityExtractionStatus | None:
        """Check if entities already exist for chunk (KISS principle)."""
        existing_entities = await self.get_entities_by_chunk(chunk_id)
        if existing_entities.total > 0:
            return EntityExtractionStatus(
                chunk_id=chunk_id,
                status="already_exists",
                entities_extracted=existing_entities.total,
                entity_types_found=[entity.entity_type for entity in existing_entities.entities],
                started_at=started_at,
                completed_at=datetime.utcnow()
            )
        return None
    
    async def _save_entities(self, chunk_id: UUID, entities: list, force_reextract: bool) -> int:
        """Save entities to database (KISS principle)."""
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                if force_reextract:
                    await conn.execute("DELETE FROM entities WHERE chunk_id = $1", chunk_id)
                
                entities_created = 0
                for entity_data in entities:
                    entity_create = EntityCreate(
                        chunk_id=chunk_id,
                        entity_type=entity_data.entity_type,
                        entity_name=entity_data.entity_name,
                        confidence=entity_data.confidence,
                        metadata=entity_data.metadata
                    )
                    await self._create_entity(conn, entity_create)
                    entities_created += 1
                
                return entities_created
    
    def _create_error_status(self, chunk_id: UUID, error_message: str, started_at: datetime) -> EntityExtractionStatus:
        """Create error status (KISS principle)."""
        return EntityExtractionStatus(
            chunk_id=chunk_id,
            status="failed",
            entities_extracted=0,
            entity_types_found=[],
            error_message=error_message,
            started_at=started_at,
            completed_at=datetime.utcnow()
        )
    
    async def _create_entity(self, conn: asyncpg.Connection, entity_data: EntityCreate) -> EntityResponse:
        """Create a single entity in the database."""
        # Get doc_id from chunk
        chunk_row = await conn.fetchrow(
            "SELECT doc_id FROM chunks WHERE id = $1",
            entity_data.chunk_id
        )
        
        if not chunk_row:
            raise ValueError(f"Chunk {entity_data.chunk_id} not found")
        
        row = await conn.fetchrow(
            """
            INSERT INTO entities (chunk_id, entity_type, entity_name, confidence, metadata, doc_id)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, chunk_id, entity_type, entity_name, confidence, metadata, created_at
            """,
            entity_data.chunk_id,
            entity_data.entity_type.value,
            entity_data.entity_name,
            entity_data.confidence,
            self._serialize_metadata(entity_data.metadata),
            chunk_row['doc_id']
        )
        
        return self._create_entity_response(row)
    
    async def get_entities_by_chunk(self, chunk_id: UUID, page: int = 1, per_page: int = 50) -> EntityList:
        """Get all entities for a chunk with pagination."""
        offset = (page - 1) * per_page
        
        async with self.db_pool.acquire() as conn:
            total_row = await conn.fetchrow(
                "SELECT COUNT(*) as total FROM entities WHERE chunk_id = $1",
                chunk_id
            )
            total = total_row['total']
            
            rows = await conn.fetch(
                """
                SELECT id, chunk_id, entity_type, entity_name, confidence, metadata, created_at
                FROM entities
                WHERE chunk_id = $1
                ORDER BY confidence DESC, entity_name
                LIMIT $2 OFFSET $3
                """,
                chunk_id, per_page, offset
            )
            
            entities = [self._create_entity_response(row) for row in rows]
            
            return EntityList(
                entities=entities,
                total=total,
                page=page,
                per_page=per_page,
                has_next=offset + per_page < total
            )
    
    async def get_entities_by_document(self, doc_id: UUID, entity_type: EntityType | None = None, page: int = 1, per_page: int = 50) -> EntityList:
        """Get all entities for a document with optional filtering."""
        offset = (page - 1) * per_page
        
        async with self.db_pool.acquire() as conn:
            if entity_type:
                total_row = await conn.fetchrow(
                    "SELECT COUNT(*) as total FROM entities WHERE doc_id = $1 AND entity_type = $2",
                    doc_id, entity_type.value
                )
                rows = await conn.fetch(
                    """
                    SELECT id, chunk_id, entity_type, entity_name, confidence, metadata, created_at
                    FROM entities
                    WHERE doc_id = $1 AND entity_type = $2
                    ORDER BY confidence DESC, entity_name
                    LIMIT $3 OFFSET $4
                    """,
                    doc_id, entity_type.value, per_page, offset
                )
            else:
                total_row = await conn.fetchrow(
                    "SELECT COUNT(*) as total FROM entities WHERE doc_id = $1",
                    doc_id
                )
                rows = await conn.fetch(
                    """
                    SELECT id, chunk_id, entity_type, entity_name, confidence, metadata, created_at
                    FROM entities
                    WHERE doc_id = $1
                    ORDER BY confidence DESC, entity_name
                    LIMIT $2 OFFSET $3
                    """,
                    doc_id, per_page, offset
                )
            
            total = total_row['total']
            
            entities = [self._create_entity_response(row) for row in rows]
            
            return EntityList(
                entities=entities,
                total=total,
                page=page,
                per_page=per_page,
                has_next=offset + per_page < total
            )
    
    async def get_entity_by_id(self, entity_id: UUID) -> EntityResponse | None:
        """Get a specific entity by ID."""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, chunk_id, entity_type, entity_name, confidence, metadata, created_at
                FROM entities
                WHERE id = $1
                """,
                entity_id
            )
            
            if not row:
                return None
            
            return self._create_entity_response(row)
    
    async def get_entities_by_project(self, project_id: UUID, page: int = 1, per_page: int = 100) -> EntityList:
        """Get all entities for a project (for knowledge graph visualization)."""
        offset = (page - 1) * per_page
        
        async with self.db_pool.acquire() as conn:
            total_row = await conn.fetchrow(
                """
                SELECT COUNT(*) as total 
                FROM entities e
                JOIN documents d ON e.doc_id = d.id
                WHERE d.project_id = $1
                """,
                project_id
            )
            
            rows = await conn.fetch(
                """
                SELECT e.id, e.chunk_id, e.entity_type, e.entity_name, e.confidence, e.metadata, e.created_at
                FROM entities e
                JOIN documents d ON e.doc_id = d.id
                WHERE d.project_id = $1
                ORDER BY e.confidence DESC, e.entity_name
                LIMIT $2 OFFSET $3
                """,
                project_id, per_page, offset
            )
            
            total = total_row['total']
            entities = [self._create_entity_response(row) for row in rows]
            
            return EntityList(
                entities=entities,
                total=total,
                page=page,
                per_page=per_page,
                has_next=offset + per_page < total
            )

    async def extract_entities_for_document(self, document_id: UUID) -> None:
        """Extract entities for all chunks in a document."""
        async with self.db_pool.acquire() as conn:
            # Get all chunks for the document
            chunks = await conn.fetch(
                "SELECT id, content FROM chunks WHERE doc_id = $1 ORDER BY chunk_index",
                document_id
            )
            
            for chunk in chunks:
                chunk_id = chunk['id']
                content = chunk['content']
                
                if content and content.strip():
                    # Create extraction request
                    from backend.models.entities import EntityExtractionRequest
                    request = EntityExtractionRequest(
                        chunk_id=chunk_id,
                        enable_llm_extraction=True
                    )
                    
                    # Extract entities for this chunk
                    await self.extract_entities_for_chunk(chunk_id, content, request)

    async def delete_entity(self, entity_id: UUID) -> bool:
        """Delete an entity by ID."""
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM entities WHERE id = $1",
                entity_id
            )
            
            return result == "DELETE 1"