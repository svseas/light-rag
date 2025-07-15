# Embedding Generation Agent Implementation Plan

**Date**: 2025-07-15 23:50  
**Feature**: Embedding Generation Agent  
**Status**: Planning Phase

## 1. Planning & Design ✅

### Feature Requirements:
- **EmbeddingGenerationAgent**: Generate vector embeddings for entities and chunks using OpenAI's text-embedding-3-large
- **Semantic Search**: Enable similarity searches using pgvector extension
- **Batch Processing**: Efficient batch embedding generation for multiple items
- **Database Integration**: Store embeddings in existing vector(1536) columns
- **API Endpoints**: Embedding generation and similarity search endpoints

### Database Schema Status:
- **entities table**: Already has `embedding vector(1536)` column ✅
- **chunks table**: Already has `embedding vector(1536)` column ✅  
- **pgvector extension**: Already enabled for similarity searches ✅
- **No schema changes needed**

### API Endpoints Design:
- `POST /api/embeddings/entities/{entity_id}/generate` - Generate embedding for specific entity
- `POST /api/embeddings/chunks/{chunk_id}/generate` - Generate embedding for specific chunk
- `POST /api/embeddings/entities/batch` - Batch generate embeddings for multiple entities
- `POST /api/embeddings/chunks/batch` - Batch generate embeddings for multiple chunks
- `GET /api/embeddings/entities/{entity_id}/similar` - Find similar entities
- `GET /api/embeddings/chunks/{chunk_id}/similar` - Find similar chunks
- `POST /api/embeddings/search` - Semantic search across entities and chunks

## 2. Data Layer Implementation

### Models (`backend/models/embeddings.py`):
- `EmbeddingGenerationRequest` - Request model for embedding generation
- `EmbeddingGenerationResponse` - Response model with embedding metadata
- `BatchEmbeddingRequest` - Request model for batch processing
- `BatchEmbeddingResponse` - Response model for batch results
- `SimilaritySearchRequest` - Request model for similarity searches
- `SimilaritySearchResponse` - Response model with similarity results
- `SemanticSearchRequest` - Request model for semantic search
- `SemanticSearchResponse` - Response model with search results

### Database Operations:
- Use existing `entities` and `chunks` tables with vector columns
- Leverage pgvector for similarity calculations
- Implement efficient batch updates for embeddings
- Add similarity search queries with configurable thresholds

## 3. Business Logic Layer

### EmbeddingGenerationAgent (`backend/agents/embedding_generation.py`):
- **Not using PydanticAI** - Direct OpenAI API integration for embeddings
- OpenAI text-embedding-3-large model via OpenRouter
- Batch processing support for efficiency
- Error handling for API failures
- Rate limiting and retry logic

### EmbeddingGenerationService (`backend/services/embedding_generation_service.py`):
- Business logic for embedding generation and storage
- Batch processing for entities and chunks
- Similarity search implementation using pgvector
- Semantic search across multiple content types
- Integration with existing entity and chunk services

### Configuration Updates:
- OpenAI embedding model configuration
- Batch size limits and processing parameters
- Similarity search thresholds and limits
- Rate limiting configuration for API calls

## 4. API Layer Implementation

### Routes (`backend/api/routes/embeddings.py`):
- Embedding generation endpoints for entities and chunks
- Batch processing endpoints for bulk operations
- Similarity search endpoints with proper pagination
- Semantic search endpoints with ranking
- Proper HTTP status codes and error handling

### Update Main Routes:
- Add embedding routes to `backend/api/main_routes.py`
- Ensure proper route organization and tags

## 5. Integration Points

### Entity Service Integration:
- Automatic embedding generation after entity extraction
- Update entity records with embedding vectors
- Similarity-based entity discovery

### Chunk Service Integration:
- Automatic embedding generation after chunk creation
- Update chunk records with embedding vectors
- Similarity-based chunk retrieval

### Search Enhancement:
- Semantic search across both entities and chunks
- Hybrid search combining text and vector similarity
- Relevance ranking based on embedding similarity

## 6. Testing Strategy

### Unit Tests:
- `tests/test_agents/test_embedding_generation.py` - Agent functionality
- `tests/test_services/test_embedding_generation_service.py` - Service logic
- `tests/test_api/test_embeddings.py` - API endpoints

### Integration Tests:
- End-to-end embedding generation workflow
- Similarity search accuracy and performance
- Batch processing efficiency and error handling

## 7. Configuration & Documentation

### Configuration Updates:
- Embedding generation parameters in `backend/core/config.py`
- OpenAI API settings and model configuration
- Batch processing and similarity search parameters

### Documentation:
- Update `project_structure.md` with new files
- Document embedding generation process and API endpoints
- Add semantic search capabilities documentation

## 8. Implementation Order

1. **Create Models**: Implement embedding-related Pydantic models
2. **EmbeddingGenerationAgent**: Build direct OpenAI API integration
3. **EmbeddingGenerationService**: Implement business logic and database operations
4. **API Routes**: Create embedding generation and search endpoints
5. **Integration**: Connect embedding generation to existing pipeline
6. **Testing**: Write comprehensive tests for all components
7. **Documentation**: Update project structure and create devlog

## Key Technical Details

### OpenAI Integration:
```python
# Direct OpenAI API usage (not PydanticAI)
import openai
from backend.core.config import get_settings

settings = get_settings()
client = openai.OpenAI(
    api_key=settings.openrouter_api_key,
    base_url="https://openrouter.ai/api/v1"
)

response = client.embeddings.create(
    model="text-embedding-3-large",
    input=texts,
    encoding_format="float"
)
```

### Database Operations:
```python
# Store embeddings using pgvector
query = """
    UPDATE entities 
    SET embedding = $1::vector 
    WHERE id = $2
"""
await conn.execute(query, embedding_vector, entity_id)

# Similarity search
query = """
    SELECT id, entity_name, embedding <-> $1::vector as distance
    FROM entities 
    WHERE embedding IS NOT NULL
    ORDER BY distance
    LIMIT $2
"""
```

### Batch Processing:
- Process embeddings in batches of 100 items
- Implement proper error handling for partial failures
- Use asyncio for concurrent processing
- Rate limiting to respect API limits

## Success Criteria

✅ Entities and chunks can be processed to generate embeddings  
✅ Embeddings are stored in database with pgvector support  
✅ Similarity search works with configurable thresholds  
✅ Batch processing handles large datasets efficiently  
✅ API endpoints provide full embedding functionality  
✅ Integration with existing pipeline works seamlessly  
✅ Comprehensive testing and error handling  
✅ Documentation and devlog completed  

This implementation will enable powerful semantic search capabilities and complete the core RAG pipeline with vector embeddings.

## Expected Outcomes

- **Vector Database**: Embeddings stored for all entities and chunks
- **Semantic Search**: Similarity-based search across content types
- **API Endpoints**: Full embedding generation and search capabilities
- **Performance**: Efficient batch processing and fast similarity queries
- **Integration**: Seamless integration with existing RAG pipeline

## Performance Considerations

- **Batch Processing**: Process multiple items in single API calls
- **Database Efficiency**: Use pgvector indexes for fast similarity searches
- **Caching**: Consider caching embeddings for frequently accessed content
- **Rate Limiting**: Respect OpenAI API rate limits
- **Concurrent Processing**: Use asyncio for parallel embedding generation

---

**Estimated Implementation Time**: 2-3 hours  
**Complexity**: Medium (OpenAI API integration, pgvector operations)  
**Dependencies**: Existing entity and chunk systems, pgvector extension  
**Next Phase**: Query decomposition and context building