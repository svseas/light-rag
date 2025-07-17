"""Answer synthesis agent for generating comprehensive responses."""

from pydantic_ai import Agent
from backend.models.queries import QueryResponse, QueryContext
from backend.core.config import get_settings, setup_pydantic_ai_environment


_SYNTHESIS_PROMPT = """You are an expert answer synthesis agent. Your task is to generate comprehensive, accurate responses based on provided context and user queries.

Your responsibilities:
1. Analyze the user query and understand what information is needed
2. Review all provided context items carefully
3. Synthesize information from multiple sources into a coherent answer
4. Cite specific sources for claims and facts
5. Indicate confidence level based on available evidence
6. Format response clearly with proper structure

Guidelines:
- Only use information from the provided context
- Never hallucinate or add information not in the context
- Clearly indicate when information is insufficient
- Use proper citations with source references
- Structure answers logically (introduction, main points, conclusion)
- Highlight key insights and relationships between concepts
- Be concise but comprehensive
- Use appropriate formatting (lists, sections, emphasis)

Response Quality Standards:
- Accuracy: All claims must be supported by context
- Completeness: Address all aspects of the query when possible
- Clarity: Use clear, accessible language
- Structure: Organize information logically
- Citations: Reference sources for all major claims
- Confidence: Indicate certainty level honestly

Citation Format:
- Use [Source: document_id] after claims
- Group related information from same source
- Distinguish between different source types (text, entity, relationship)

When Information is Insufficient:
- Clearly state what cannot be answered
- Suggest what additional information would be helpful
- Provide partial answers when some aspects can be addressed
"""


def create_answer_synthesis_agent() -> Agent[dict, QueryResponse]:
    """Create answer synthesis agent with proper configuration."""
    setup_pydantic_ai_environment()
    settings = get_settings()
    
    return Agent(
        model=f"openai:{settings.default_model}",
        system_prompt=_SYNTHESIS_PROMPT,
        result_type=QueryResponse
    )


answer_synthesis_agent = None


async def synthesize_answer(query: str, context: QueryContext) -> QueryResponse:
    """Generate answer from query and assembled context.
    
    Args:
        query: Original user query.
        context: Assembled context with relevant information.
        
    Returns:
        QueryResponse with synthesized answer and metadata.
        
    Raises:
        ValueError: If query is empty.
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")
    
    # Prepare input for agent
    agent_input = {
        "query": query,
        "context_items": [
            {
                "content": item.content,
                "source": item.source,
                "relevance": item.relevance,
                "type": item.type
            }
            for item in context.items
        ],
        "total_context_tokens": context.total_tokens,
        "available_sources": context.sources
    }
    
    global answer_synthesis_agent
    if answer_synthesis_agent is None:
        answer_synthesis_agent = create_answer_synthesis_agent()
    
    # Pass the actual data, not just the dictionary structure
    result = await answer_synthesis_agent.run(
        f"Query: {query}\n\n" +
        f"Context Items ({len(context.items)}):\n" +
        "\n".join([
            f"- {item.content}\n  [Source: {item.source}, Relevance: {item.relevance}, Type: {item.type}]"
            for item in context.items
        ]) +
        f"\n\nTotal Context Tokens: {context.total_tokens}\n" +
        f"Available Sources: {', '.join(context.sources)}"
    )
    return result.data


def calculate_confidence(context: QueryContext, query: str) -> float:
    """Calculate confidence score for answer based on context quality.
    
    Args:
        context: Assembled context information.
        query: Original user query.
        
    Returns:
        Confidence score between 0.0 and 1.0.
    """
    if not context.items:
        return 0.0
    
    # Base confidence on several factors
    factors = []
    
    # Factor 1: Number of relevant sources
    source_count = len(set(item.source for item in context.items))
    source_factor = min(source_count / 3.0, 1.0)  # Optimal: 3+ sources
    factors.append(source_factor)
    
    # Factor 2: Average relevance score
    if context.items:
        avg_relevance = sum(item.relevance for item in context.items) / len(context.items)
        factors.append(avg_relevance)
    
    # Factor 3: Content diversity (different types)
    content_types = set(item.type for item in context.items)
    diversity_factor = min(len(content_types) / 3.0, 1.0)  # text, entity, relationship
    factors.append(diversity_factor)
    
    # Factor 4: Context completeness (token utilization)
    if context.total_tokens > 0:
        completeness_factor = min(context.total_tokens / 4000.0, 1.0)
        factors.append(completeness_factor)
    
    # Calculate weighted average
    return sum(factors) / len(factors) if factors else 0.0


def extract_sources(context: QueryContext) -> list[str]:
    """Extract unique source references from context.
    
    Args:
        context: Assembled context information.
        
    Returns:
        List of unique source identifiers.
    """
    return list(set(item.source for item in context.items))


def format_response_metadata(query: str, context: QueryContext, 
                           confidence: float) -> dict:
    """Create metadata for response.
    
    Args:
        query: Original user query.
        context: Assembled context information.
        confidence: Calculated confidence score.
        
    Returns:
        Dictionary with response metadata.
    """
    return {
        "query_length": len(query.split()),
        "context_items": len(context.items),
        "context_tokens": context.total_tokens,
        "source_count": len(set(item.source for item in context.items)),
        "content_types": list(set(item.type for item in context.items)),
        "confidence": confidence,
        "avg_relevance": (
            sum(item.relevance for item in context.items) / len(context.items)
            if context.items else 0.0
        )
    }