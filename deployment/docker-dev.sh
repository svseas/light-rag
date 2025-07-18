#!/bin/bash

# Docker Development Scripts for LightRAG
# Usage: ./deployment/docker-dev.sh [command]
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

# Check if .env file exists
check_env_file() {
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating from .env.example..."
        cp .env.example .env
        print_warning "Please edit .env file with your actual configuration values"
        return 1
    fi
    return 0
}

# Function to start development environment
start_dev() {
    print_status "Starting LightRAG development environment..."
    
    if ! check_env_file; then
        print_error "Please configure .env file before starting"
        exit 1
    fi
    
    docker-compose -f docker-compose.dev.yml up -d
    print_status "Development environment started!"
    print_info "Application: http://localhost:8000"
    print_info "pgAdmin: http://localhost:8080"
    print_info "Database: localhost:5432"
    print_info "Redis: localhost:6379"
}

# Function to stop development environment
stop_dev() {
    print_status "Stopping LightRAG development environment..."
    docker-compose -f docker-compose.dev.yml down
    print_status "Development environment stopped!"
}

# Function to restart development environment
restart_dev() {
    print_status "Restarting LightRAG development environment..."
    docker-compose -f docker-compose.dev.yml restart
    print_status "Development environment restarted!"
}

# Function to view logs
logs_dev() {
    print_status "Showing logs for development environment..."
    docker-compose -f docker-compose.dev.yml logs -f "${2:-app}"
}

# Function to run database migrations
migrate_dev() {
    print_status "Running database migrations..."
    docker-compose -f docker-compose.dev.yml run --rm migrate
    print_status "Database migrations completed!"
}

# Function to access database shell
db_shell() {
    print_status "Connecting to database shell..."
    docker-compose -f docker-compose.dev.yml exec db psql -U postgres -d lightrag
}

# Function to access application shell
app_shell() {
    print_status "Connecting to application shell..."
    docker-compose -f docker-compose.dev.yml exec app bash
}

# Function to run tests
test_dev() {
    print_status "Running tests..."
    docker-compose -f docker-compose.dev.yml exec app python -m pytest tests/ -v
}

# Function to show status
status_dev() {
    print_status "Development environment status:"
    docker-compose -f docker-compose.dev.yml ps
}

# Function to clean up everything
clean_dev() {
    print_warning "This will remove all containers, volumes, and networks..."
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Cleaning up development environment..."
        docker-compose -f docker-compose.dev.yml down -v --remove-orphans
        docker system prune -f
        print_status "Development environment cleaned!"
    else
        print_info "Operation cancelled."
    fi
}

# Function to build images
build_dev() {
    print_status "Building development images..."
    docker-compose -f docker-compose.dev.yml build --no-cache
    print_status "Development images built!"
}

# Function to show help
show_help() {
    echo "LightRAG Docker Development Scripts"
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start     - Start development environment"
    echo "  stop      - Stop development environment"
    echo "  restart   - Restart development environment"
    echo "  logs      - Show logs (optionally specify service name)"
    echo "  migrate   - Run database migrations"
    echo "  db-shell  - Access database shell"
    echo "  app-shell - Access application shell"
    echo "  test      - Run tests"
    echo "  status    - Show service status"
    echo "  build     - Build development images"
    echo "  clean     - Clean up everything (removes all data)"
    echo "  help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 logs app"
    echo "  $0 logs db"
    echo "  $0 migrate"
    echo "  $0 clean"
}

# Main script logic
case "${1:-help}" in
    start)
        start_dev
        ;;
    stop)
        stop_dev
        ;;
    restart)
        restart_dev
        ;;
    logs)
        logs_dev "$@"
        ;;
    migrate)
        migrate_dev
        ;;
    db-shell)
        db_shell
        ;;
    app-shell)
        app_shell
        ;;
    test)
        test_dev
        ;;
    status)
        status_dev
        ;;
    build)
        build_dev
        ;;
    clean)
        clean_dev
        ;;
    help|*)
        show_help
        ;;
esac