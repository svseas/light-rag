"""LLM-based adaptive context window analyzer."""

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from backend.models.queries import QueryDecomposition
from backend.core.config import get_settings, setup_pydantic_ai_environment


class ContextWindowRecommendation(BaseModel):
    """LLM recommendation for adaptive context window sizing."""
    
    complexity_level: str = Field(..., description="Simple, moderate, complex, or highly_complex")
    reasoning: str = Field(..., description="Brief explanation of complexity assessment")
    recommended_tokens: int = Field(..., description="Recommended context window size (2000-10000)")
    key_factors: list[str] = Field(..., description="Top 3 factors driving complexity")


class AdaptiveContextAnalyzer:
    """LLM-based analyzer for determining optimal context window size."""
    
    def __init__(self):
        self.agent = None
        self.default_tokens = 4000
        self.min_tokens = 2000
        self.max_tokens = 10000
    
    def _create_agent(self) -> Agent:
        """Create the LLM agent for context analysis."""
        setup_pydantic_ai_environment()
        settings = get_settings()
        
        system_prompt = """You are an expert at analyzing query complexity to determine optimal context window sizes for RAG systems.

Your task: Given a user query and its decomposition, recommend the appropriate context window size (in tokens).

Guidelines:
- Simple queries (factual, single concept): 2000-3000 tokens
- Moderate queries (explanatory, multi-faceted): 3000-5000 tokens  
- Complex queries (analytical, comparative): 5000-7000 tokens
- Highly complex queries (multi-domain, temporal analysis): 7000-10000 tokens

Key factors to consider:
1. Number of entities and concepts
2. Query intent (factual vs analytical vs comparative)
3. Temporal complexity (time ranges, historical analysis)
4. Multi-step reasoning requirements
5. Cross-domain knowledge needs

Be concise but thorough in your reasoning. Focus on the most impactful factors."""

        return Agent(
            model=f"openai:{settings.default_model}",
            system_prompt=system_prompt,
            result_type=ContextWindowRecommendation
        )
    
    async def analyze_query(self, query: str, decomposition: QueryDecomposition) -> ContextWindowRecommendation:
        """Analyze query complexity and recommend context window size.
        
        Args:
            query: Original user query
            decomposition: Query decomposition result
            
        Returns:
            ContextWindowRecommendation with analysis
        """
        if self.agent is None:
            self.agent = self._create_agent()
        
        # Prepare analysis input
        analysis_input = f"""
Query: "{query}"

Decomposition Analysis:
- Intent: {decomposition.intent}
- Entities: {decomposition.entities}
- Sub-queries: {[sq.text for sq in decomposition.sub_queries]}
- Temporal constraints: {decomposition.temporal_constraints}
- Search scope: {decomposition.scope}
- Confidence: {decomposition.confidence}

Analyze this query's complexity and recommend optimal context window size.
"""
        
        try:
            result = await self.agent.run(analysis_input)
            recommendation = result.data
            
            # Validate and clamp token recommendation
            recommendation.recommended_tokens = max(
                self.min_tokens, 
                min(self.max_tokens, recommendation.recommended_tokens)
            )
            
            return recommendation
            
        except Exception as e:
            # Fallback to default if LLM fails
            return ContextWindowRecommendation(
                complexity_level="moderate",
                reasoning=f"LLM analysis failed ({str(e)}), using default context window",
                recommended_tokens=self.default_tokens,
                key_factors=["fallback_mode"]
            )
    
    def get_default_tokens(self) -> int:
        """Get default context window size."""
        return self.default_tokens


# Global analyzer instance
adaptive_context_analyzer = AdaptiveContextAnalyzer()