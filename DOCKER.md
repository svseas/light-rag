# LightRAG Docker Setup

This document explains how to run LightRAG using Docker for both development and production environments.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 4GB of available RAM
- 10GB of available disk space

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd light-rag
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your configuration
nano .env
```

**Required Configuration:**
- `OPENROUTER_API_KEY` - Your OpenRouter API key
- `GOOGLE_API_KEY` - Your Google API key for embeddings
- `FIREBASE_*` - Your Firebase configuration
- `LOGFIRE_TOKEN` - Your Logfire token for observability

### 3. Start Development Environment

```bash
# Using the helper script
./deployment/docker-dev.sh start

# Or using docker-compose directly
docker-compose -f docker-compose.dev.yml up -d
```

### 4. Access the Application

- **Application**: http://localhost:8000
- **pgAdmin**: http://localhost:8080 (admin@lightrag.com / admin)
- **Database**: localhost:5432 (postgres / postgres)

## Development Environment

### Available Services

- **app**: Main LightRAG application with hot reloading
- **db**: PostgreSQL 16 with pgvector extension
- **redis**: Redis for caching
- **pgadmin**: Database administration interface
- **migrate**: Database migration runner (runs once)

### Development Commands

```bash
# Start development environment
./deployment/docker-dev.sh start

# Stop development environment
./deployment/docker-dev.sh stop

# Restart services
./deployment/docker-dev.sh restart

# View logs
./deployment/docker-dev.sh logs        # All services
./deployment/docker-dev.sh logs app    # Application only
./deployment/docker-dev.sh logs db     # Database only

# Run database migrations
./deployment/docker-dev.sh migrate

# Access database shell
./deployment/docker-dev.sh db-shell

# Access application shell
./deployment/docker-dev.sh app-shell

# Run tests
./deployment/docker-dev.sh test

# Check service status
./deployment/docker-dev.sh status

# Build images
./deployment/docker-dev.sh build

# Clean up everything (removes all data)
./deployment/docker-dev.sh clean
```

### Development Features

- **Hot Reloading**: Code changes are automatically reflected
- **Volume Mounting**: Source code is mounted for live editing
- **Debug Mode**: Enabled by default with detailed logging
- **Database Access**: Direct access to PostgreSQL via pgAdmin
- **Isolated Environment**: Separate from production

## Production Environment

### Available Services

- **app**: Main LightRAG application (production build)
- **db**: PostgreSQL 16 with pgvector extension
- **redis**: Redis for caching
- **migrate**: Database migration runner (runs once)

### Production Commands

```bash
# Start production environment
./deployment/docker-prod.sh start

# Stop production environment
./deployment/docker-prod.sh stop

# View logs
./deployment/docker-prod.sh logs

# Run database migrations
./deployment/docker-prod.sh migrate

# Create database backup
./deployment/docker-prod.sh backup-db

# Restore database from backup
./deployment/docker-prod.sh restore-db backup_20231201_120000.sql

# Check service status and resource usage
./deployment/docker-prod.sh status

# Update application (pull, build, restart)
./deployment/docker-prod.sh update

# Scale services
./deployment/docker-prod.sh scale app 3

# Health check
./deployment/docker-prod.sh health
```

### Production Security

- **Non-root user**: Application runs as non-root user
- **Health checks**: Built-in health monitoring
- **Security headers**: Proper security configuration
- **Environment isolation**: Separate production environment
- **Resource limits**: Configured resource constraints

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | OpenRouter API key for LLMs | `sk-...` |
| `GOOGLE_API_KEY` | Google API key for embeddings | `AIza...` |
| `LOGFIRE_TOKEN` | Logfire token for observability | `lf_...` |

### Firebase Configuration

| Variable | Description |
|----------|-------------|
| `FIREBASE_API_KEY` | Firebase API key |
| `FIREBASE_AUTH_DOMAIN` | Firebase auth domain |
| `FIREBASE_PROJECT_ID` | Firebase project ID |
| `FIREBASE_STORAGE_BUCKET` | Firebase storage bucket |
| `FIREBASE_MESSAGING_SENDER_ID` | Firebase sender ID |
| `FIREBASE_APP_ID` | Firebase app ID |
| `FIREBASE_MEASUREMENT_ID` | Firebase measurement ID |
| `FIREBASE_PRIVATE_KEY_ID` | Firebase private key ID |
| `FIREBASE_PRIVATE_KEY` | Firebase private key |
| `FIREBASE_CLIENT_EMAIL` | Firebase client email |
| `FIREBASE_CLIENT_ID` | Firebase client ID |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_PASSWORD` | `postgres` | Database password |
| `DEBUG` | `false` | Debug mode |
| `APP_PORT` | `8000` | Application port |
| `DEFAULT_MODEL` | `claude-3.5-sonnet` | Default LLM model |
| `EMBEDDING_MODEL` | `gemini-embedding-001` | Embedding model |

