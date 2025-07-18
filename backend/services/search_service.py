"""Unified search service combining multiple search strategies."""

import asyncio
from uuid import UUID
from typing import Protocol
from backend.models.queries import SearchResult, SearchResults
from backend.core.database import get_db_pool
from backend.utils.freshness_scoring import default_freshness_scorer


class SearchStrategy(Protocol):
    """Protocol for search strategies."""
    
    async def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Execute search with given query."""
        ...


class SemanticSearchStrategy:
    """Semantic search using embeddings."""
    
    def __init__(self, db_pool):
        self.db_pool = db_pool
        from backend.services.embedding_generation_service import EmbeddingGenerationService
        self.embedding_service = EmbeddingGenerationService(db_pool)
    
    async def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Search using semantic similarity."""
        from backend.models.embeddings import SemanticSearchRequest
        
        try:
            # Use existing semantic search functionality
            search_request = SemanticSearchRequest(
                query=query,
                limit=limit,
                min_similarity=0.3
            )
            
            response = await self.embedding_service.semantic_search(search_request)
            
            return [
                SearchResult(
                    id=str(result.content_id),
                    content=result.content_preview or "No preview available",
                    source=result.document_name or "unknown",  # Now using actual document name
                    score=result.similarity_score,
                    metadata={"type": "semantic", "content_type": result.content_type}
                )
                for result in response.results
            ]
        except Exception as e:
            # Fallback to basic search if embedding service fails
            print(f"Error in semantic search: {e}")
            return []


