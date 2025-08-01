# LightRAG - Advanced RAG System

LightRAG is a comprehensive Retrieval-Augmented Generation (RAG) system that combines document processing, entity extraction, relationship mapping, and multi-modal search capabilities. It uses Google Gemini for embeddings, supports graph-based analytics, and provides a modern web interface.

## Features

- **Document Processing**: Upload and process PDF files (primary), with experimental support for TXT files
- **Entity & Relationship Extraction**: Advanced NLP with 52+ entity types and 12+ relationship types
- **Vector Search**: 3072-dimensional Google Gemini embeddings with semantic similarity
- **Graph Analytics**: PostgreSQL with pgvector, PostGIS, and pgrouting for graph operations
- **Multi-Modal Search**: Combines keyword, semantic, and graph-based search strategies
- **Firebase Authentication**: Secure user management and project isolation
- **Real-time Processing**: Async pipeline with WebSocket support
- **Docker Deployment**: Containerized setup with automatic migrations

## Prerequisites

### Required Software
- **Docker & Docker Compose**: For containerized deployment
- **Git**: For cloning the repository
- **Python 3.12+**: For local development (optional)

### Required API Keys
- **OpenRouter API Key**: For LLM operations (Claude, etc.)
- **Google API Key**: For Gemini embeddings
- **Firebase Project**: For authentication (optional)
- **Logfire Token**: For observability (optional)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Vietnam-VoDich/light-rag.git
cd light-rag
```

### 2. Environment Setup

Copy the environment template and configure your API keys:

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```env
# Required API Keys
OPENROUTER_API_KEY=your_openrouter_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# OpenAI Configuration (using OpenRouter)
OPENAI_API_KEY=your_openrouter_api_key_here
OPENAI_BASE_URL=https://openrouter.ai/api/v1

# Database Configuration (auto-configured for Docker)
DATABASE_URL=postgresql://postgres:postgres@db:5432/lightrag
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=lightrag

# Application Configuration
DEBUG=false
SECRET_KEY=your-secure-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Model Configuration
DEFAULT_MODEL=anthropic/claude-3.5-sonnet
EMBEDDING_MODEL=gemini-embedding-001

# Optional: Firebase Authentication
FIREBASE_API_KEY=your_firebase_api_key
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_PROJECT_ID=your-project-id
# ... other Firebase config

# Optional: Observability
LOGFIRE_TOKEN=your_logfire_token
```

### 3. Deploy with Docker

```bash
cd deployment
cp ../.env .env  # Copy environment variables
docker compose up --build
```

This will:
- Build a custom PostgreSQL image with pgvector, PostGIS, and pgrouting
- Run all database migrations automatically
- Start the application on http://localhost:8000
- Set up Redis for caching

### 4. Verify Installation

Check that the application is running:

```bash
curl http://localhost:8000/api/health
```

You should see:
```json
{
  "status": "healthy",
  "database_configured": true,
  "timestamp": "2025-07-29T08:00:00Z"
}
```

## Development Setup

### Local Development

If you prefer to run the application locally:

```bash
# Install Python dependencies
pip install uv
uv sync

# Set up local PostgreSQL with extensions
psql -c "CREATE DATABASE lightrag;"
psql -d lightrag -c "CREATE EXTENSION vector;"
psql -d lightrag -c "CREATE EXTENSION postgis;"
psql -d lightrag -c "CREATE EXTENSION pgrouting;"

# Run migrations
uv run python scripts/run_migrations.py

# Start the application
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Project Structure

```
light-rag/
   backend/                 # FastAPI application
      agents/             # PydanticAI agents for processing
      api/                # REST API routes
      core/               # Configuration and dependencies
      models/             # Data models and schemas
      services/           # Business logic
      utils/              # Helper functions
   frontend/               # HTMX-based frontend
      static/             # CSS and JavaScript
      templates/          # HTML templates
      components/         # Reusable components
   deployment/             # Docker configuration
      Dockerfile          # Application container
      Dockerfile.postgres # Custom PostgreSQL with extensions
      docker-compose.yml  # Full stack setup
   migrations/             # Database schema migrations
   scripts/                # Setup and utility scripts
   tests/                  # Test suite
```

## Usage

### Document Upload and Processing

