# Project Structure

```
light-rag/
├── .python-version               # Python version specification
├── .env                          # Environment variables
├── .gitignore                    # Git ignore rules
├── README.md                     # Project README
├── pyproject.toml                # Python project configuration
├── main.py                       # Entry point
├── coding_guideline.md           # Coding standards
├── implement_guideline.md        # Feature implementation guidelines
├── project_structure.md          # This file
├── docs/
│   └── system-design.md          # System design documentation
├── devlog/
│   └── 20250715_1625_devlog.md   # Development logs
├── backend/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main_routes.py         # ✅ Main API router
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── documents.py     # ✅ Document endpoints
│   │   │   ├── chunks.py        # ✅ Chunk endpoints
│   │   │   ├── entities.py      # ✅ Entity endpoints
│   │   │   ├── queries.py       # Query endpoints
│   │   │   └── health.py        # ✅ Health check
│   │   └── websockets/
│   │       ├── __init__.py
│   │       └── query_stream.py  # WebSocket for streaming
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── document_processor.py # ✅ Document processing agent
│   │   ├── chunking.py          # ✅ Chunking agent
│   │   ├── entity_extraction.py # ✅ Entity extraction agent
│   │   ├── summarization.py
│   │   ├── relationship_extraction.py
│   │   ├── embedding.py
│   │   ├── query_decomposition.py
│   │   ├── context_builder.py
│   │   └── answer_synthesis.py
│   ├── app.py                   # ✅ FastAPI application factory
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            # ✅ Configuration with Logfire
│   │   ├── database.py          # Database connection
│   │   └── dependencies.py      # ✅ FastAPI dependencies
│   ├── models/
│   │   ├── __init__.py
│   │   ├── documents.py         # ✅ Document models
│   │   ├── chunks.py            # ✅ Chunk models
│   │   ├── entities.py          # ✅ Entity models (52 types)
│   │   └── queries.py           # Query models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── document_service.py  # ✅ Document business logic
│   │   ├── chunking_service.py  # ✅ Chunking business logic
│   │   ├── entity_extraction_service.py  # ✅ Entity extraction business logic
│   │   ├── search_service.py    # Search operations
│   │   └── graph_service.py     # Graph operations
│   └── utils/
│       ├── __init__.py
│       └── helpers.py           # Utility functions
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css        # Custom styles
│   │   └── js/
│   │       └── app.js           # Frontend JavaScript
│   ├── templates/
│   │   ├── base.html            # Base template
│   │   ├── index.html           # Main page
│   │   ├── documents.html       # Document management
│   │   └── query.html           # Query interface
│   └── components/
│       └── __init__.py          # HTMX components
├── docker/
│   ├── Dockerfile               # Application Dockerfile
│   └── docker-compose.yml       # Full stack composition
├── migrations/
│   ├── 001_create_tables.sql    # ✅ Database schema creation
│   └── 002_fix_entity_schema.sql # ✅ Entity schema fixes and graph support
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest configuration
│   ├── test_agents/             # Agent tests
│   ├── test_api/                # API tests
│   └── test_services/           # Service tests
└── scripts/
    ├── setup_db.py              # ✅ Database setup script
    └── test_document_upload.py  # ✅ Document upload test script
```

## Directory Descriptions


### `backend/`
The main application code following a clean architecture pattern:
- **api/**: FastAPI routes and WebSocket handlers
- **agents/**: PydanticAI agents for various RAG tasks
- **core/**: Core configuration and database setup
- **models/**: Data models and schemas
- **services/**: Business logic layer
- **utils/**: Helper functions and utilities

### `frontend/`
Lightweight HTMX-based frontend:
- **static/**: CSS and JavaScript files
- **templates/**: HTML templates
- **components/**: Reusable HTMX components

### `docker/`
Docker configuration for easy deployment and development.

### `migrations/`
Database migration files with SQL schema definitions.

### `devlog/`
Development logs following YYYYMMDD_HHMM_devlog.md convention.

### `tests/`
Comprehensive test suite with pytest.

### `scripts/`
Utility scripts for setup and maintenance.

## Implementation Status

### ✅ Completed
- **Core Configuration**: Logfire integration, OpenRouter setup
- **FastAPI Application**: Complete web app with CORS and middleware
- **Database Schema**: PostgreSQL with pgvector, pgrouting, asyncpg with graph capabilities
- **Document Models**: Complete Pydantic models with validation
- **DocumentProcessor Agent**: PydanticAI agent with markitdown integration
- **Document Service**: Full asyncpg database implementation with async processing
- **Chunking Agent**: Simple chonkie-based text chunking agent
- **Chunking Service**: Database operations for chunk management
- **Entity Extraction Agent**: PydanticAI agent with 52 comprehensive entity types
- **Entity Extraction Service**: Database operations with orjson optimization
- **API Endpoints**: Document upload, retrieval, status checking, health check, chunk management, entity extraction
- **Database Setup**: Migration scripts and setup utilities with graph database support
- **Testing**: Manual testing with PDF document processing and entity extraction verified

### 🚧 In Progress
- **Relationship Extraction Agent**: Next implementation phase

### ⏳ Pending
- Relationship extraction
- Embedding generation
- Query system (decomposition, context building, answer synthesis)
- Frontend UI (HTMX templates and components)

## Notes
- All Python packages include `__init__.py` files
- Follow the structure defined in `docs/system-design.md`
- Update this file when adding new directories or files
- ✅ indicates implemented files, others are planned