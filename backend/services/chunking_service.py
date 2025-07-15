from datetime import datetime
from uuid import UUID
import asyncpg
import logfire

from backend.models.chunks import (
    ChunkCreate, ChunkResponse, ChunkList, ChunkingRequest, ChunkingStatus
)
from backend.agents.chunking import ChunkingAgent


class ChunkingService:
    def __init__(self, db_pool: asyncpg.Pool, chunking_agent: ChunkingAgent):
        self.db_pool = db_pool
        self.chunking_agent = chunking_agent
    
    async def create_chunks_for_document(self, doc_id: UUID, content: str, request: ChunkingRequest) -> ChunkingStatus:
        """Create chunks for a document."""
        started_at = datetime.utcnow()
        
        try:
            with logfire.span("chunking_document", doc_id=str(doc_id)):
                if not request.force_rechunk:
                    existing_chunks = await self.get_chunks_by_document(doc_id)
                    if existing_chunks.total > 0:
                        return ChunkingStatus(
                            doc_id=doc_id,
                            status="already_exists",
                            chunks_created=existing_chunks.total,
                            total_tokens=0,
                            started_at=started_at,
                            completed_at=datetime.utcnow()
                        )
                
                chunk_texts = self.chunking_agent.chunk_document(content, request)
                chunks_created = await self._save_chunks(doc_id, chunk_texts, request.force_rechunk)
                
                return ChunkingStatus(
                    doc_id=doc_id,
                    status="completed",
                    chunks_created=chunks_created,
                    total_tokens=sum(len(chunk.split()) for chunk in chunk_texts),
                    started_at=started_at,
                    completed_at=datetime.utcnow()
                )
        
        except Exception as e:
            logfire.error("Chunking failed", doc_id=str(doc_id), error=str(e))
            return ChunkingStatus(
                doc_id=doc_id,
                status="failed",
                chunks_created=0,
                total_tokens=0,
                error_message=str(e),
                started_at=started_at,
                completed_at=datetime.utcnow()
            )
    
    async def _save_chunks(self, doc_id: UUID, chunk_texts: list[str], force_rechunk: bool) -> int:
        """Save chunks to database."""
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                if force_rechunk:
                    await conn.execute("DELETE FROM chunks WHERE doc_id = $1", doc_id)
                
                chunks_created = 0
                for i, chunk_content in enumerate(chunk_texts):
                    chunk_create = ChunkCreate(
                        doc_id=doc_id,
                        content=chunk_content,
                        chunk_index=i,
                        tokens=len(chunk_content.split())
                    )
                    await self._create_chunk(conn, chunk_create)
                    chunks_created += 1
                
                return chunks_created
    
    async def _create_chunk(self, conn: asyncpg.Connection, chunk_data: ChunkCreate) -> ChunkResponse:
        """Create a single chunk in the database."""
        row = await conn.fetchrow(
            """
            INSERT INTO chunks (doc_id, content, chunk_index, tokens)
            VALUES ($1, $2, $3, $4)
            RETURNING id, doc_id, content, chunk_index, tokens, created_at, embedding
            """,
            chunk_data.doc_id,
            chunk_data.content,
            chunk_data.chunk_index,
            chunk_data.tokens
        )
        
        return ChunkResponse(
            id=row['id'],
            doc_id=row['doc_id'],
            content=row['content'],
            chunk_index=row['chunk_index'],
            tokens=row['tokens'],
            created_at=row['created_at'],
            embedding=row['embedding']
        )
    
    async def get_chunks_by_document(self, doc_id: UUID, page: int = 1, per_page: int = 50) -> ChunkList:
        """Get all chunks for a document with pagination."""
        offset = (page - 1) * per_page
        
        async with self.db_pool.acquire() as conn:
            total_row = await conn.fetchrow(
                "SELECT COUNT(*) as total FROM chunks WHERE doc_id = $1",
                doc_id
            )
            total = total_row['total']
            
            rows = await conn.fetch(
                """
                SELECT id, doc_id, content, chunk_index, tokens, created_at, embedding
                FROM chunks
                WHERE doc_id = $1
                ORDER BY chunk_index
                LIMIT $2 OFFSET $3
                """,
                doc_id, per_page, offset
            )
            
            chunks = [
                ChunkResponse(
                    id=row['id'],
                    doc_id=row['doc_id'],
                    content=row['content'],
                    chunk_index=row['chunk_index'],
                    tokens=row['tokens'],
                    created_at=row['created_at'],
                    embedding=row['embedding']
                )
                for row in rows
            ]
            
            return ChunkList(
                chunks=chunks,
                total=total,
                page=page,
                per_page=per_page,
                has_next=offset + per_page < total
            )
    
    async def get_chunk_by_id(self, chunk_id: UUID) -> ChunkResponse | None:
        """Get a specific chunk by ID."""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, doc_id, content, chunk_index, tokens, created_at, embedding
                FROM chunks
                WHERE id = $1
                """,
                chunk_id
            )
            
            if not row:
                return None
            
            return ChunkResponse(
                id=row['id'],
                doc_id=row['doc_id'],
                content=row['content'],
                chunk_index=row['chunk_index'],
                tokens=row['tokens'],
                created_at=row['created_at'],
                embedding=row['embedding']
            )
    
    async def delete_chunk(self, chunk_id: UUID) -> bool:
        """Delete a chunk by ID."""
        async with self.db_pool.acquire() as conn:
            result = await conn.execute("DELETE FROM chunks WHERE id = $1", chunk_id)
            return result == "DELETE 1"