import logging
import time
from datetime import datetime
from uuid import UUID

import asyncpg
import logfire

from backend.agents.embedding_generation import EmbeddingGenerationAgent
from backend.models.embeddings import (
    EmbeddingType,
    EmbeddingGenerationRequest,
    EmbeddingGenerationResponse,
    BatchEmbeddingRequest,
    BatchEmbeddingResponse,
    SimilaritySearchRequest,
    SimilaritySearchResponse,
    SimilarityResult,
    SemanticSearchRequest,
    SemanticSearchResponse,
    EmbeddingStats,
    EmbeddingStatsResponse,
)

logger = logging.getLogger(__name__)


class EmbeddingGenerationService:
    """Service for generating and managing embeddings."""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.agent = EmbeddingGenerationAgent()
    
    async def generate_embedding(self, request: EmbeddingGenerationRequest) -> EmbeddingGenerationResponse:
        """Generate embedding for a single content item."""
        start_time = time.time()
        
        async with self.db_pool.acquire() as conn:
            try:
                # Check if embedding exists and skip if not forcing regeneration
                if not request.force_regenerate and await self._has_embedding(conn, request.content_type, request.content_id):
                    return self._create_response(request, False, start_time)
                
                # Get content and generate embedding
                content = await self._get_content_text(conn, request.content_type, request.content_id)
                embedding = await self.agent.generate_embedding(content)
                
                # Store embedding
                await self._store_embedding(conn, request.content_type, request.content_id, embedding)
                
                return self._create_response(request, True, start_time)
                
            except Exception as e:
                logger.error(f"Error generating embedding: {e}")
                return self._create_response(request, False, start_time, str(e))
    
    async def generate_embeddings_batch(self, request: BatchEmbeddingRequest) -> BatchEmbeddingResponse:
        """Generate embeddings for multiple content items."""
        start_time = time.time()
        
        async with self.db_pool.acquire() as conn:
            try:
                # Get items that need embeddings
                items = await self._get_items_for_batch(conn, request)
                
                if not items:
                    return BatchEmbeddingResponse(
                        content_type=request.content_type,
                        total_requested=len(request.content_ids),
                        total_processed=0,
                        total_generated=0,
                        total_skipped=len(request.content_ids),
                        total_failed=0,
                        processing_time=time.time() - start_time,
                        results=[]
                    )
                
                # Generate embeddings in batch
                texts = [item['text'] for item in items]
                embeddings = await self.agent.generate_embeddings_batch(texts)
                
                # Store embeddings
                await self._store_embeddings_batch(conn, request.content_type, items, embeddings)
                
                return BatchEmbeddingResponse(
                    content_type=request.content_type,
                    total_requested=len(request.content_ids),
                    total_processed=len(items),
                    total_generated=len(embeddings),
                    total_skipped=len(request.content_ids) - len(items),
                    total_failed=0,
                    processing_time=time.time() - start_time,
                    results=[]
                )
                
            except Exception as e:
                logger.error(f"Error in batch processing: {e}")
                return BatchEmbeddingResponse(
                    content_type=request.content_type,
                    total_requested=len(request.content_ids),
                    total_processed=0,
                    total_generated=0,
                    total_skipped=0,
                    total_failed=len(request.content_ids),
                    processing_time=time.time() - start_time,
                    results=[]
                )
    
    async def similarity_search(self, request: SimilaritySearchRequest) -> SimilaritySearchResponse:
        """Find similar content items."""
        start_time = time.time()
        
        async with self.db_pool.acquire() as conn:
            try:
                # Get query embedding
                query_embedding = await self._get_embedding(conn, request.content_type, request.content_id)
                if not query_embedding:
                    return SimilaritySearchResponse(
                        query_content_type=request.content_type,
                        query_content_id=request.content_id,
                        total_results=0,
                        results=[],
                        processing_time=time.time() - start_time
                    )
                
                # Search similar items
                results = await self._search_similar(conn, request, query_embedding)
                
                return SimilaritySearchResponse(
                    query_content_type=request.content_type,
                    query_content_id=request.content_id,
                    total_results=len(results),
                    results=results,
                    processing_time=time.time() - start_time
                )
                
            except Exception as e:
                logger.error(f"Error in similarity search: {e}")
                return SimilaritySearchResponse(
                    query_content_type=request.content_type,
                    query_content_id=request.content_id,
                    total_results=0,
                    results=[],
                    processing_time=time.time() - start_time
                )
    
    async def semantic_search(self, request: SemanticSearchRequest) -> SemanticSearchResponse:
        """Search content using query text."""
        start_time = time.time()
        
        try:
            # Generate query embedding
            query_embedding = await self.agent.generate_embedding(request.query)
            
            async with self.db_pool.acquire() as conn:
                results = await self._search_by_text(conn, request, query_embedding)
                
                return SemanticSearchResponse(
                    query=request.query,
                    total_results=len(results),
                    results=results,
                    processing_time=time.time() - start_time
                )
                
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return SemanticSearchResponse(
                query=request.query,
                total_results=0,
                results=[],
                processing_time=time.time() - start_time
            )
    
    async def get_embedding_stats(self) -> EmbeddingStatsResponse:
        """Get embedding statistics."""
        start_time = time.time()
        
        async with self.db_pool.acquire() as conn:
            entity_stats = await conn.fetchrow("SELECT COUNT(*) as total, COUNT(embedding) as with_embeddings FROM entities")
            chunk_stats = await conn.fetchrow("SELECT COUNT(*) as total, COUNT(embedding) as with_embeddings FROM chunks")
            
            stats = EmbeddingStats(
                total_entities=entity_stats['total'],
                entities_with_embeddings=entity_stats['with_embeddings'],
                total_chunks=chunk_stats['total'],
                chunks_with_embeddings=chunk_stats['with_embeddings'],
                embedding_dimension=self.agent.get_embedding_dimension(),
                last_updated=datetime.utcnow()
            )
            
            return EmbeddingStatsResponse(
                stats=stats,
                processing_time=time.time() - start_time
            )
    
    # Helper methods (DRY)
    def _get_table_info(self, content_type: EmbeddingType) -> tuple[str, str]:
        """Get table name and text column for content type."""
        if content_type == EmbeddingType.ENTITY:
            return "entities", "entity_name"
        return "chunks", "content"
    
    async def _has_embedding(self, conn: asyncpg.Connection, content_type: EmbeddingType, content_id: UUID) -> bool:
        """Check if embedding exists."""
        table, _ = self._get_table_info(content_type)
        result = await conn.fetchval(f"SELECT embedding IS NOT NULL FROM {table} WHERE id = $1", content_id)
        return result or False
    
    async def _get_content_text(self, conn: asyncpg.Connection, content_type: EmbeddingType, content_id: UUID) -> str:
        """Get text content for embedding."""
        table, text_column = self._get_table_info(content_type)
        text = await conn.fetchval(f"SELECT {text_column} FROM {table} WHERE id = $1", content_id)
        if not text:
            raise ValueError(f"Content {content_id} not found")
        return text
    
    async def _get_embedding(self, conn: asyncpg.Connection, content_type: EmbeddingType, content_id: UUID) -> list[float] | None:
        """Get existing embedding."""
        table, _ = self._get_table_info(content_type)
        embedding = await conn.fetchval(f"SELECT embedding FROM {table} WHERE id = $1", content_id)
        return embedding
    
    async def _store_embedding(self, conn: asyncpg.Connection, content_type: EmbeddingType, content_id: UUID, embedding: list[float]) -> None:
        """Store embedding in database."""
        table, _ = self._get_table_info(content_type)
        # Convert list to string format for PostgreSQL vector type
        embedding_str = '[' + ','.join(map(str, embedding)) + ']'
        await conn.execute(f"UPDATE {table} SET embedding = $1::vector WHERE id = $2", embedding_str, content_id)
    
    async def _get_items_for_batch(self, conn: asyncpg.Connection, request: BatchEmbeddingRequest) -> list[dict]:
        """Get items needing embeddings for batch processing."""
        table, text_column = self._get_table_info(request.content_type)
        where_clause = "WHERE id = ANY($1)" + ("" if request.force_regenerate else " AND embedding IS NULL")
        query = f"SELECT id, {text_column} as text FROM {table} {where_clause}"
        
        rows = await conn.fetch(query, request.content_ids)
        return [{'id': row['id'], 'text': row['text']} for row in rows]
    
    async def _store_embeddings_batch(self, conn: asyncpg.Connection, content_type: EmbeddingType, items: list[dict], embeddings: list[list[float]]) -> None:
        """Store embeddings in batch."""
        table, _ = self._get_table_info(content_type)
        # Convert embeddings to string format for PostgreSQL vector type
        update_data = [('[' + ','.join(map(str, embedding)) + ']', item['id']) for item, embedding in zip(items, embeddings)]
        await conn.executemany(f"UPDATE {table} SET embedding = $1::vector WHERE id = $2", update_data)
    
    async def _search_similar(self, conn: asyncpg.Connection, request: SimilaritySearchRequest, query_embedding: list[float]) -> list[SimilarityResult]:
        """Search for similar items."""
        table, text_column = self._get_table_info(request.content_type)
        
        # Convert embedding to string format for PostgreSQL
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        
        where_clause = "WHERE embedding IS NOT NULL"
        params = [embedding_str, request.limit]
        
        if request.exclude_self:
            where_clause += " AND id != $3"
            params.append(request.content_id)
        
        query = f"""
            SELECT id, {text_column} as content, 1 - (embedding <-> $1::vector) as similarity
            FROM {table} {where_clause}
            ORDER BY embedding <-> $1::vector
            LIMIT $2
        """
        
        rows = await conn.fetch(query, *params)
        return [self._create_similarity_result(request.content_type, row) for row in rows]
    
    async def _search_by_text(self, conn: asyncpg.Connection, request: SemanticSearchRequest, query_embedding: list[float]) -> list[SimilarityResult]:
        """Search by text query embedding."""
        results = []
        content_types = request.content_types or [EmbeddingType.ENTITY, EmbeddingType.CHUNK]
        
        # Convert embedding to string format for PostgreSQL
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        
        for content_type in content_types:
            table, text_column = self._get_table_info(content_type)
            
            where_clause = "WHERE embedding IS NOT NULL"
            params = [embedding_str]
            
            if request.doc_id:
                where_clause += " AND doc_id = $2"
                params.append(request.doc_id)
            
            query = f"""
                SELECT id, {text_column} as content, 1 - (embedding <-> $1::vector) as similarity
                FROM {table} {where_clause}
                ORDER BY embedding <-> $1::vector
                LIMIT {request.limit}
            """
            
            rows = await conn.fetch(query, *params)
            results.extend([self._create_similarity_result(content_type, row) for row in rows])
        
        # Sort by similarity and limit
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:request.limit]
    
    def _create_response(self, request: EmbeddingGenerationRequest, generated: bool, start_time: float, error: str | None = None) -> EmbeddingGenerationResponse:
        """Create embedding generation response."""
        return EmbeddingGenerationResponse(
            content_type=request.content_type,
            content_id=request.content_id,
            embedding_generated=generated,
            embedding_dimension=self.agent.get_embedding_dimension(),
            processing_time=time.time() - start_time,
            error_message=error
        )
    
    async def generate_embeddings_for_document(self, document_id: UUID) -> None:
        """Generate embeddings for all chunks in a document."""
        async with self.db_pool.acquire() as conn:
            # Get all chunks for the document
            chunks = await conn.fetch(
                "SELECT id FROM chunks WHERE doc_id = $1 ORDER BY chunk_index",
                document_id
            )
            
            logfire.info(f"Generating embeddings for {len(chunks)} chunks in document {document_id}")
            
            for chunk in chunks:
                chunk_id = chunk['id']
                
                # Check if embedding already exists
                if await self._has_embedding(conn, EmbeddingType.CHUNK, chunk_id):
                    continue
                
                # Generate embedding for this chunk
                from backend.models.embeddings import EmbeddingGenerationRequest
                request = EmbeddingGenerationRequest(
                    content_type=EmbeddingType.CHUNK,
                    content_id=chunk_id
                )
                
                await self.generate_embedding(request)

    def _create_similarity_result(self, content_type: EmbeddingType, row: dict) -> SimilarityResult:
        """Create similarity result."""
        content = row['content']
        preview = content[:200] + "..." if len(content) > 200 else content
        
        return SimilarityResult(
            content_type=content_type,
            content_id=row['id'],
            similarity_score=max(0.0, min(1.0, row['similarity'])),
            content_preview=preview
        )