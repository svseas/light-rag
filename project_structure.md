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
├── backend/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── documents.py     # Document endpoints
│   │   │   ├── queries.py       # Query endpoints
│   │   │   ├── entities.py      # Entity endpoints
│   │   │   └── health.py        # Health check
│   │   └── websockets/
│   │       ├── __init__.py
│   │       └── query_stream.py  # WebSocket for streaming
│   ├── agents/
│   │   ├── __init__.py
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
│   │   ├── __init__.py
│   │   ├── config.py            # Configuration management
│   │   ├── database.py          # Database connection
│   │   └── dependencies.py      # FastAPI dependencies
│   ├── models/
│   │   ├── __init__.py
│   │   ├── documents.py         # Document models
│   │   ├── chunks.py            # Chunk models
│   │   ├── entities.py          # Entity/relationship models
│   │   └── queries.py           # Query models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── document_service.py  # Document business logic
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
│   └── README.md                # Database migrations info
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest configuration
│   ├── test_agents/             # Agent tests
│   ├── test_api/                # API tests
│   └── test_services/           # Service tests
└── scripts/
    ├── setup_db.py              # Database setup script
    └── seed_data.py             # Sample data script
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
Database migration files (using Alembic).

### `tests/`
Comprehensive test suite with pytest.

### `scripts/`
Utility scripts for setup and maintenance.

## Notes
- All Python packages include `__init__.py` files
- Follow the structure defined in `docs/system-design.md`
- Update this file when adding new directories or files