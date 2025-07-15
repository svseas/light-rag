# Relationship Extraction Agent Implementation Plan

**Date**: 2025-07-15 23:00  
**Feature**: Relationship Extraction Agent  
**Status**: Planning Phase

## 1. Planning & Design ✅

### Feature Requirements:
- **RelationshipExtractionAgent**: PydanticAI agent that extracts relationships between entities
- **Relationship Types**: Various semantic relationships (WORKS_FOR, LOCATED_IN, PART_OF, etc.)
- **Database Storage**: Store relationships with confidence scores and metadata
- **API Endpoints**: Relationship management and retrieval endpoints
- **Graph Integration**: Automatic sync with pgrouting entity_edges table

### Database Schema Updates:
- Relationships table already exists with: id, source_entity_id, target_entity_id, relationship_type, confidence, weight
- Entity_edges table already exists for pgrouting integration
- Triggers already exist for automatic synchronization

### API Endpoints Design:
- `POST /api/relationships/extract` - Extract relationships from entities in a document/chunk
- `GET /api/relationships/documents/{doc_id}` - List relationships for a document
- `GET /api/relationships/entities/{entity_id}` - List relationships for an entity
- `GET /api/relationships/{relationship_id}` - Get specific relationship details
- `DELETE /api/relationships/{relationship_id}` - Delete a relationship
- `GET /api/graph/path/{source_entity_id}/{target_entity_id}` - Find path between entities

## 2. Data Layer Implementation

### Models (`backend/models/relationships.py`):
- `RelationshipBase` - Base relationship model with common fields
- `RelationshipCreate` - Input model for relationship creation
- `RelationshipResponse` - Output model for API responses
- `RelationshipList` - Paginated relationship list
- `RelationshipExtractionRequest` - Request model for extraction operations
- `RelationshipExtractionStatus` - Status tracking for extraction operations
- `GraphPathResponse` - Response model for graph path queries

### Database Operations:
- Use existing relationships table
- Leverage automatic entity_edges synchronization
- Implement relationship retrieval with filtering and pagination

## 3. Business Logic Layer

### RelationshipExtractionAgent (`backend/agents/relationship_extraction.py`):
- PydanticAI agent configured for relationship extraction
- Analyze entity pairs and determine semantic relationships
- Structured output with relationship types and confidence scores
- Context-aware relationship classification

### RelationshipExtractionService (`backend/services/relationship_extraction_service.py`):
- Business logic for relationship management
- Integration with entity extraction service
- Batch processing for entity pairs
- Database persistence for relationships

### GraphService (`backend/services/graph_service.py`):
- Graph analytics and path finding
- Integration with pgrouting functions
- Entity network analysis
- Connected component analysis

## 4. API Layer Implementation

### Routes (`backend/api/routes/relationships.py`):
- Relationship management endpoints
- Proper HTTP status codes and error handling
- Pydantic validation for all inputs/outputs
- Integration with existing entity system

### Graph Routes (`backend/api/routes/graph.py`):
- Graph analytics endpoints
- Path finding and network analysis
- Entity connectivity queries
- Graph visualization support

### Update Main Routes:
- Add relationship and graph routes to `backend/api/main_routes.py`
- Ensure proper route organization

## 5. Integration Points

### Entity Service Integration:
- Extract relationships from entity pairs
- Update relationship counts in entity metadata
- Trigger relationship extraction after entity extraction

### Graph Database Integration:
- Leverage existing pgrouting integration
- Use entity_edges table for graph queries
- Maintain relationship consistency

## 6. Testing Strategy

### Unit Tests:
- `tests/test_agents/test_relationship_extraction.py` - Agent functionality
- `tests/test_services/test_relationship_extraction_service.py` - Service logic
- `tests/test_services/test_graph_service.py` - Graph operations
- `tests/test_api/test_relationships.py` - API endpoints

### Integration Tests:
- End-to-end relationship extraction workflow
- Graph path finding and analytics
- Error scenarios and recovery

## 7. Configuration & Documentation

### Configuration Updates:
- Relationship extraction parameters in `backend/core/config.py`
- Default relationship types and confidence thresholds
- Graph analytics configuration

### Documentation:
- Update `project_structure.md` with new files
- Document relationship types and extraction parameters
- API endpoint documentation

## 8. Implementation Order

1. **Create Models**: Implement relationship-related Pydantic models
2. **RelationshipExtractionAgent**: Build PydanticAI agent for relationship extraction
3. **RelationshipExtractionService**: Implement business logic and database operations
4. **GraphService**: Implement graph analytics and path finding
5. **API Routes**: Create relationship and graph management endpoints
6. **Integration**: Connect relationship extraction to entity pipeline
7. **Testing**: Write comprehensive tests
8. **Documentation**: Update project structure and create devlog

## Key Technical Details

### Relationship Types:
```python
RELATIONSHIP_TYPES = {
    "WORKS_FOR": "Employment or affiliation relationship",
    "LOCATED_IN": "Geographic or spatial relationship",
    "PART_OF": "Hierarchical or component relationship",
    "OWNS": "Ownership or possession relationship",
    "CREATES": "Creation or authorship relationship",
    "USES": "Usage or utilization relationship",
    "COMPETES_WITH": "Competition or rivalry relationship",
    "COLLABORATES_WITH": "Collaboration or partnership relationship",
    "INFLUENCES": "Influence or impact relationship",
    "DEPENDS_ON": "Dependency or reliance relationship",
    "SIMILAR_TO": "Similarity or equivalence relationship",
    "OPPOSES": "Opposition or conflict relationship"
}
```

### PydanticAI Agent Configuration:
```python
relationship_extraction_agent = Agent(
    model='openai:gpt-4o-mini',
    result_type=RelationshipExtractionResult,
    system_prompt="""
    Analyze the given entities and extract semantic relationships between them.
    Return structured relationships with types, confidence scores, and context.
    
    Consider entity context, document content, and semantic meaning.
    """,
)
```

### Database Operations:
- Batch insert relationships for efficiency
- Automatic synchronization with entity_edges table
- Maintain proper foreign key relationships
- Graph queries using pgrouting functions

### Error Handling:
- Relationship extraction failures should not break entity processing
- Graceful degradation for graph operations
- Proper logging with Logfire integration

## Success Criteria

✅ Entity pairs can be processed to extract semantic relationships  
✅ Relationships are stored in database with automatic graph sync  
✅ API endpoints work for relationship management  
✅ Graph analytics provide meaningful insights  
✅ Integration with existing entity extraction pipeline  
✅ Comprehensive testing and error handling  
✅ Documentation and devlog completed  

This implementation will provide advanced graph analytics capabilities and complete the core RAG pipeline with entity relationships.

## Expected Outcomes

- **Relationship Database**: Structured storage of semantic relationships
- **Graph Analytics**: Path finding, connectivity analysis, network insights
- **API Endpoints**: Full CRUD operations for relationship management
- **Knowledge Graph**: Complete entity-relationship knowledge graph
- **Search Enhancement**: Relationship-based search and discovery

## Graph Analytics Features

- **Shortest Path**: Find shortest path between any two entities
- **Connected Components**: Identify entity clusters and communities
- **Centrality Analysis**: Identify most important entities in the graph
- **Relationship Strength**: Weighted relationships based on confidence
- **Network Visualization**: Support for graph visualization tools

---

**Estimated Implementation Time**: 2-3 hours  
**Complexity**: Medium-High (graph operations, relationship semantics)  
**Dependencies**: Existing entity extraction system, pgrouting setup  
**Next Phase**: Embedding generation and vector search