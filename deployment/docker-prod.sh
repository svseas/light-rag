#!/bin/bash

# Docker Production Scripts for LightRAG
# Usage: ./deployment/docker-prod.sh [command]
# Note: Run this script from the project root directory

set -e

# Change to project root directory
cd "$(dirname "$0")/.."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if .env file exists and has production values
check_env_file() {
    if [ ! -f ".env" ]; then
        print_error ".env file not found. Please create it from .env.example"
        return 1
    fi
    
    # Check for development values that shouldn't be in production
    if grep -q "DEBUG=true" .env; then
        print_error "DEBUG is set to true in .env file. This should be false for production."
        return 1
    fi
    
    if grep -q "your-.*-here" .env; then
        print_error "Found placeholder values in .env file. Please configure all required values."
        return 1
    fi
    
    return 0
}

# Function to start production environment
start_prod() {
    print_status "Starting LightRAG production environment..."
    
    if ! check_env_file; then
        print_error "Please configure .env file properly before starting production"
        exit 1
    fi
    
    # Build images first
    docker-compose -f docker-compose.yml build --no-cache
    
    # Start services
    docker-compose -f docker-compose.yml up -d
    
    print_status "Production environment started!"
    print_info "Application: http://localhost:8000"
    print_warning "Make sure to configure your reverse proxy (nginx, traefik, etc.)"
}

# Function to stop production environment
stop_prod() {
    print_status "Stopping LightRAG production environment..."
    docker-compose -f docker-compose.yml down
    print_status "Production environment stopped!"
}

# Function to restart production environment
restart_prod() {
    print_status "Restarting LightRAG production environment..."
    docker-compose -f docker-compose.yml restart
    print_status "Production environment restarted!"
}

# Function to view logs
logs_prod() {
    print_status "Showing logs for production environment..."
    docker-compose -f docker-compose.yml logs -f "${2:-app}"
}

# Function to run database migrations
migrate_prod() {
    print_status "Running database migrations..."
    docker-compose -f docker-compose.yml run --rm migrate
    print_status "Database migrations completed!"
}

# Function to backup database
backup_db() {
    print_status "Creating database backup..."
    BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
    docker-compose -f docker-compose.yml exec db pg_dump -U postgres lightrag > "$BACKUP_FILE"
    print_status "Database backup created: $BACKUP_FILE"
}

# Function to restore database
restore_db() {
    if [ -z "$2" ]; then
        print_error "Please specify backup file: $0 restore-db <backup_file>"
        exit 1
    fi
    
    if [ ! -f "$2" ]; then
        print_error "Backup file not found: $2"
        exit 1
    fi
    
    print_warning "This will replace all data in the database!"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Restoring database from $2..."
        docker-compose -f docker-compose.yml exec -T db psql -U postgres -d lightrag < "$2"
        print_status "Database restored successfully!"
    else
        print_info "Operation cancelled."
    fi
}

# Function to show status
status_prod() {
    print_status "Production environment status:"
    docker-compose -f docker-compose.yml ps
    echo ""
    print_status "Resource usage:"
    docker stats --no-stream
}

# Function to update application
update_prod() {
    print_status "Updating production application..."
    
    # Pull latest code (assuming this is run from a CI/CD pipeline)
    print_status "Pulling latest images..."
    docker-compose -f docker-compose.yml pull
    
    # Build new images
    print_status "Building new images..."
    docker-compose -f docker-compose.yml build --no-cache
    
    # Stop services
    print_status "Stopping services..."
    docker-compose -f docker-compose.yml down
    
    # Start services
    print_status "Starting updated services..."
    docker-compose -f docker-compose.yml up -d
    
    print_status "Production application updated!"
}

# Function to scale services
scale_prod() {
    if [ -z "$2" ]; then
        print_error "Please specify service and scale: $0 scale <service> <replicas>"
        exit 1
    fi
    
    if [ -z "$3" ]; then
        print_error "Please specify number of replicas: $0 scale <service> <replicas>"
        exit 1
    fi
    
    print_status "Scaling $2 to $3 replicas..."
    docker-compose -f docker-compose.yml up -d --scale "$2=$3"
    print_status "Service scaled successfully!"
}

# Function to check health
health_check() {
    print_status "Checking service health..."
    
    # Check if services are running
    if ! docker-compose -f docker-compose.yml ps | grep -q "Up"; then
        print_error "Some services are not running!"
        docker-compose -f docker-compose.yml ps
        exit 1
    fi
    
    # Check application health endpoint
    if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
        print_status "Application health check: PASSED"
    else
        print_error "Application health check: FAILED"
        exit 1
    fi
    
    # Check database connection
    if docker-compose -f docker-compose.yml exec db pg_isready -U postgres > /dev/null 2>&1; then
        print_status "Database health check: PASSED"
    else
        print_error "Database health check: FAILED"
        exit 1
    fi
    
    print_status "All health checks passed!"
}

# Function to show help
show_help() {
    echo "LightRAG Docker Production Scripts"
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start       - Start production environment"
    echo "  stop        - Stop production environment"
    echo "  restart     - Restart production environment"
    echo "  logs        - Show logs (optionally specify service name)"
    echo "  migrate     - Run database migrations"
    echo "  backup-db   - Create database backup"
    echo "  restore-db  - Restore database from backup file"
    echo "  status      - Show service status and resource usage"
    echo "  update      - Update application (pull, build, restart)"
    echo "  scale       - Scale a service to N replicas"
    echo "  health      - Check service health"
    echo "  help        - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 logs app"
    echo "  $0 backup-db"
    echo "  $0 restore-db backup_20231201_120000.sql"
    echo "  $0 scale app 3"
    echo "  $0 health"
}

# Main script logic
case "${1:-help}" in
    start)
        start_prod
        ;;
    stop)
        stop_prod
        ;;
    restart)
        restart_prod
        ;;
    logs)
        logs_prod "$@"
        ;;
    migrate)
        migrate_prod
        ;;
    backup-db)
        backup_db
        ;;
    restore-db)
        restore_db "$@"
        ;;
    status)
        status_prod
        ;;
    update)
        update_prod
        ;;
    scale)
        scale_prod "$@"
        ;;
    health)
        health_check
        ;;
    help|*)
        show_help
        ;;
esac