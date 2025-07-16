from datetime import datetime
from uuid import UUID
import logging

import asyncpg
import orjson
import logfire

from backend.agents.relationship_extraction import RelationshipExtractionAgent
from backend.models.relationships import (
    RelationshipResponse,
    RelationshipList,
    RelationshipExtractionRequest,
    RelationshipExtractionResult,
    RelationshipType,
)
from backend.models.entities import EntityResponse

logger = logging.getLogger(__name__)


class RelationshipExtractionService:
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.agent = RelationshipExtractionAgent()

    async def extract_relationships_for_document(
        self, doc_id: UUID, request: RelationshipExtractionRequest
    ) -> RelationshipExtractionResult:
        """Extract relationships between entities in a document."""
        async with self.db_pool.acquire() as conn:
            # Get entities and document content
            entities = await self._get_entities(conn, doc_id)
            if len(entities) < 2:
                return self._empty_result(len(entities))
            
            content = await self._get_document_content(conn, doc_id)
            
            # Extract relationships using agent
            result = await self.agent.extract_relationships(
                entities=entities,
                context=content,
                relationship_types=request.relationship_types,
                confidence_threshold=request.confidence_threshold
            )
            
            # Store relationships
            if result.relationships:
                await self._store_relationships(conn, result.relationships, doc_id, entities)
            
            return result

    async def get_relationships_for_document(
        self, doc_id: UUID, page: int = 1, per_page: int = 50
    ) -> RelationshipList:
        """Get relationships for a document with pagination."""
        offset = (page - 1) * per_page
        
        async with self.db_pool.acquire() as conn:
            # Get total count
            total = await conn.fetchval(
                "SELECT COUNT(*) FROM relationships WHERE doc_id = $1",
                doc_id
            )
            
            # Get relationships with entity names
            rows = await conn.fetch(
                """
                SELECT r.id, r.source_entity_id, r.target_entity_id, r.relationship_type, 
                       r.confidence, r.weight, r.doc_id, r.created_at,
                       e1.entity_name as source_name, e1.entity_type as source_type,
                       e2.entity_name as target_name, e2.entity_type as target_type
                FROM relationships r
                JOIN entities e1 ON r.source_entity_id = e1.id
                JOIN entities e2 ON r.target_entity_id = e2.id
                WHERE r.doc_id = $1
                ORDER BY r.confidence DESC
                LIMIT $2 OFFSET $3
                """,
                doc_id, per_page, offset
            )
            
            return RelationshipList(
                relationships=[self._create_response(row) for row in rows],
                total=total,
                page=page,
                per_page=per_page,
                has_next=offset + per_page < total
            )

    async def get_relationships_for_entity(
        self, entity_id: UUID, page: int = 1, per_page: int = 50
    ) -> RelationshipList:
        """Get relationships for an entity with pagination."""
        async with self.db_pool.acquire() as conn:
            return await self._get_relationships_paginated(
                conn, 
                "source_entity_id = $1 OR target_entity_id = $1", 
                [entity_id], 
                page, 
                per_page
            )

    async def get_relationship_by_id(self, relationship_id: UUID) -> RelationshipResponse | None:
        """Get a specific relationship by ID."""
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT id, source_entity_id, target_entity_id, relationship_type, 
                       confidence, weight, doc_id, created_at
                FROM relationships WHERE id = $1
            """
            row = await conn.fetchrow(query, relationship_id)
            return self._create_response(row) if row else None

    async def get_relationships_by_project(self, project_id: UUID, page: int = 1, per_page: int = 100) -> RelationshipList:
        """Get all relationships for a project (for knowledge graph visualization)."""
        offset = (page - 1) * per_page
        
        async with self.db_pool.acquire() as conn:
            total_row = await conn.fetchrow(
                """
                SELECT COUNT(*) as total 
                FROM relationships r
                JOIN documents d ON r.doc_id = d.id
                WHERE d.project_id = $1
                """,
                project_id
            )
            
            rows = await conn.fetch(
                """
                SELECT r.id, r.source_entity_id, r.target_entity_id, r.relationship_type, 
                       r.confidence, r.weight, r.doc_id, r.created_at,
                       e1.entity_name as source_name, e1.entity_type as source_type,
                       e2.entity_name as target_name, e2.entity_type as target_type
                FROM relationships r
                JOIN documents d ON r.doc_id = d.id
                JOIN entities e1 ON r.source_entity_id = e1.id
                JOIN entities e2 ON r.target_entity_id = e2.id
                WHERE d.project_id = $1
                ORDER BY r.confidence DESC
                LIMIT $2 OFFSET $3
                """,
                project_id, per_page, offset
            )
            
            total = total_row['total']
            relationships = [self._create_response(row) for row in rows]
            
            return RelationshipList(
                relationships=relationships,
                total=total,
                page=page,
                per_page=per_page,
                has_next=offset + per_page < total
            )

    async def extract_relationships_for_document_pipeline(self, document_id: UUID) -> None:
        """Extract relationships for all entities in a document (pipeline version)."""
        async with self.db_pool.acquire() as conn:
            # Get all entities for the document
            entities = await self._get_entities(conn, document_id)
            
            if len(entities) < 2:
                # Need at least 2 entities to form relationships
                logfire.info(f"Not enough entities ({len(entities)}) to extract relationships for document {document_id}")
                return
            
            # Create extraction request
            from backend.models.relationships import RelationshipExtractionRequest
            request = RelationshipExtractionRequest(
                doc_id=document_id,
                enable_llm_extraction=True
            )
            
            # Use existing extraction logic
            await self.extract_relationships_for_document(document_id, request)

    async def delete_relationship(self, relationship_id: UUID) -> bool:
        """Delete a relationship by ID."""
        async with self.db_pool.acquire() as conn:
            result = await conn.execute("DELETE FROM relationships WHERE id = $1", relationship_id)
            return "DELETE 1" in result

    async def _get_entities(self, conn: asyncpg.Connection, doc_id: UUID) -> list[EntityResponse]:
        """Get all entities for a document."""
        query = """
            SELECT id, entity_name, entity_type, confidence, metadata, doc_id, chunk_id, created_at
            FROM entities WHERE doc_id = $1 ORDER BY confidence DESC
        """
        rows = await conn.fetch(query, doc_id)
        return [self._create_entity_response(row) for row in rows]

    async def _get_document_content(self, conn: asyncpg.Connection, doc_id: UUID) -> str:
        """Get document content for context."""
        content = await conn.fetchval("SELECT content_md FROM documents WHERE id = $1", doc_id)
        return content or ""

    async def _get_relationships_paginated(
        self, conn: asyncpg.Connection, where_clause: str, params: list, page: int, per_page: int
    ) -> RelationshipList:
        """Get relationships with pagination (DRY helper)."""
        offset = (page - 1) * per_page
        
        # Get relationships
        query = f"""
            SELECT id, source_entity_id, target_entity_id, relationship_type, 
                   confidence, weight, doc_id, created_at
            FROM relationships WHERE {where_clause}
            ORDER BY created_at DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}
        """
        rows = await conn.fetch(query, *params, per_page, offset)
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM relationships WHERE {where_clause}"
        total = await conn.fetchval(count_query, *params)
        
        return RelationshipList(
            relationships=[self._create_response(row) for row in rows],
            total=total,
            page=page,
            per_page=per_page,
            has_next=offset + per_page < total
        )

    async def _store_relationships(
        self, conn: asyncpg.Connection, relationships: list, doc_id: UUID, entities: list[EntityResponse]
    ) -> None:
        """Store relationships in database - LLM already provides entity IDs."""
        relationship_data = []
        for rel in relationships:
            # LLM already provides entity IDs, no matching needed!
            relationship_data.append((
                rel.source_entity_id, rel.target_entity_id, rel.relationship_type.value,
                rel.confidence, rel.weight, doc_id, datetime.utcnow()
            ))
        
        if relationship_data:
            query = """
                INSERT INTO relationships 
                (source_entity_id, target_entity_id, relationship_type, confidence, weight, doc_id, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """
            await conn.executemany(query, relationship_data)

    def _empty_result(self, entities_count: int) -> RelationshipExtractionResult:
        """Create empty result (DRY helper)."""
        return RelationshipExtractionResult(
            relationships=[],
            total_relationships=0,
            relationship_types_found=[],
            entities_processed=entities_count
        )

    def _serialize_metadata(self, metadata: dict | None) -> str | None:
        """Serialize metadata using orjson."""
        return orjson.dumps(metadata).decode('utf-8') if metadata else None

    def _parse_metadata(self, metadata_str: str | None) -> dict | None:
        """Parse metadata using orjson."""
        if not metadata_str:
            return None
        try:
            return orjson.loads(metadata_str)
        except (orjson.JSONDecodeError, TypeError):
            logger.warning(f"Failed to parse metadata: {metadata_str}")
            return None

    def _create_response(self, row: asyncpg.Record) -> RelationshipResponse:
        """Create RelationshipResponse from database row (DRY helper)."""
        from backend.models.relationships import EntitySummary
        
        # Create entity summaries if entity names are available
        source_entity = None
        target_entity = None
        
        if 'source_name' in row and row['source_name']:
            source_entity = EntitySummary(
                id=row['source_entity_id'],
                entity_name=row['source_name'],
                entity_type=row['source_type']
            )
        
        if 'target_name' in row and row['target_name']:
            target_entity = EntitySummary(
                id=row['target_entity_id'],
                entity_name=row['target_name'],
                entity_type=row['target_type']
            )
        
        return RelationshipResponse(
            id=row['id'],
            source_entity_id=row['source_entity_id'],
            target_entity_id=row['target_entity_id'],
            relationship_type=RelationshipType(row['relationship_type']),
            confidence=row['confidence'],
            weight=row['weight'],
            metadata=None,  # No metadata in database schema
            doc_id=row['doc_id'],
            created_at=row['created_at'],
            source_entity=source_entity,
            target_entity=target_entity
        )

    def _create_entity_response(self, row: asyncpg.Record) -> EntityResponse:
        """Create EntityResponse from database row."""
        from backend.models.entities import EntityType
        return EntityResponse(
            id=row['id'],
            entity_name=row['entity_name'],
            entity_type=EntityType(row['entity_type']),
            confidence=row['confidence'],
            metadata=self._parse_metadata(row['metadata']),
            doc_id=row['doc_id'],
            chunk_id=row.get('chunk_id'),  # Handle missing chunk_id
            created_at=row['created_at']
        )