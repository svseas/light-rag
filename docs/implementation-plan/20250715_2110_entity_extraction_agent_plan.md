# Entity Extraction Agent Implementation Plan

**Date**: 2025-07-15 21:10  
**Feature**: Entity Extraction Agent  
**Status**: Planning Phase

## 1. Planning & Design ✅

### Feature Requirements:
- **EntityExtractionAgent**: PydanticAI agent that extracts entities from text chunks
- **Entity Types**: Person, Organization, Location, Date, Event, Concept
- **Database Storage**: Store entities with relationships to chunks
- **API Endpoints**: Entity management and retrieval endpoints
- **Batch Processing**: Process multiple chunks efficiently

### Database Schema Updates:
- Entities table already exists with: id, chunk_id, entity_type, entity_name, confidence, metadata
- No schema changes needed for basic functionality

### API Endpoints Design:
- `POST /api/chunks/{chunk_id}/entities` - Extract entities from a chunk
- `GET /api/chunks/{chunk_id}/entities` - List entities for a chunk
- `GET /api/documents/{doc_id}/entities` - List all entities for a document
- `GET /api/entities/{entity_id}` - Get specific entity details
- `DELETE /api/entities/{entity_id}` - Delete an entity

## 2. Data Layer Implementation

### Models (`backend/models/entities.py`):
- `EntityBase` - Base entity model with common fields
- `EntityCreate` - Input model for entity creation
- `EntityResponse` - Output model for API responses
- `EntityList` - Paginated entity list
- `EntityExtractionRequest` - Request model for extraction operations
- `EntityExtractionStatus` - Status tracking for extraction operations

### Database Operations:
- Use existing entities table
- Add entity extraction status tracking
- Implement entity retrieval with pagination and filtering

## 3. Business Logic Layer

### EntityExtractionAgent (`backend/agents/entity_extraction.py`):
- PydanticAI agent configured for entity extraction
- Structured output with entity types and confidence scores
- Configurable entity types and extraction parameters
- Error handling for extraction failures

### EntityExtractionService (`backend/services/entity_extraction_service.py`):
- Business logic for entity management
- Integration with chunking service
- Batch processing capabilities
- Database persistence for entities

### Dependencies:
- No new dependencies needed - uses existing pydantic-ai setup

## 4. API Layer Implementation

### Routes (`backend/api/routes/entities.py`):
- Entity management endpoints
- Proper HTTP status codes and error handling
- Pydantic validation for all inputs/outputs
- Integration with existing chunk and document routes

### Update Main Routes:
- Add entity routes to `backend/api/main_routes.py`
- Ensure proper route organization

## 5. Integration Points

### Chunking Service Integration:
- Trigger entity extraction after chunking
- Update processing pipeline
- Add entity extraction status to processing metadata

### Database Connections:
- Use existing asyncpg connection patterns
- Maintain transaction consistency
- Proper error handling and rollback

## 6. Testing Strategy

### Unit Tests:
- `tests/test_agents/test_entity_extraction.py` - Agent functionality
- `tests/test_services/test_entity_extraction_service.py` - Service logic
- `tests/test_api/test_entities.py` - API endpoints

### Integration Tests:
- End-to-end entity extraction workflow
- Chunk-to-entities pipeline
- Error scenarios and recovery

## 7. Configuration & Documentation

### Configuration Updates:
- Entity extraction parameters in `backend/core/config.py`
- Default entity types and confidence thresholds
- Batch processing configuration

### Documentation:
- Update `project_structure.md` with new files
- Document entity types and extraction parameters
- API endpoint documentation

## 8. Implementation Order

1. **Create Models**: Implement entity-related Pydantic models
2. **EntityExtractionAgent**: Build PydanticAI agent for entity extraction
3. **EntityExtractionService**: Implement business logic and database operations
4. **API Routes**: Create entity management endpoints
5. **Integration**: Connect entity extraction to chunking pipeline
6. **Testing**: Write comprehensive tests
7. **Documentation**: Update project structure and create devlog

## Key Technical Details

### Entity Types:
```python
ENTITY_TYPES = {
    "PERSON": "Person names and individual entities",
    "ORGANIZATION": "Companies, institutions, groups",
    "LOCATION": "Places, addresses, geographical entities",
    "DATE": "Dates, times, temporal expressions",
    "EVENT": "Events, meetings, occurrences",
    "CONCEPT": "Abstract concepts, topics, themes"
}
```

### PydanticAI Agent Configuration:
```python
entity_extraction_agent = Agent(
    model='openai:gpt-4o-mini',
    result_type=EntityExtractionResult,
    system_prompt="""
    Extract entities from the given text chunk.
    Return structured entities with types and confidence scores.
    
    Entity types: PERSON, ORGANIZATION, LOCATION, DATE, EVENT, CONCEPT
    """,
)
```

### Database Operations:
- Batch insert entities for efficiency
- Maintain proper foreign key relationships to chunks
- Index entities for fast retrieval by type and name

### Error Handling:
- Entity extraction failures should not break chunk processing
- Graceful degradation and retry mechanisms
- Proper logging with Logfire integration

## Success Criteria

✅ Chunks can be processed to extract structured entities  
✅ Entities are stored in database with proper relationships  
✅ API endpoints work for entity management  
✅ Integration with existing chunking pipeline  
✅ Comprehensive testing and error handling  
✅ Documentation and devlog completed  

This implementation will provide the foundation for the next phase (relationship extraction) by identifying entities that can be connected through relationships.

## Expected Outcomes

- **Entity Database**: Structured storage of extracted entities
- **API Endpoints**: Full CRUD operations for entity management
- **Processing Pipeline**: Automated entity extraction from chunks
- **Search Foundation**: Entities ready for relationship extraction and search

---

**Estimated Implementation Time**: 2-3 hours  
**Complexity**: Medium (structured AI output, database relationships)  
**Dependencies**: Existing chunking system, pydantic-ai setup  
**Next Phase**: Relationship extraction between entities