## Docker Images

### Application Image

- **Base**: `python:3.12-slim`
- **Dependencies**: Installed via UV for fast dependency resolution
- **Security**: Runs as non-root user
- **Size**: ~500MB (optimized with multi-stage build)

### Database Image

- **Base**: `pgvector/pgvector:pg16`
- **Extensions**: pgvector for vector operations
- **Persistence**: Data persisted in named volumes

## Volume Management

### Named Volumes

- `postgres_data`: Database data
- `redis_data`: Redis data
- `uploads_data`: Uploaded files
- `logs_data`: Application logs

### Backup Volumes

```bash
# Create volume backup
docker run --rm -v postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .

# Restore volume backup
docker run --rm -v postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /data
```

## Networking

### Internal Network

Services communicate via the `lightrag-network` bridge network:

- **app** → **db**: Database connections
- **app** → **redis**: Caching
- **pgadmin** → **db**: Database administration

### External Access

- **Application**: Port 8000
- **Database**: Port 5432 (dev only)
- **Redis**: Port 6379 (dev only)
- **pgAdmin**: Port 8080 (dev only)

## Troubleshooting

### Common Issues

1. **Port conflicts**: Change ports in `.env` file
2. **Permission denied**: Ensure scripts are executable
3. **Out of memory**: Increase Docker memory limit
4. **Database connection failed**: Check database is healthy

### Debugging Commands

```bash
# Check service logs
docker-compose logs -f service_name

# Check service health
docker-compose ps

# Access service shell
docker-compose exec service_name bash

# Check resource usage
docker stats

# Check network
docker network ls
docker network inspect lightrag_lightrag-network
```

### Log Locations

- **Application logs**: `/app/logs/app.log`
- **Database logs**: Docker logs
- **Redis logs**: Docker logs

## Performance Optimization

### Resource Limits

Add resource limits to `docker-compose.yml`:

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

### Database Optimization

PostgreSQL configuration for production:

```yaml
services:
  db:
    environment:
      POSTGRES_INITDB_ARGS: "--data-checksums"
    command: >
      postgres
      -c shared_preload_libraries=pg_stat_statements
      -c max_connections=100
      -c shared_buffers=256MB
      -c effective_cache_size=1GB
      -c maintenance_work_mem=64MB
      -c checkpoint_completion_target=0.9
      -c wal_buffers=16MB
      -c default_statistics_target=100
```

## Security Considerations

### Production Security

1. **Change default passwords**: Update all default passwords
2. **Use secrets**: Store sensitive data in Docker secrets
3. **Network security**: Use internal networks only
4. **Regular updates**: Keep images updated
5. **Backup encryption**: Encrypt database backups

### Environment Security

```bash
# Use Docker secrets for sensitive data
echo "super_secret_password" | docker secret create db_password -

# Reference in compose file
services:
  db:
    secrets:
      - db_password
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
```

## Monitoring

### Health Checks

All services include health checks:

```bash
# Check service health
docker-compose ps

# View health check logs
docker inspect lightrag-app | grep -A 20 "Health"
```

### Logging

- **Structured logging**: JSON format for production
- **Log rotation**: Automatic log rotation
- **Centralized logging**: Logfire integration

## Updates and Maintenance

### Updating Images

```bash
# Pull latest images
docker-compose pull

# Rebuild local images
docker-compose build --no-cache

# Restart services
docker-compose up -d
```

### Database Maintenance

```bash
# Run database migrations
./deployment/docker-prod.sh migrate

# Create backup
./deployment/docker-prod.sh backup-db

# Optimize database
docker-compose exec db psql -U postgres -d lightrag -c "VACUUM ANALYZE;"
```

## Support

For issues related to:
- **Docker setup**: Check this documentation
- **Application bugs**: Check application logs
- **Database issues**: Check database logs
- **Performance**: Check resource usage

## License

This Docker setup is part of the LightRAG project and follows the same license terms.