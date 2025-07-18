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
from backend.agents.adaptive_context_analyzer import adaptive_context_analyzer
from backend.services.search_service import SearchService
from backend.services.reranking_service import RerankingService
from backend.services.query_expansion_service import get_query_expansion_service
from backend.services.conversation_context_service import conversation_context_service
from backend.core.database import get_db_pool


class QueryService:
    """Main service for processing user queries."""
    
    def __init__(self, search_service: SearchService, db_pool):
        self.search_service = search_service
        self.db_pool = db_pool
        self.reranking_service = RerankingService()
        self.query_expansion_service = None
    
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
            # Step 1: Get conversation context
            conversation_context = None
            if request.user_id:
                recent_history = await self.get_query_history(request.user_id, limit=5)
                conversation_context = conversation_context_service.extract_context_from_history(recent_history)
            
            # Step 2: Expand query with conversation context
            original_query = request.query
            if conversation_context and conversation_context.recent_queries:
                expanded_query = conversation_context_service.expand_query_with_context(
                    request.query, conversation_context
                )
                # Use expanded query for processing
                request.query = expanded_query
            
            # Step 3: Initialize query expansion service
            if self.query_expansion_service is None:
                self.query_expansion_service = await get_query_expansion_service(self.db_pool)
            
            # Step 4: Expand query with content awareness
            expansions = await self.query_expansion_service.expand_query(
                request.query, request.project_id, request.document_ids
            )
            
            # Step 5: Calculate optimal k values
            k_values = self.query_expansion_service.calculate_optimal_k(request.query, expansions)
            
            # Step 6: Decompose query
            decomposition = await decompose_query(request.query)
            
            # Step 7: Analyze query complexity for adaptive context window
            context_recommendation = await adaptive_context_analyzer.analyze_query(
                request.query, decomposition
            )
            
            # Step 8: Execute search strategies with optimized k values
            if request.document_ids:
                search_results = await self.search_service.search_by_documents(
                    request.query, request.document_ids, k_values.get("keyword_k", 50)
                )
            else:
                search_results = await self.search_service.search_all(
                    request.query, k_values
                )
            
            # Step 9: Rerank using RRF + Cross-encoder (get more results for context building)
            reranked_results = self.reranking_service.process_results(
                request.query,
                search_results.keyword_results,
                search_results.semantic_results,
                search_results.graph_results,
                final_k=k_values.get("final_k", 20)  # Increased from 5 to 20 for better context
            )
            
            # Step 10: Build context with reranked results for better relevance
            # Create SearchResults with reranked results for context building
            from backend.models.queries import SearchResults
            reranked_search_results = SearchResults(
                query=search_results.query,
                keyword_results=reranked_results,  # Use reranked results (now 20 instead of 5)
                semantic_results=[],  # Already merged into reranked_results
                graph_results=[],     # Already merged into reranked_results
                total_results=len(reranked_results)
            )
            
            context = await build_context(
                request.query, 
                reranked_search_results,
                max_tokens=context_recommendation.recommended_tokens
            )
            
            # Step 12: Synthesize answer with conversation context
            answer_response = await synthesize_answer(request.query, context)
            
            # Step 13: Calculate confidence and extract sources
            confidence = calculate_confidence(context, request.query)
            sources = extract_sources(context) if request.include_sources else []
            
            # Step 14: Create response metadata
            processing_time = time.time() - start_time
            metadata = format_response_metadata(request.query, context, confidence)
            metadata.update({
                "conversation_context": {
                    "original_query": original_query,
                    "expanded_query": request.query if request.query != original_query else None,
                    "context_summary": conversation_context.context_summary if conversation_context else None,
                    "recent_queries_count": len(conversation_context.recent_queries) if conversation_context else 0,
                    "session_duration_minutes": conversation_context.session_duration if conversation_context else 0,
                    "extracted_entities": conversation_context.extracted_entities if conversation_context else [],
                    "key_topics": conversation_context.key_topics if conversation_context else []
                },
                "decomposition": {
                    "intent": decomposition.intent,
                    "entities": decomposition.entities,
                    "sub_queries": [sq.text for sq in decomposition.sub_queries]
                },
                "expansion": {
                    "expanded_terms": expansions.expanded_terms,
                    "synonyms": expansions.synonyms,
                    "related_concepts": expansions.related_concepts
                },
                "search_optimization": {
                    "k_values": k_values,
                    "original_results": {
                        "keyword_count": len(search_results.keyword_results),
                        "semantic_count": len(search_results.semantic_results),
                        "graph_count": len(search_results.graph_results),
                        "total_count": search_results.total_results
                    },
                    "reranked_count": len(reranked_results),
                    "freshness_info": {
                        "temporal_query_detected": self.search_service.freshness_scorer.is_temporal_query(request.query),
                        "freshness_weight": self.search_service.freshness_scorer.calculate_weight_for_query(request.query),
                        "sample_freshness_scores": [
                            {
                                "source": result.source,
                                "freshness_category": result.metadata.get("freshness_category", "N/A"),
                                "age_days": result.metadata.get("age_days", "N/A"),
                                "freshness_boost": result.metadata.get("freshness_boost", "N/A"),
                                "original_score": result.metadata.get("original_score", "N/A"),
                                "boosted_score": result.score
                            }
                            for result in reranked_results[:3]  # Show top 3 results
                            if result.metadata.get("freshness_category")
                        ]
                    }
                },
                "adaptive_context": {
                    "complexity_level": context_recommendation.complexity_level,
                    "recommended_tokens": context_recommendation.recommended_tokens,
                    "actual_tokens": context.total_tokens,
                    "key_factors": context_recommendation.key_factors,
                    "reasoning": context_recommendation.reasoning
                }
            })
            
            # Step 15: Store query history
            if request.user_id:
                await self._store_query_history(
                    query_id, request, answer_response.answer, metadata
                )
            
            return QueryProcessingResponse(
                id=query_id,
                query=original_query,  # Return original query to user
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