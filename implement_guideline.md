# Implementation Guidelines

## Feature Implementation Steps

When implementing a new feature in the LightRAG project, follow these steps in order:

### 1. Planning & Design
- [ ] Define feature requirements clearly
- [ ] Update `docs/system-design.md` if architecture changes
- [ ] Create/update database schema in `migrations/`
- [ ] Design API endpoints and data flow

### 2. Data Layer Implementation
- [ ] Create/update models in `backend/models/`
  - Define Pydantic models for request/response
  - Create database schemas if needed
- [ ] Add database migrations in `migrations/`
- [ ] Update `backend/core/database.py` if new connections needed

### 3. Business Logic Layer
- [ ] Implement service logic in `backend/services/`
  - Keep business logic separate from API layer
  - Handle data validation and transformation
  - Implement error handling
- [ ] Create/update PydanticAI agents in `backend/agents/` if AI functionality needed
  - Document all LLM prompts clearly
  - Keep agents focused on single responsibilities
- [ ] Add utility functions in `backend/utils/` if needed

### 4. API Layer Implementation
- [ ] Create/update routes in `backend/api/routes/`
  - Use proper HTTP methods and status codes
  - Implement request/response validation with Pydantic
  - Add proper error handling
- [ ] Add WebSocket handlers in `backend/api/websockets/` if real-time features needed
- [ ] Update `backend/core/dependencies.py` for new dependencies

### 5. Frontend Implementation
- [ ] Create/update HTML templates in `frontend/templates/`
  - Use HTMX for dynamic interactions
  - Follow responsive design principles
- [ ] Add JavaScript in `frontend/static/js/` if needed
- [ ] Update CSS in `frontend/static/css/` for styling
- [ ] Create reusable components in `frontend/components/`

### 6. Testing
- [ ] Write unit tests in appropriate `tests/` subdirectory:
  - `tests/test_agents/` for PydanticAI agents
  - `tests/test_api/` for API endpoints
  - `tests/test_services/` for business logic
- [ ] Create test fixtures in `tests/conftest.py`
- [ ] Ensure minimum 80% code coverage
- [ ] Test both success and failure scenarios

### 7. Documentation & Configuration
- [ ] Update `project_structure.md` if new files/directories added
- [ ] Update `README.md` with new feature documentation
- [ ] Add configuration options to `backend/core/config.py` if needed
- [ ] Update `pyproject.toml` with new dependencies

### 8. Integration & Deployment
- [ ] Update `docker/docker-compose.yml` if new services needed
- [ ] Update `docker/Dockerfile` if new dependencies added
- [ ] Create setup scripts in `scripts/` if needed
- [ ] Test full integration locally

## File Naming Conventions

### Backend Files
- **Models**: `{entity_name}.py` (e.g., `documents.py`, `chunks.py`)
- **Services**: `{entity_name}_service.py` (e.g., `document_service.py`)
- **Routes**: `{entity_name}.py` (e.g., `documents.py` for document routes)
- **Agents**: `{functionality}.py` (e.g., `entity_extraction.py`)

### Frontend Files
- **Templates**: `{page_name}.html` (e.g., `documents.html`)
- **Components**: `{component_name}.py` (e.g., `document_upload.py`)

### Test Files
- **Test files**: `test_{module_name}.py` (e.g., `test_document_service.py`)

## Code Organization Best Practices

### Backend Structure
```python
# backend/services/document_service.py
class DocumentService:
    def __init__(self, db_pool):
        self.db_pool = db_pool
    
    async def create_document(self, document_data: DocumentCreate) -> Document:
        # Business logic here
        pass

# backend/api/routes/documents.py
@router.post("/documents", response_model=Document)
async def create_document(
    document_data: DocumentCreate,
    service: DocumentService = Depends(get_document_service)
):
    return await service.create_document(document_data)
```

### Agent Structure
```python
# backend/agents/entity_extraction.py
from pydantic_ai import Agent

extraction_agent = Agent(
    model='openai:gpt-4',
    system_prompt="""
    Extract entities from the given text.
    Return a structured list of entities with their types.
    """,
    result_type=EntityList
)
```

## Error Handling Pattern

### Service Layer
```python
from backend.utils.exceptions import DocumentNotFoundError

async def get_document(self, doc_id: str) -> Document:
    try:
        # Database operation
        pass
    except Exception as e:
        raise DocumentNotFoundError(f"Document {doc_id} not found")
```

### API Layer
```python
from fastapi import HTTPException

try:
    return await service.get_document(doc_id)
except DocumentNotFoundError as e:
    raise HTTPException(status_code=404, detail=str(e))
```

## Database Migration Pattern

1. Create migration file in `migrations/`
2. Use descriptive names: `001_create_documents_table.sql`
3. Include both UP and DOWN migrations
4. Update `scripts/setup_db.py` to run new migrations

## Testing Pattern

```python
# tests/test_services/test_document_service.py
import pytest
from backend.services.document_service import DocumentService

@pytest.fixture
async def document_service():
    # Setup test service
    pass

async def test_create_document(document_service):
    # Test implementation
    pass
```

## Review Checklist

Before marking a feature as complete:
- [ ] All code follows `coding_guideline.md`
- [ ] Tests pass with good coverage
- [ ] Documentation is updated
- [ ] No sensitive data in code
- [ ] Proper error handling implemented
- [ ] Code is properly typed
- [ ] KISS and SOLID principles followed