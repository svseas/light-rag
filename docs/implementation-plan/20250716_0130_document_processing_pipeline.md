# Document Processing Pipeline Implementation Plan

**Date:** 2025-01-16 01:30  
**Updated:** 2025-01-16 01:45  
**Feature:** Complete document processing pipeline with automatic chunking, embedding, entity/relationship extraction, and knowledge graph visualization

## Requirements

### Core Functionality
1. **Separated Upload & Processing**: Upload completes fast, processing starts automatically from frontend
2. **AI-Powered Analysis**: Auto extract entities, relationships, create graph nodes/edges  
3. **Real-time Updates**: Frontend shows processing status and knowledge graph updates
4. **Non-blocking Architecture**: Processing doesn't block user interface

### Revised User Flow
1. User uploads document via frontend
2. **Upload completes immediately** (fast response)
3. **Frontend automatically triggers processing** (no user button needed)
4. Backend processes document in sequence:
   - Document processing (markitdown) - already done during upload
   - Text chunking (chonkie)
   - Embedding generation (Google Gemini)
   - Entity extraction (PydanticAI)
   - Relationship extraction (PydanticAI)
   - Graph construction
5. **Frontend shows real-time progress** via WebSocket/polling
6. **Knowledge graph updates live** as processing completes

## Implementation Steps

### 1. Planning & Design ✅

#### Database Schema Updates
- No new migrations needed - existing schema supports the pipeline
- Tables available: documents, chunks, entities, relationships, embeddings

#### API Endpoints Design
- Keep `/documents/upload` fast (no processing trigger)
- Add `/documents/{id}/process` endpoint to start pipeline
- Add `/pipeline/{execution_id}/status` for status polling
- Add `/entities/project/{id}` and `/relationships/project/{id}` for knowledge graph
- Add WebSocket `/ws/pipeline/{execution_id}` for real-time updates

### 2. Data Layer Implementation

#### Models Enhancement
- [ ] Update document models to include processing status
- [ ] Add pipeline status tracking models
- [ ] Create response models for knowledge graph data

### 3. Business Logic Layer

#### Services Implementation
- [ ] Create `DocumentPipelineService` orchestrating all processing steps
- [ ] Enhance existing services for async processing
- [ ] Add error handling and retry logic for pipeline failures

#### Agent Integration
- [ ] Integrate existing agents into pipeline workflow
- [ ] Add graph construction logic
- [ ] Implement batch processing for efficiency

### 4. API Layer Implementation

#### Route Updates
- [ ] Keep document upload route simple (fast response)
- [ ] Add `POST /documents/{id}/process` endpoint
- [ ] Add `GET /pipeline/{execution_id}/status` endpoint
- [ ] Add knowledge graph data endpoints (`/entities/project/{id}`, `/relationships/project/{id}`)
- [ ] Add WebSocket endpoint `/ws/pipeline/{execution_id}`

### 5. Frontend Implementation

#### Knowledge Graph Visualization
- [ ] Add entity display components
- [ ] Add relationship visualization
- [ ] Add graph interaction features
- [ ] Update document upload feedback

#### Frontend Processing Flow
- [ ] Auto-trigger processing after successful upload
- [ ] Add processing status indicators and progress bars
- [ ] Add WebSocket client for real-time updates
- [ ] Add live knowledge graph updates
- [ ] Add retry capability for failed processing

### 6. Testing & Integration

#### Testing Strategy
- [ ] Unit tests for pipeline service
- [ ] Integration tests for full workflow
- [ ] Frontend interaction testing
- [ ] Performance testing with multiple documents

## Technical Architecture

### Processing Pipeline Flow
```
Frontend Upload → Upload Response (fast) → Auto-trigger Processing
                                              ↓
Document Processing → Chunking → Embedding Generation → Entity Extraction
                                                           ↓
Knowledge Graph Updates ← Graph Construction ← Relationship Extraction
                                ↓
Real-time Frontend Updates (WebSocket)
```

### Technology Stack
- **Backend**: FastAPI, asyncio for async processing
- **AI/ML**: PydanticAI agents, Google Gemini API
- **Database**: PostgreSQL with asyncpg
- **Frontend**: HTMX, WebSocket, JavaScript
- **Graph**: D3.js or similar for visualization

### Error Handling
- Graceful degradation if individual steps fail
- Retry logic for transient failures
- User notification of processing status
- Rollback capability for failed pipelines

## Success Criteria

1. **Separation of Concerns**: Upload and processing are decoupled
2. **User Experience**: Upload feels instant, processing happens automatically in background
3. **Real-time Feedback**: Users see processing progress and knowledge graph updates live
4. **Performance**: Upload completes in <5 seconds, processing status updates in real-time
5. **Reliability**: Processing failures don't affect upload, retries available
6. **Scalability**: Multiple documents can process concurrently

## Implementation Advantages

### **Why Frontend Auto-Trigger is Better:**
1. **⚡ Fast Upload**: User gets immediate feedback
2. **🔧 Flexible**: Can add conditions/settings before processing
3. **🛡️ Reliable**: Upload success ≠ processing success (clearer errors)
4. **🔄 Retryable**: Can retry processing without re-upload
5. **📊 Transparent**: Clear separation between upload and processing states
6. **⚖️ Scalable**: Processing doesn't block upload endpoint

### **Frontend Flow:**
```javascript
async function uploadDocument(file) {
    // 1. Upload (fast)
    const uploadResult = await API.post('/documents/upload', formData);
    showToast('Document uploaded successfully!', 'success');
    
    // 2. Auto-trigger processing (automatic, no user button)
    const pipelineResult = await API.post(`/documents/${uploadResult.document_id}/process`);
    
    // 3. Show real-time updates
    connectToPipelineUpdates(pipelineResult.execution_id);
    showProcessingIndicator('Processing document...');
}
```

## Risk Mitigation

1. **Upload/Processing Separation**: Clear error boundaries and user feedback
2. **Processing Failures**: Retry capability without affecting upload
3. **Frontend Responsiveness**: WebSocket for non-blocking real-time updates
4. **User Understanding**: Clear indicators for upload vs processing status
5. **Error Recovery**: Failed processing doesn't invalidate uploaded document