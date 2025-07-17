"""Main query processing service coordinating all components."""

import time
import orjson
from uuid import uuid4, UUID
from datetime import datetime
from backend.models.queries import (
    QueryProcessingRequest, QueryProcessingResponse, QueryHistory
)
from backend.agents.query_decomposition import decompose_query
from backend.agents.context_builder import build_context
from backend.agents.answer_synthesis import (
    synthesize_answer, calculate_confidence, extract_sources, format_response_metadata
)
from backend.services.search_service import SearchService
from backend.core.database import get_db_pool


class QueryService:
    """Main service for processing user queries."""
    
    def __init__(self, search_service: SearchService, db_pool):
        self.search_service = search_service
        self.db_pool = db_pool
    
    async def process_query(self, request: QueryProcessingRequest) -> QueryProcessingResponse:
        """Process user query through complete pipeline.
        
        Args:
            request: Query processing request with user input.
            
        Returns:
            QueryProcessingResponse with answer and metadata.
            
        Raises:
            ValueError: If query is invalid.
            Exception: If processing fails.
        """
        start_time = time.time()
        query_id = uuid4()
        
        try:
            # Step 1: Decompose query
            decomposition = await decompose_query(request.query)
            
            # Step 2: Execute search strategies
            if request.document_ids:
                search_results = await self.search_service.search_by_documents(
                    request.query, request.document_ids, request.max_results
                )
            else:
                search_results = await self.search_service.search_all(
                    request.query, request.max_results
                )
            
            # Step 3: Build context
            context = await build_context(request.query, search_results)
            
            # Step 4: Synthesize answer
            answer_response = await synthesize_answer(request.query, context)
            
            # Step 5: Calculate confidence and extract sources
            confidence = calculate_confidence(context, request.query)
            sources = extract_sources(context) if request.include_sources else []
            
            # Step 6: Create response metadata
            processing_time = time.time() - start_time
            metadata = format_response_metadata(request.query, context, confidence)
            metadata.update({
                "decomposition": {
                    "intent": decomposition.intent,
                    "entities": decomposition.entities,
                    "sub_queries": [sq.text for sq in decomposition.sub_queries]
                },
                "search_results": {
                    "keyword_count": len(search_results.keyword_results),
                    "semantic_count": len(search_results.semantic_results),
                    "graph_count": len(search_results.graph_results),
                    "total_count": search_results.total_results
                }
            })
            
            # Step 7: Store query history
            if request.user_id:
                await self._store_query_history(
                    query_id, request, answer_response.answer, metadata
                )
            
            return QueryProcessingResponse(
                id=query_id,
                query=request.query,
                answer=answer_response.answer,
                sources=sources,
                processing_time=processing_time,
                confidence=confidence,
                metadata=metadata,
                created_at=datetime.now()
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            # Store failed query for debugging
            if request.user_id:
                await self._store_query_history(
                    query_id, request, f"Error: {str(e)}", 
                    {"error": str(e), "processing_time": processing_time}
                )
            
            raise Exception(f"Query processing failed: {str(e)}")
    
    async def _store_query_history(self, query_id: UUID, request: QueryProcessingRequest,
                                 response: str, metadata: dict) -> None:
        """Store query and response in history table."""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO query_history (
                    id, user_id, project_id, query_text, response_text, 
                    context_used, metadata, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, 
            query_id, request.user_id, request.project_id, request.query,
            response, orjson.dumps(metadata).decode(), orjson.dumps(metadata).decode(), datetime.now()
            )
    
    async def get_query_history(self, user_id: str, limit: int = 50) -> list[QueryHistory]:
        """Get query history for user.
        
        Args:
            user_id: User identifier.
            limit: Maximum number of queries to return.
            
        Returns:
            List of QueryHistory records.
        """
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, user_id, project_id, query_text, response_text,
                       context_used, metadata, created_at
                FROM query_history
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            """, user_id, limit)
            
            return [
                QueryHistory(
                    id=row["id"],
                    user_id=row["user_id"],
                    project_id=row["project_id"],
                    query_text=row["query_text"],
                    response_text=row["response_text"],
                    context_used=orjson.loads(row["context_used"]) if row["context_used"] else {},
                    metadata=orjson.loads(row["metadata"]) if row["metadata"] else {},
                    created_at=row["created_at"]
                )
                for row in rows
            ]
    
    async def delete_query_history(self, user_id: str, query_id: UUID) -> bool:
        """Delete specific query from history.
        
        Args:
            user_id: User identifier.
            query_id: Query identifier to delete.
            
        Returns:
            True if deleted, False if not found.
        """
        async with self.db_pool.acquire() as conn:
            result = await conn.execute("""
                DELETE FROM query_history
                WHERE id = $1 AND user_id = $2
            """, query_id, user_id)
            
            return result == "DELETE 1"


async def get_query_service() -> QueryService:
    """Get query service instance."""
    from backend.services.search_service import get_search_service
    
    search_service = await get_search_service()
    db_pool = await get_db_pool()
    
    return QueryService(search_service, db_pool)