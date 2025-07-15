# Project Management Implementation Plan

**Date**: 2025-07-15 15:30  
**Feature**: Project Management System  
**Priority**: High  

## Overview

Implement a project management system where each authenticated user can create one project for demo purposes. Each project can contain a maximum of 5 documents, with each document not exceeding 5MB, and users can upload up to 5 documents at once.

## Requirements

### Core Features
1. **User Projects**: Each user can create exactly 1 project (demo limitation)
2. **Document Limits**: Maximum 5 documents per project
3. **File Size Limits**: Maximum 5MB per document
4. **Batch Upload**: Upload up to 5 documents simultaneously
5. **Project Isolation**: Documents, chunks, entities, relationships scoped to projects

### Technical Requirements
1. **Authentication**: All project operations require user authentication
2. **Database Design**: Add project_id foreign key to existing tables
3. **API Design**: RESTful endpoints for project management
4. **Validation**: Enforce limits at API and database level
5. **Error Handling**: Clear error messages for limit violations

## Implementation Steps

### 1. Planning & Design ✅
- [x] Define project management requirements
- [ ] Update `docs/system-design.md` with project architecture
- [ ] Create database schema for projects in `migrations/`
- [ ] Design API endpoints and data flow

### 2. Data Layer Implementation
- [ ] Create project models in `backend/models/`
  - Project creation/update models
  - Project response models
  - Document upload models with limits
- [ ] Add project table migration in `migrations/`
- [ ] Update existing tables to include project_id
- [ ] Add proper indexes and constraints

### 3. Business Logic Layer
- [ ] Implement project service in `backend/services/`
  - Project creation with user validation
  - Document limit enforcement
  - File size validation
  - Batch upload handling
- [ ] Update document service for project scoping
- [ ] Add project utilities in `backend/utils/`

### 4. API Layer Implementation
- [ ] Create project routes in `backend/api/routes/`
  - Project CRUD operations
  - Document upload with limits
  - Batch upload endpoint
- [ ] Update existing routes to include project scoping
- [ ] Add project middleware for authentication
- [ ] Update `backend/core/dependencies.py`

### 5. Frontend Implementation
- [ ] Create project templates in `frontend/templates/`
  - Project dashboard
  - Document upload interface
  - Batch upload UI
- [ ] Update CSS for project styling
- [ ] Add JavaScript for file validation

### 6. Testing
- [ ] Write unit tests for project service
- [ ] Test API endpoints with limits
- [ ] Test batch upload functionality
- [ ] Test error scenarios

### 7. Documentation & Configuration
- [ ] Update `project_structure.md`
- [ ] Update `README.md`
- [ ] Add project configuration options
- [ ] Update file size limits in config

### 8. Integration & Deployment
- [ ] Test full project workflow
- [ ] Update database with new schema
- [ ] Test with existing documents

## Database Schema Changes

### New Tables

```sql
-- Projects table
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(128) NOT NULL REFERENCES users(uid),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)  -- One project per user
);
```

### Table Updates

```sql
-- Add project_id to existing tables
ALTER TABLE documents ADD COLUMN project_id UUID NOT NULL REFERENCES projects(id);
ALTER TABLE chunks ADD COLUMN project_id UUID NOT NULL REFERENCES projects(id);
ALTER TABLE entities ADD COLUMN project_id UUID NOT NULL REFERENCES projects(id);
ALTER TABLE relationships ADD COLUMN project_id UUID NOT NULL REFERENCES projects(id);
```

## API Endpoints

### Project Management
- `POST /api/projects` - Create user project (one per user)
- `GET /api/projects/me` - Get current user's project
- `PUT /api/projects/{id}` - Update project details
- `DELETE /api/projects/{id}` - Delete project and all data

### Document Upload
- `POST /api/projects/{id}/documents` - Upload single document
- `POST /api/projects/{id}/documents/batch` - Upload multiple documents
- `GET /api/projects/{id}/documents` - List project documents
- `DELETE /api/projects/{id}/documents/{doc_id}` - Delete document

### Project Statistics
- `GET /api/projects/{id}/stats` - Get project statistics
- `GET /api/projects/{id}/usage` - Check usage limits

## Configuration Changes

