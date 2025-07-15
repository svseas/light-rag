# ChunkingAgent Implementation Plan

## 1. Planning & Design ✅

### Feature Requirements:
- **ChunkingAgent**: PydanticAI agent that intelligently splits documents into chunks
- **Chonkie Integration**: Use chonkie library for context-aware chunking
- **Database Storage**: Store chunks with embeddings preparation
- **API Endpoints**: Chunk management and retrieval endpoints

### Database Schema Updates:
- Chunks table already exists with: id, doc_id, content, chunk_index, embedding, tokens
- No schema changes needed, but may need to update chunk processing logic

### API Endpoints Design:
- `POST /api/documents/{doc_id}/chunks` - Trigger chunking for a document
- `GET /api/documents/{doc_id}/chunks` - List chunks for a document
- `GET /api/chunks/{chunk_id}` - Get specific chunk details
- `DELETE /api/chunks/{chunk_id}` - Delete a chunk

## 2. Data Layer Implementation

### Models (`backend/models/chunks.py`):
- `ChunkCreate` - Input model for chunk creation
- `ChunkResponse` - Output model for API responses
- `ChunkList` - Paginated chunk list
- `ChunkingRequest` - Request model for chunking operations
- `ChunkingStatus` - Status tracking for chunking operations

### Database Operations:
- Extend existing chunks table usage
- Add chunking status tracking
- Implement chunk retrieval with pagination

## 3. Business Logic Layer

### ChunkingAgent (`backend/agents/chunking.py`):
- PydanticAI agent with chonkie integration
- Configurable chunk size and overlap parameters
- Token counting and validation
- Error handling for chunking failures

### ChunkingService (`backend/services/chunking_service.py`):
- Business logic for chunk management
- Integration with document service
- Async chunking operations
- Database persistence for chunks

### Dependencies to Add:
- `chonkie` library for intelligent chunking
- Update `pyproject.toml` with new dependencies

## 4. API Layer Implementation

### Routes (`backend/api/routes/chunks.py`):
- Chunk management endpoints
- Proper HTTP status codes and error handling
- Pydantic validation for all inputs/outputs
- Integration with existing document routes

### Update Main Routes:
- Add chunk routes to `backend/api/main_routes.py`
- Ensure proper route organization

## 5. Integration Points

### Document Service Integration:
- Trigger chunking after document processing
- Update document processing pipeline
- Add chunking status to document metadata

### Database Connections:
- Use existing asyncpg connection patterns
- Maintain transaction consistency
- Proper error handling and rollback

## 6. Testing Strategy

### Unit Tests:
- `tests/test_agents/test_chunking.py` - Agent functionality
- `tests/test_services/test_chunking_service.py` - Service logic
- `tests/test_api/test_chunks.py` - API endpoints

### Integration Tests:
- End-to-end chunking workflow
- Document-to-chunks pipeline
- Error scenarios and recovery

## 7. Configuration & Documentation

### Configuration Updates:
- Chunking parameters in `backend/core/config.py`
- Environment variables for chunk settings
- Default chunk size and overlap configuration

### Documentation:
- Update `project_structure.md` with new files
- Document chunking parameters and configuration
- API endpoint documentation

## 8. Implementation Order

1. **Add Dependencies**: Update `pyproject.toml` with chonkie
2. **Create Models**: Implement chunk-related Pydantic models
3. **ChunkingAgent**: Build PydanticAI agent with chonkie integration
4. **ChunkingService**: Implement business logic and database operations
5. **API Routes**: Create chunk management endpoints
6. **Integration**: Connect chunking to document processing pipeline
7. **Testing**: Write comprehensive tests
8. **Documentation**: Update project structure and create devlog

## Key Technical Details

### Chonkie Integration:
```python
from chonkie import TokenChunker
chunker = TokenChunker(chunk_size=512, overlap=50)
chunks = chunker.chunk(document_content)
```

### Database Operations:
- Batch insert chunks for efficiency
- Maintain proper foreign key relationships
- Index chunks for fast retrieval

### Error Handling:
- Chunking failures should not break document processing
- Graceful degradation and retry mechanisms
- Proper logging with Logfire integration

## Success Criteria

✅ Documents can be chunked intelligently using chonkie
✅ Chunks are stored in database with proper relationships
✅ API endpoints work for chunk management
✅ Integration with existing document pipeline
✅ Comprehensive testing and error handling
✅ Documentation and devlog completed

This implementation will provide the foundation for the next phase (embedding generation) by preparing document chunks for vector processing.