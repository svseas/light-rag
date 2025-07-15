# LightRAG Demo Application System Design

## Overview
A demonstration RAG (Retrieval-Augmented Generation) system using PydanticAI, PostgreSQL, FastAPI, and a lightweight frontend.

## Architecture

### Backend Stack
- **FastAPI**: REST API framework
- **PydanticAI**: LLM agent orchestration
- **PostgreSQL**: Main database with pgvector and pgrouting extensions
- **Elasticsearch**: Text search capabilities
- **Redis**: Queue for async processing

### Frontend
- **HTMX + Alpine.js**: Lightweight, server-driven UI
- **TailwindCSS**: Styling

## Database Schema

```sql
-- Documents
documents (
  id, name, original_format, content_md, 
  created_at, updated_at
)

-- Document metadata with summaries
document_metadata (
  doc_id, summary, recursive_summary,
  entity_count, chunk_count, metadata_json
)

-- Chunks with embeddings
chunks (
  id, doc_id, content, chunk_index,
  embedding (vector), tokens, created_at
)

-- Knowledge graph
entities (
  id, name, type, doc_id, chunk_id,
  properties_json
)

relationships (
  id, source_entity_id, target_entity_id,
  relationship_type, doc_id, confidence
)

-- Query history
queries (
  id, query_text, decomposed_queries,
  context_sources, answer, created_at
)
```

## PydanticAI Agents

1. **DocumentProcessor**: Converts docs to markdown using markitdown
2. **ChunkingAgent**: Uses chonkie for intelligent document chunking
3. **SummarizationAgent**: Creates recursive summaries (chunk→section→document)
4. **EntityExtractor**: Extracts entities from text
5. **RelationshipExtractor**: Identifies relationships between entities
6. **EmbeddingAgent**: Generates embeddings using OpenAI/local models
7. **QueryDecomposer**: Breaks complex queries into sub-queries
8. **ContextBuilder**: Combines vector search, text search, and graph traversal
9. **AnswerSynthesizer**: Generates final answers with citations

## Processing Pipeline

### Document Ingestion
1. Upload document (PDF, DOCX, TXT, MD)
2. Convert to markdown (markitdown)
3. Chunk document (chonkie with overlap)
4. Generate embeddings (parallel processing)
5. Extract entities and relationships
6. Build knowledge graph in PostgreSQL
7. Create recursive summaries
8. Index in Elasticsearch

### Query Processing
1. Decompose query into semantic components
2. Execute parallel searches:
   - Vector similarity (pgvector)
   - Text search (Elasticsearch)
   - Graph traversal (pgrouting)
3. Rank and merge results
4. Build context with source tracking
5. Generate answer with citations

## API Endpoints

```
POST   /api/documents/upload
GET    /api/documents
GET    /api/documents/{id}
DELETE /api/documents/{id}

POST   /api/query
GET    /api/query/{id}
WS     /api/query/stream

GET    /api/entities
GET    /api/relationships
GET    /api/graph/visualize
```

## Project Structure

```
light-rag/
├── backend/
│   ├── api/
│   │   ├── routes/
│   │   └── websockets/
│   ├── agents/
│   │   ├── document_processor.py
│   │   ├── chunking.py
│   │   ├── summarization.py
│   │   ├── entity_extraction.py
│   │   ├── relationship_extraction.py
│   │   ├── embedding.py
│   │   ├── query_decomposition.py
│   │   ├── context_builder.py
│   │   └── answer_synthesis.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── dependencies.py
│   ├── models/
│   │   ├── documents.py
│   │   ├── chunks.py
│   │   ├── entities.py
│   │   └── queries.py
│   ├── services/
│   │   ├── document_service.py
│   │   ├── search_service.py
│   │   └── graph_service.py
│   └── utils/
├── frontend/
│   ├── static/
│   ├── templates/
│   └── components/
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── migrations/
├── tests/
├── scripts/
└── docs/
```

## Key Features

1. **Multi-modal Document Support**: PDF, DOCX, TXT, Markdown
2. **Intelligent Chunking**: Context-aware splitting with overlap
3. **Hybrid Search**: Vector + keyword + graph-based retrieval
4. **Knowledge Graph**: Visual representation of entities and relationships
5. **Streaming Responses**: Real-time answer generation
6. **Source Attribution**: Clear citations for generated answers
7. **Simple UI**: Clean, responsive interface with HTMX

## Development Plan

### Phase 1: Core Infrastructure
- Set up FastAPI project structure
- Configure PostgreSQL with extensions
- Implement basic document upload and storage
- Create PydanticAI agent framework

### Phase 2: Document Processing
- Integrate markitdown for conversion
- Implement chonkie-based chunking
- Add embedding generation
- Build recursive summarization

### Phase 3: Knowledge Extraction
- Entity extraction with LLM
- Relationship identification
- Graph construction in PostgreSQL
- Elasticsearch indexing

### Phase 4: Query System
- Query decomposition
- Multi-source context building
- Answer synthesis with citations
- Streaming API implementation

### Phase 5: Frontend
- HTMX-based UI
- Document management interface
- Query interface with results
- Simple graph visualization

## Dependencies

```toml
# Core
fastapi = "^0.115.0"
pydantic-ai = "^0.0.10"
uvicorn = "^0.30.0"

# Database
asyncpg = "^0.29.0"
sqlalchemy = "^2.0.0"
pgvector = "^0.3.0"
elasticsearch = "^8.13.0"
redis = "^5.0.0"

# Document Processing
markitdown = "^0.0.1"
chonkie = "^0.1.0"

# ML/AI
openai = "^1.0.0"
numpy = "^1.26.0"
scikit-learn = "^1.5.0"

# Frontend
jinja2 = "^3.1.0"
python-multipart = "^0.0.9"
```

## Implementation Notes

This plan creates a functional demo that showcases modern RAG techniques while remaining manageable in scope. The architecture is designed to be:

- **Modular**: Each agent handles a specific task
- **Scalable**: Async processing with Redis queues
- **Extensible**: Easy to add new document types or search strategies
- **Observable**: Query history and performance tracking
- **User-friendly**: Simple UI with real-time feedback