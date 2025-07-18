"""Query expansion service using flexible strategy pattern."""

from typing import List, Dict, Protocol
from uuid import UUID
from pydantic_ai import Agent
from pydantic import BaseModel, Field
from backend.core.config import get_settings, setup_pydantic_ai_environment


class QueryExpansions(BaseModel):
    """Model for query expansion results."""
    original_query: str = Field(..., description="Original user query")
    expanded_terms: List[str] = Field(default_factory=list, description="Related terms")
    synonyms: List[str] = Field(default_factory=list, description="Synonyms")
    related_concepts: List[str] = Field(default_factory=list, description="Related concepts")


class ContentAnalyzer(Protocol):
    """Protocol for content analysis strategies."""
    
    async def analyze_content(self, db_pool, project_id: UUID = None, 
                            document_ids: List[UUID] = None) -> Dict[str, List[str]]:
        """Analyze content and return context information."""
        ...


class EntityBasedAnalyzer:
    """Analyze content based on extracted entities."""
    
    def __init__(self, limit: int = 50):
        self.limit = limit
    
    async def analyze_content(self, db_pool, project_id: UUID = None, 
                            document_ids: List[UUID] = None) -> Dict[str, List[str]]:
        """Get entities and types from content."""
        context = {"entities": [], "topics": []}
        
        async with db_pool.acquire() as conn:
            query = "SELECT DISTINCT e.entity_name, e.entity_type FROM entities e WHERE 1=1"
            params = []
            
            if project_id:
                query += " AND e.project_id = $1"
                params.append(project_id)
            
            if document_ids:
                param_num = len(params) + 1
                query += f" AND e.doc_id = ANY(${param_num})"
                params.append([str(doc_id) for doc_id in document_ids])
            
            query += f" LIMIT {self.limit}"
            
            try:
                rows = await conn.fetch(query, *params)
                context["entities"] = [row["entity_name"] for row in rows]
                context["topics"] = list(set(row["entity_type"] for row in rows))
            except Exception:
                pass
        
        return context


class SimpleQueryExpander:
    """Simple query expander using LLM with content context."""
    
    def __init__(self):
        self._agent = None
    
    @property
    def agent(self) -> Agent:
        if self._agent is None:
            setup_pydantic_ai_environment()
            settings = get_settings()
            
            system_prompt = """Expand the user query with relevant terms that would help find related content.

Rules:
1. Keep expansions focused and relevant
2. Generate 2-3 expanded terms, 2-3 synonyms, 1-2 related concepts
3. Consider the content context provided
4. Maintain original query intent"""
            
            self._agent = Agent(
                model=f"openai:{settings.default_model}",
                system_prompt=system_prompt,
                result_type=QueryExpansions
            )
        return self._agent
    
    async def expand(self, query: str, content_context: Dict[str, List[str]]) -> QueryExpansions:
        """Expand query using content context."""
        context_str = ""
        if content_context.get("entities"):
            context_str += f"Available entities: {', '.join(content_context['entities'][:10])}\n"
        if content_context.get("topics"):
            context_str += f"Content topics: {', '.join(content_context['topics'][:10])}\n"
        
        prompt = f"Query: {query}\n\nContent Context:\n{context_str}"
        result = await self.agent.run(prompt)
        return result.data


class AdaptiveTopKCalculator:
    """Calculate optimal k values based on query characteristics."""
    
    def __init__(self, base_k: int = 50, max_k: int = 100, min_k: int = 20):
        self.base_k = base_k
        self.max_k = max_k
        self.min_k = min_k
    
    def calculate_k_values(self, query: str, expansions: QueryExpansions = None) -> Dict[str, int]:
        """Calculate k values for different search strategies."""
        complexity = self._query_complexity(query, expansions)
        
        # Adjust base k based on complexity
        adjusted_k = max(self.min_k, min(self.max_k, int(self.base_k * complexity)))
        
        return {
            "keyword_k": adjusted_k,
            "semantic_k": adjusted_k,
            "graph_k": max(10, adjusted_k // 2),
            "rerank_k": min(25, adjusted_k // 2),
            "final_k": 5
        }
    
    def _query_complexity(self, query: str, expansions: QueryExpansions = None) -> float:
        """Calculate complexity multiplier (0.5 - 1.5)."""
        factors = []
        
        # Query length
        word_count = len(query.split())
        factors.append(min(word_count / 8.0, 1.0))
        
        # Question words indicate complexity
        question_words = {'how', 'why', 'what', 'when', 'where', 'compare', 'analyze'}
        has_question = any(word in query.lower() for word in question_words)
        factors.append(0.8 if has_question else 0.4)
        
        # Expansion richness
        if expansions:
            expansion_count = len(expansions.expanded_terms + expansions.synonyms + expansions.related_concepts)
            factors.append(min(expansion_count / 8.0, 1.0))
        
        avg_complexity = sum(factors) / len(factors)
        return max(0.5, min(1.5, avg_complexity + 0.5))


class QueryExpansionService:
    """Main service using strategy pattern for flexible query expansion."""
    
    def __init__(self, db_pool, 
                 content_analyzer: ContentAnalyzer = None,
                 query_expander: SimpleQueryExpander = None,
                 topk_calculator: AdaptiveTopKCalculator = None):
        self.db_pool = db_pool
        self.content_analyzer = content_analyzer or EntityBasedAnalyzer()
        self.query_expander = query_expander or SimpleQueryExpander()
        self.topk_calculator = topk_calculator or AdaptiveTopKCalculator()
    
    async def expand_query(self, query: str, project_id: UUID = None, 
                          document_ids: List[UUID] = None) -> QueryExpansions:
        """Expand query with content awareness."""
        # Analyze content context
        content_context = await self.content_analyzer.analyze_content(
            self.db_pool, project_id, document_ids
        )
        
        # Expand query using context
        expansions = await self.query_expander.expand(query, content_context)
        return expansions
    
    def calculate_optimal_k(self, query: str, expansions: QueryExpansions = None) -> Dict[str, int]:
        """Calculate optimal k values for search strategies."""
        return self.topk_calculator.calculate_k_values(query, expansions)
    
    def create_query_variations(self, expansions: QueryExpansions, max_variations: int = 3) -> List[str]:
        """Create query variations from expansions."""
        variations = [expansions.original_query]
        
        # Add variations with expanded terms
        for term in expansions.expanded_terms[:max_variations]:
            variations.append(f"{expansions.original_query} {term}")
        
        return variations[:max_variations + 1]


async def get_query_expansion_service(db_pool) -> QueryExpansionService:
    """Get query expansion service with default strategies."""
    return QueryExpansionService(db_pool)