```python
# Project limits
MAX_PROJECTS_PER_USER: int = 1
MAX_DOCUMENTS_PER_PROJECT: int = 5
MAX_DOCUMENT_SIZE: int = 5 * 1024 * 1024  # 5MB
MAX_BATCH_UPLOAD_SIZE: int = 5
```

## Models Structure

```python
# Project models
class Project(BaseModel):
    id: UUID
    user_id: str
    name: str
    description: str | None = None
    document_count: int = 0
    created_at: datetime
    updated_at: datetime

class ProjectCreate(BaseModel):
    name: str
    description: str | None = None

class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

class BatchUploadRequest(BaseModel):
    files: list[UploadFile]
    
    def validate_batch_size(self) -> bool:
        return len(self.files) <= 5
```

## Validation Rules

### Project Level
- One project per user maximum
- Project name required and unique per user
- Soft delete projects to maintain data integrity

### Document Level
- Maximum 5 documents per project
- Maximum 5MB per document
- Maximum 5 documents in batch upload
- Supported file types: PDF, DOCX, TXT, MD

### API Level
- Authentication required for all operations
- Project ownership validation
- File size validation before processing
- Batch size validation

## Error Handling

### Business Rules
```python
class ProjectLimitExceededError(Exception):
    """User already has maximum projects"""

class DocumentLimitExceededError(Exception):
    """Project has maximum documents"""

class FileSizeExceededError(Exception):
    """Document exceeds size limit"""

class BatchSizeExceededError(Exception):
    """Batch upload exceeds limit"""
```

### HTTP Status Codes
- 400: Bad Request (validation errors)
- 403: Forbidden (limit exceeded)
- 404: Not Found (project not found)
- 409: Conflict (duplicate project)
- 413: Payload Too Large (file size)

## Security Considerations

1. **Authentication**: All endpoints require valid JWT token
2. **Authorization**: Users can only access their own projects
3. **File Validation**: Validate file types and sizes
4. **Rate Limiting**: Prevent abuse of batch upload
5. **Input Sanitization**: Sanitize project names and descriptions

## Performance Considerations

1. **Database Indexes**: Add indexes on project_id columns
2. **File Upload**: Stream large files for memory efficiency
3. **Batch Processing**: Process uploads asynchronously
4. **Cleanup**: Implement cleanup for failed uploads

## Migration Strategy

1. **Schema Migration**: Add projects table and foreign keys
2. **Data Migration**: Create default projects for existing users
3. **Gradual Rollout**: Implement feature flags for testing
4. **Rollback Plan**: Keep old endpoints for compatibility

## Testing Strategy

### Unit Tests
- Project service business logic
- Document limit validation
- File size validation
- Batch upload processing

### Integration Tests
- Full project workflow
- Document upload with limits
- Error scenarios
- Authentication integration

### Performance Tests
- Batch upload performance
- Large file handling
- Concurrent uploads

## Success Criteria

- [ ] Users can create exactly one project
- [ ] Projects can contain maximum 5 documents
- [ ] Documents are limited to 5MB each
- [ ] Batch upload works for up to 5 documents
- [ ] All existing functionality works with project scoping
- [ ] Proper error handling for all limit violations
- [ ] Clean database schema with proper constraints
- [ ] Comprehensive test coverage
- [ ] Performance meets requirements

## Timeline

- **Day 1**: Planning, database schema, models
- **Day 2**: Project service and API implementation
- **Day 3**: Document upload with limits and batch processing
- **Day 4**: Testing and integration
- **Day 5**: Frontend and documentation

## File Structure

```
backend/
├── models/
│   ├── projects.py          # Project models
│   └── documents.py         # Updated document models
├── services/
│   ├── project_service.py   # Project business logic
│   └── document_service.py  # Updated with project scoping
├── api/
│   ├── routes/
│   │   ├── projects.py      # Project endpoints
│   │   └── documents.py     # Updated document endpoints
│   └── middleware/
│       └── project_middleware.py # Project validation
├── utils/
│   └── file_validation.py   # File validation utilities

migrations/
└── 004_create_projects_table.sql # Project schema

frontend/
├── templates/
│   ├── projects/
│   │   ├── dashboard.html   # Project dashboard
│   │   └── upload.html      # Document upload
└── static/
    └── js/
        └── upload.js        # File upload validation
```

## Dependencies

No new external dependencies required. Will use existing:
- FastAPI for API endpoints
- asyncpg for database operations
- Pydantic for validation
- Python-multipart for file uploads