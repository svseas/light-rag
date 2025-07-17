"""Context building agent for assembling relevant information."""

import logfire
from pydantic_ai import Agent
from backend.models.queries import QueryContext, ContextItem, SearchResults
from backend.core.config import get_settings, setup_pydantic_ai_environment


_CONTEXT_BUILDING_PROMPT = """You are a context building expert. Your task is to analyze search results and create the most relevant context for answering a user query.

Your responsibilities:
1. Rank and select the most relevant search results
2. Eliminate redundant information 
3. Ensure diverse information sources
4. Organize context by relevance and importance
5. Stay within token limits while maximizing information value

Guidelines:
- Prioritize results with higher relevance scores
- Include different types of information (text, entities, relationships)
- Avoid duplicate content from different sources
- Consider recency when available
- Maintain source attribution for all content
- Balance comprehensiveness with conciseness

Context Item Types:
- text: Direct text content from documents
- entity: Information about extracted entities
- relationship: Information about entity relationships
- summary: Condensed information from multiple sources

Selection Criteria:
- Relevance score > 0.3
- Unique content (no duplicates)
- Diverse source coverage
- Balanced information types
- Total token count within limits
"""


def create_context_builder_agent() -> Agent[dict, QueryContext]:
    """Create context building agent with proper configuration."""
    setup_pydantic_ai_environment()
    settings = get_settings()
    
    return Agent(
        model=f"openai:{settings.default_model}",
        system_prompt=_CONTEXT_BUILDING_PROMPT,
        result_type=QueryContext
    )


context_builder_agent = None


async def build_context(query: str, search_results: SearchResults, 
                       max_tokens: int = 8000) -> QueryContext:
    """Build context from search results for answer generation.
    
    Args:
        query: Original user query.
        search_results: Results from multiple search strategies.
        max_tokens: Maximum tokens for context.
        
    Returns:
        QueryContext with assembled relevant information.
        
    Raises:
        ValueError: If query is empty or no results provided.
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")
    
    if search_results.total_results == 0:
        return QueryContext(
            query=query,
            items=[],
            total_tokens=0,
            sources=[]
        )
    
    # Prepare input for agent
    agent_input = {
        "query": query,
        "keyword_results": [
            {
                "content": result.content,
                "source": result.source,
                "score": result.score,
                "type": result.metadata.get("type", "text")
            }
            for result in search_results.keyword_results
        ],
        "semantic_results": [
            {
                "content": result.content,
                "source": result.source,
                "score": result.score,
                "type": result.metadata.get("type", "text")
            }
            for result in search_results.semantic_results
        ],
        "graph_results": [
            {
                "content": result.content,
                "source": result.source,
                "score": result.score,
                "type": result.metadata.get("type", "text")
            }
            for result in search_results.graph_results
        ],
        "max_tokens": max_tokens
    }
    
    with logfire.span("context_building") as span:
        span.set_attribute("search_results_keyword_count", len(search_results.keyword_results))
        span.set_attribute("search_results_semantic_count", len(search_results.semantic_results))
        span.set_attribute("search_results_graph_count", len(search_results.graph_results))
        span.set_attribute("total_search_results", search_results.total_results)
        
        # Log first semantic result content for debugging
        if search_results.semantic_results:
            first_result = search_results.semantic_results[0]
            span.set_attribute("first_semantic_content_preview", first_result.content[:200])
            span.set_attribute("first_semantic_score", first_result.score)
            span.set_attribute("first_semantic_source", first_result.source)
        
        global context_builder_agent
        if context_builder_agent is None:
            context_builder_agent = create_context_builder_agent()
        
        with logfire.span("context_agent_run"):
            # Pass the actual data, not just the dictionary
            result = await context_builder_agent.run(
                f"Query: {query}\n\n" +
                f"Keyword Results ({len(search_results.keyword_results)}):\n" +
                "\n".join([f"- {r.content} (score: {r.score}, source: {r.source})" for r in search_results.keyword_results[:3]]) +
                f"\n\nSemantic Results ({len(search_results.semantic_results)}):\n" +
                "\n".join([f"- {r.content} (score: {r.score}, source: {r.source})" for r in search_results.semantic_results[:3]]) +
                f"\n\nGraph Results ({len(search_results.graph_results)}):\n" +
                "\n".join([f"- {r.content} (score: {r.score}, source: {r.source})" for r in search_results.graph_results[:3]]) +
                f"\n\nMax tokens: {max_tokens}"
            )
            context_data = result.data
        
        span.set_attribute("context_items_count", len(context_data.items))
        span.set_attribute("context_total_tokens", context_data.total_tokens)
        span.set_attribute("context_sources_count", len(context_data.sources))
        
        # Log first context item for debugging
        if context_data.items:
            first_item = context_data.items[0]
            span.set_attribute("first_context_content_preview", first_item.content[:200])
            span.set_attribute("first_context_relevance", first_item.relevance)
            span.set_attribute("first_context_type", first_item.type)
    
    return context_data


def merge_search_results(search_results: SearchResults) -> list[ContextItem]:
    """Merge and deduplicate search results into context items.
    
    Args:
        search_results: Results from multiple search strategies.
        
    Returns:
        List of unique context items sorted by relevance.
    """
    all_results = []
    seen_content = set()
    
    # Combine all results
    for result_list in [search_results.keyword_results, 
                       search_results.semantic_results,
                       search_results.graph_results]:
        for result in result_list:
            # Skip duplicates
            if result.content in seen_content:
                continue
            
            seen_content.add(result.content)
            all_results.append(ContextItem(
                content=result.content,
                source=result.source,
                relevance=result.score,
                type=result.metadata.get("type", "text")
            ))
    
    # Sort by relevance score
    all_results.sort(key=lambda x: x.relevance, reverse=True)
    
    return all_results


def estimate_tokens(text: str) -> int:
    """Estimate token count for text (rough approximation)."""
    return len(text.split()) * 1.3  # Rough estimate: ~1.3 tokens per word