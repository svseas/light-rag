"""Query decomposition agent for breaking down complex queries."""

from pydantic_ai import Agent
from backend.models.queries import QueryDecomposition, QueryType, SearchScope
from backend.core.config import get_settings, setup_pydantic_ai_environment


_DECOMPOSITION_PROMPT = """You are a query analysis expert. Analyze the user query and break it down into components.

Your task:
1. Identify the primary intent (factual, analytical, comparative, summarization, exploratory)
2. Extract key entities mentioned in the query
3. Break complex queries into simpler sub-queries if needed
4. Identify any temporal constraints (dates, time ranges)
5. Determine the appropriate search scope

Guidelines:
- Keep sub-queries simple and focused
- Extract only explicit entities (people, places, concepts)
- Mark temporal references clearly
- Assign priority weights (0.1-1.0) based on importance
- Be precise about query intent classification

Examples:
Query: "What are the main differences between Python and JavaScript for web development?"
Intent: comparative
Entities: ["Python", "JavaScript", "web development"]
Sub-queries: 
- "Python features for web development" (priority: 0.9)
- "JavaScript features for web development" (priority: 0.9)
- "Python vs JavaScript comparison" (priority: 1.0)

Query: "Tell me about climate change impacts in the last 10 years"
Intent: summarization
Entities: ["climate change"]
Temporal: ["last 10 years"]
Sub-queries:
- "Climate change impacts recent decade" (priority: 1.0)
"""


def create_query_decomposition_agent() -> Agent[str, QueryDecomposition]:
    """Create query decomposition agent with proper configuration."""
    setup_pydantic_ai_environment()
    settings = get_settings()
    
    return Agent(
        model=f"openai:{settings.default_model}",
        system_prompt=_DECOMPOSITION_PROMPT,
        result_type=QueryDecomposition
    )


query_decomposition_agent = None


async def decompose_query(query: str) -> QueryDecomposition:
    """Decompose user query into structured components.
    
    Args:
        query: User query text to analyze.
        
    Returns:
        QueryDecomposition with analyzed components.
        
    Raises:
        ValueError: If query is empty or invalid.
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")
    
    global query_decomposition_agent
    if query_decomposition_agent is None:
        query_decomposition_agent = create_query_decomposition_agent()
    
    result = await query_decomposition_agent.run(query.strip())
    return result.data