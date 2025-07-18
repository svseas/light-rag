"""Reranking service implementing RRF fusion and cross-encoder reranking."""

from typing import List, Dict
from backend.models.queries import SearchResult


class RRFFusion:
    """Reciprocal Rank Fusion algorithm for combining ranked lists."""
    
    def __init__(self, k: int = 60):
        self.k = k
    
    def fuse(self, keyword_results: List[SearchResult], 
             semantic_results: List[SearchResult], 
             graph_results: List[SearchResult]) -> List[SearchResult]:
        """Fuse multiple ranked lists using RRF algorithm."""
        # Collect all unique results with their RRF scores
        rrf_scores: Dict[str, float] = {}
        result_lookup: Dict[str, SearchResult] = {}
        
        # Process each result list
        for rank, result in enumerate(keyword_results, 1):
            rrf_scores[result.id] = rrf_scores.get(result.id, 0) + (1.0 / (self.k + rank))
            result_lookup[result.id] = result
            
        for rank, result in enumerate(semantic_results, 1):
            rrf_scores[result.id] = rrf_scores.get(result.id, 0) + (1.0 / (self.k + rank))
            result_lookup[result.id] = result
            
        for rank, result in enumerate(graph_results, 1):
            rrf_scores[result.id] = rrf_scores.get(result.id, 0) + (1.0 / (self.k + rank))
            result_lookup[result.id] = result
        
        # Sort by RRF score and create fused results
        sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        return [
            SearchResult(
                id=result_id,
                content=result_lookup[result_id].content,
                source=result_lookup[result_id].source,
                score=rrf_score,
                metadata={
                    **result_lookup[result_id].metadata,
                    "rrf_score": rrf_score,
                    "original_score": result_lookup[result_id].score
                }
            )
            for result_id, rrf_score in sorted_items
        ]


class CrossEncoderReranker:
    """Cross-encoder reranking using sentence-transformers."""
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self._model = None
    
    @property
    def model(self):
        """Lazy load the cross-encoder model."""
        if self._model is None:
            try:
                from sentence_transformers.cross_encoder import CrossEncoder
                self._model = CrossEncoder(self.model_name)
            except ImportError:
                raise ImportError("sentence-transformers required for cross-encoder reranking")
        return self._model
    
    def rerank(self, query: str, results: List[SearchResult], top_k: int = 25) -> List[SearchResult]:
        """Rerank results using cross-encoder model."""
        if not results:
            return []
        
        # Take only top_k results to rerank (performance optimization)
        candidates = results[:top_k]
        
        # Create query-document pairs
        pairs = [[query, result.content] for result in candidates]
        
        # Get relevance scores from cross-encoder
        scores = self.model.predict(pairs)
        
        # Combine results with new scores and sort
        reranked = []
        for result, score in zip(candidates, scores):
            reranked_result = SearchResult(
                id=result.id,
                content=result.content,
                source=result.source,
                score=float(score),
                metadata={
                    **result.metadata,
                    "cross_encoder_score": float(score),
                    "rrf_score": result.metadata.get("rrf_score"),
                    "original_score": result.metadata.get("original_score")
                }
            )
            reranked.append(reranked_result)
        
        # Sort by cross-encoder score
        return sorted(reranked, key=lambda x: x.score, reverse=True)


class RerankingService:
    """Service implementing Retrieve -> Fuse -> Rerank -> Synthesize flow."""
    
    def __init__(self, use_cross_encoder: bool = True):
        self.rrf_fusion = RRFFusion()
        self.cross_encoder = CrossEncoderReranker() if use_cross_encoder else None
    
    def process_results(self, query: str,
                       keyword_results: List[SearchResult],
                       semantic_results: List[SearchResult], 
                       graph_results: List[SearchResult],
                       final_k: int = 5) -> List[SearchResult]:
        """Complete reranking pipeline: Fuse -> Rerank -> Top-K."""
        
        # Step 1: Fuse using RRF
        fused_results = self.rrf_fusion.fuse(keyword_results, semantic_results, graph_results)
        
        # Step 2: Cross-encoder reranking (if enabled)
        if self.cross_encoder and fused_results:
            reranked_results = self.cross_encoder.rerank(query, fused_results, top_k=25)
        else:
            reranked_results = fused_results
        
        # Step 3: Return final top-k for LLM
        return reranked_results[:final_k]


async def get_reranking_service() -> RerankingService:
    """Get reranking service instance."""
    return RerankingService()