class KeywordSearchStrategy:
    """Full-text search using PostgreSQL."""
    
    def __init__(self, db_pool):
        self.db_pool = db_pool
    
    async def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Search using keyword matching."""
        async with self.db_pool.acquire() as conn:
            # Use PostgreSQL full-text search with document names
            results = await conn.fetch("""
                SELECT c.id, c.content, d.name as doc_name,
                       ts_rank(to_tsvector('english', c.content), 
                              plainto_tsquery('english', $2)) as score
                FROM chunks c
                JOIN documents d ON c.doc_id = d.id
                WHERE to_tsvector('english', c.content) @@ 
                      plainto_tsquery('english', $2)
                ORDER BY score DESC
                LIMIT $1
            """, limit, query)
            
            return [
                SearchResult(
                    id=str(row["id"]),
                    content=row["content"],
                    source=row["doc_name"] or "unknown",
                    score=float(row["score"]),
                    metadata={"type": "keyword"}
                )
                for row in results
            ]


class GraphSearchStrategy:
    """Knowledge graph search using entities and relationships."""
    
    def __init__(self, db_pool):
        self.db_pool = db_pool
    
    async def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Search using knowledge graph."""
        async with self.db_pool.acquire() as conn:
            # Search entities matching query with document names
            entity_results = await conn.fetch("""
                SELECT e.id, e.entity_name as content, d.name as doc_name,
                       similarity(e.entity_name, $2) as score
                FROM entities e
                JOIN chunks c ON e.chunk_id = c.id
                JOIN documents d ON c.doc_id = d.id
                WHERE similarity(e.entity_name, $2) > 0.3
                ORDER BY score DESC
                LIMIT $1
            """, limit // 2, query)
            
            # Search relationships involving matching entities with document names
            rel_results = await conn.fetch("""
                SELECT r.id, 
                       CONCAT(e1.entity_name, ' ', r.relationship_type, ' ', e2.entity_name) as content,
                       d.name as doc_name,
                       r.confidence as score
                FROM relationships r
                JOIN entities e1 ON r.source_entity_id = e1.id
                JOIN entities e2 ON r.target_entity_id = e2.id
                JOIN chunks c ON e1.chunk_id = c.id
                JOIN documents d ON c.doc_id = d.id
                WHERE similarity(e1.entity_name, $2) > 0.2 
                   OR similarity(e2.entity_name, $2) > 0.2
                ORDER BY score DESC
                LIMIT $1
            """, limit // 2, query)
            
            results = []
            
            # Add entity results
            for row in entity_results:
                results.append(SearchResult(
                    id=str(row["id"]),
                    content=row["content"],
                    source=row["doc_name"] or "unknown",
                    score=float(row["score"]),
                    metadata={"type": "entity"}
                ))
            
            # Add relationship results
            for row in rel_results:
                results.append(SearchResult(
                    id=str(row["id"]),
                    content=row["content"],
                    source=row["doc_name"] or "unknown",
                    score=float(row["score"]),
                    metadata={"type": "relationship"}
                ))
            
            return results


class SearchService:
    """Unified search service combining multiple strategies."""
    
    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.semantic_search = SemanticSearchStrategy(db_pool)
        self.keyword_search = KeywordSearchStrategy(db_pool)
        self.graph_search = GraphSearchStrategy(db_pool)
        self.freshness_scorer = default_freshness_scorer
    
    async def _apply_freshness_scoring(self, results: list[SearchResult], query: str) -> list[SearchResult]:
        """Apply freshness scoring to search results."""
        if not results:
            return results
        
        # Get document creation dates for all unique sources
        document_sources = list(set(result.source for result in results if result.source != "unknown"))
        
        if not document_sources:
            return results
        
        # Fetch document creation dates using document names
        async with self.db_pool.acquire() as conn:
            doc_dates = await conn.fetch("""
                SELECT name, created_at 
                FROM documents 
                WHERE name = ANY($1::text[])
            """, document_sources)
        
        # Create lookup dict for document dates
        doc_date_lookup = {row["name"]: row["created_at"] for row in doc_dates}
        
        # Apply freshness scoring to each result
        freshness_boosted_results = []
        for result in results:
            if result.source in doc_date_lookup:
                doc_created_at = doc_date_lookup[result.source]
                freshness_score = self.freshness_scorer.calculate_freshness_score(doc_created_at)
                
                # Apply freshness boost to score
                boosted_score = self.freshness_scorer.apply_freshness_boost(
                    result.score, freshness_score, query
                )
                
                # Update metadata with freshness info
                updated_metadata = result.metadata.copy()
                updated_metadata.update({
                    "freshness_score": freshness_score.freshness_score,
                    "freshness_category": freshness_score.freshness_category,
                    "age_days": freshness_score.age_days,
                    "freshness_boost": freshness_score.boost_factor,
                    "original_score": result.score,
                    "freshness_explanation": self.freshness_scorer.get_freshness_explanation(freshness_score)
                })
                
                # Create updated result with boosted score
                freshness_boosted_results.append(SearchResult(
                    id=result.id,
                    content=result.content,
                    source=result.source,
                    score=boosted_score,
                    metadata=updated_metadata
                ))
            else:
                # No freshness info available, keep original
                freshness_boosted_results.append(result)
        
        return freshness_boosted_results
    
    async def search_all(self, query: str, k_values: dict = None) -> SearchResults:
        """Execute all search strategies in parallel with optimized k values."""
        # Use provided k values or defaults
        if k_values is None:
            k_values = {"keyword_k": 50, "semantic_k": 50, "graph_k": 25}
        
        # Run all searches concurrently with optimized k values
        keyword_task = asyncio.create_task(
            self.keyword_search.search(query, k_values.get("keyword_k", 50))
        )
        semantic_task = asyncio.create_task(
            self.semantic_search.search(query, k_values.get("semantic_k", 50))
        )
        graph_task = asyncio.create_task(
            self.graph_search.search(query, k_values.get("graph_k", 25))
        )
        
        # Wait for all searches to complete
        keyword_results, semantic_results, graph_results = await asyncio.gather(
            keyword_task, semantic_task, graph_task,
            return_exceptions=True
        )
        
        # Handle potential exceptions
        if isinstance(keyword_results, Exception):
            keyword_results = []
        if isinstance(semantic_results, Exception):
            semantic_results = []
        if isinstance(graph_results, Exception):
            graph_results = []
        
        # Apply freshness scoring to all result types
        keyword_results = await self._apply_freshness_scoring(keyword_results, query)
        semantic_results = await self._apply_freshness_scoring(semantic_results, query)
        graph_results = await self._apply_freshness_scoring(graph_results, query)
        
        total_results = len(keyword_results) + len(semantic_results) + len(graph_results)
        
        return SearchResults(
            query=query,
            keyword_results=keyword_results,
            semantic_results=semantic_results,
            graph_results=graph_results,
            total_results=total_results
        )
    
    async def search_by_documents(self, query: str, document_ids: list[UUID], 
                                limit: int = 10) -> SearchResults:
        """Search within specific documents only."""
        doc_filter = "AND c.doc_id = ANY($3)"
        
        async with self.db_pool.acquire() as conn:
            # Keyword search within documents
            keyword_results = await conn.fetch(f"""
                SELECT c.id, c.content, d.name as source,
                       ts_rank(to_tsvector('english', c.content), 
                              plainto_tsquery('english', $2)) as score
                FROM chunks c
                JOIN documents d ON c.doc_id = d.id
                WHERE to_tsvector('english', c.content) @@ 
                      plainto_tsquery('english', $2)
                      {doc_filter}
                ORDER BY score DESC
                LIMIT $1
            """, limit, query, [str(doc_id) for doc_id in document_ids])
            
            # For semantic search, we'll use the semantic search service
            # which properly handles embedding generation
            try:
                from backend.models.embeddings import SemanticSearchRequest
                search_request = SemanticSearchRequest(
                    query=query,
                    limit=limit,
                    similarity_threshold=0.3,
                    doc_id=document_ids[0] if document_ids else None  # Use first doc for filtering
                )
                semantic_response = await self.semantic_search.embedding_service.semantic_search(search_request)
                semantic_search_results = [
                    SearchResult(
                        id=str(result.content_id),
                        content=result.content_preview or "No preview available",
                        source=result.document_name or "unknown",
                        score=result.similarity_score,
                        metadata={"type": "semantic", "content_type": result.content_type}
                    )
                    for result in semantic_response.results
                ]
            except Exception as e:
                print(f"Error in document-specific semantic search: {e}")
                semantic_search_results = []
        
        keyword_search_results = [
            SearchResult(
                id=str(row["id"]),
                content=row["content"],
                source=str(row["source"]),
                score=float(row["score"]),
                metadata={"type": "keyword"}
            )
            for row in keyword_results
        ]
        
        # Apply freshness scoring to document-specific results
        keyword_search_results = await self._apply_freshness_scoring(keyword_search_results, query)
        semantic_search_results = await self._apply_freshness_scoring(semantic_search_results, query)
        
        return SearchResults(
            query=query,
            keyword_results=keyword_search_results,
            semantic_results=semantic_search_results,
            graph_results=[],
            total_results=len(keyword_search_results) + len(semantic_search_results)
        )


async def get_search_service() -> SearchService:
    """Get search service instance."""
    db_pool = await get_db_pool()
    return SearchService(db_pool)