1. **Access the Web Interface**: Navigate to http://localhost:8000
2. **Create Account**: Sign up or log in (if Firebase is configured)
3. **Create Project**: Set up a new project for your documents
4. **Upload Documents**: Drag and drop PDF, DOCX, TXT, or MD files
5. **Processing Pipeline**: Documents are automatically:
   - Chunked into manageable segments
   - Processed for entity extraction (52+ types)
   - Analyzed for relationships (12+ types)
   - Embedded using Google Gemini (3072 dimensions)

### Search and Query

The system provides three search modes:

- **Keyword Search**: Traditional full-text search
- **Semantic Search**: Vector similarity using embeddings
- **Graph Search**: Entity and relationship-based queries

### API Usage

```bash
# Upload a document
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@document.pdf" \
  -F "project_id=your-project-id"

# Search documents
curl -X POST http://localhost:8000/api/queries/search \
  -H "Content-Type: application/json" \
  -d '{"query": "your search query", "limit": 10}'

# Get document entities
curl http://localhost:8000/api/entities?document_id=doc-id

# Get relationships
curl http://localhost:8000/api/relationships?document_id=doc-id
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `OPENROUTER_API_KEY` | OpenRouter API key for LLM operations | Yes | - |
| `GOOGLE_API_KEY` | Google API key for Gemini embeddings | Yes | - |
| `DATABASE_URL` | PostgreSQL connection string | Yes | Auto-configured for Docker |
| `DEFAULT_MODEL` | LLM model for processing | No | `anthropic/claude-3.5-sonnet` |
| `EMBEDDING_MODEL` | Embedding model | No | `gemini-embedding-001` |
| `MAX_FILE_SIZE` | Maximum upload size in bytes | No | `10485760` (10MB) |
| `DEBUG` | Enable debug mode | No | `false` |

### Vector Dimensions

The system uses **3072-dimensional embeddings** from Google Gemini. Due to PostgreSQL pgvector limitations:
- **No specialized vector indexes** (ivfflat/hnsw) for >2000 dimensions
- **Sequential scans** are used for similarity searches
- **Performance** is optimized through chunking and batching

## Deployment

### Production Deployment

For production deployment:

1. **Update Environment Variables**:
   ```env
   DEBUG=false
   SECRET_KEY=generate-strong-secret-key
   ALLOWED_HOSTS=yourdomain.com
   ```

2. **Configure Reverse Proxy** (nginx example):
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **SSL Certificate**: Use Let's Encrypt or your certificate provider

4. **Monitoring**: Configure Logfire or your monitoring solution

### Scaling

- **Horizontal Scaling**: Deploy multiple application containers behind a load balancer
- **Database Scaling**: Use PostgreSQL read replicas for read-heavy workloads
- **Caching**: Redis is included for session and query caching
- **File Storage**: Consider object storage (S3, GCS) for uploaded files

## Troubleshooting

### Common Issues

**Database Connection Failed**
```bash
# Check if PostgreSQL is running
docker compose ps
docker compose logs db
```

**Migration Errors**
```bash
# Run migrations manually
docker exec -it lightrag-db psql -U postgres -d lightrag
# Check applied migrations
SELECT * FROM schema_migrations;
```

**Vector Index Errors**
- This is expected for 3072-dimensional vectors
- The system works without specialized indexes
- Performance impact is minimal for typical use cases

**Out of Memory**
- Increase Docker memory limits
- Reduce batch sizes in configuration
- Monitor resource usage with `docker stats`

### Logs and Debugging

```bash
# Application logs
docker compose logs app

# Database logs
docker compose logs db

# All services
docker compose logs -f
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Follow the coding guidelines in `coding_guideline.md`
4. Run tests: `pytest`
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push to branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: Report bugs on [GitHub Issues](https://github.com/Vietnam-VoDich/light-rag/issues)
- **Documentation**: Check the `docs/` directory for detailed documentation
- **Community**: Join our discussions for questions and support

## Acknowledgments

- **pgvector**: PostgreSQL extension for vector similarity search
- **PydanticAI**: Framework for AI agent development
- **FastAPI**: Modern web framework for building APIs
- **HTMX**: Dynamic HTML without JavaScript complexity
- **Google Gemini**: Advanced embedding generation