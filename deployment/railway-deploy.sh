#!/bin/bash

# Railway Deployment Script for LightRAG
# Usage: ./deployment/railway-deploy.sh

set -e

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

print_status "🚀 Railway Deployment Guide for LightRAG"
echo ""

print_info "Prerequisites:"
echo "1. Install Railway CLI: npm install -g @railway/cli"
echo "2. Login to Railway: railway login"
echo "3. Create a new project: railway new"
echo ""

print_info "Deployment Steps:"
echo ""

print_status "Step 1: Create PostgreSQL Database"
echo "In your Railway project dashboard:"
echo "• Click '+ New' or use Ctrl/Cmd + K"
echo "• Select 'PostgreSQL' from templates"
echo "• Note down the database credentials"
echo ""

print_status "Step 2: Set Environment Variables"
echo "Set these variables in Railway dashboard:"
echo ""
echo "# Database Configuration"
echo "DATABASE_URL=postgresql://username:password@host:port/database"
echo "POSTGRES_USER=your_postgres_user"
echo "POSTGRES_PASSWORD=your_postgres_password"
echo "POSTGRES_DB=lightrag"
echo ""
echo "# API Keys (get from your providers)"
echo "OPENROUTER_API_KEY=your_openrouter_api_key"
echo "GOOGLE_API_KEY=your_google_api_key"
echo "LOGFIRE_TOKEN=your_logfire_token"
echo ""
echo "# OpenAI Configuration"
echo "OPENAI_API_KEY=your_openrouter_api_key"
echo "OPENAI_BASE_URL=https://openrouter.ai/api/v1"
echo ""
echo "# Firebase Configuration (if using)"
echo "FIREBASE_API_KEY=your_firebase_api_key"
echo "FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com"
echo "FIREBASE_PROJECT_ID=your_project_id"
echo "# ... other Firebase vars"
echo ""
echo "# Application Configuration"
echo "DEBUG=false"
echo "SECRET_KEY=your_production_secret_key"
echo "ALLOWED_HOSTS=yourdomain.railway.app"
echo "LOG_LEVEL=INFO"
echo ""
echo "# Model Configuration"
echo "DEFAULT_MODEL=anthropic/claude-3.5-sonnet"
echo "EMBEDDING_MODEL=gemini-embedding-001"
echo ""

print_status "Step 3: Deploy Application"
echo "Run these commands in your project directory:"
echo ""
echo "# Connect to Railway project"
echo "railway link"
echo ""
echo "# Deploy the application"
echo "railway up"
echo ""

print_status "Step 4: Run Database Migrations"
echo "After deployment, run migrations:"
echo ""
echo "# Connect to your deployed service"
echo "railway run python -c \"
import asyncio
import asyncpg
from backend.core.database import get_db_pool
from pathlib import Path

async def run_migrations():
    pool = await get_db_pool()
    migrations_dir = Path('migrations')
    
    for migration_file in sorted(migrations_dir.glob('*.sql')):
        print(f'Running migration: {migration_file.name}')
        with open(migration_file, 'r') as f:
            sql = f.read()
        
        async with pool.acquire() as conn:
            await conn.execute(sql)
        
        print(f'Completed: {migration_file.name}')
    
    await pool.close()

asyncio.run(run_migrations())
\""
echo ""

print_status "Step 5: Verify Deployment"
echo "Check these endpoints:"
echo "• https://yourdomain.railway.app/api/health"
echo "• https://yourdomain.railway.app/ (main application)"
echo ""

print_warning "Important Notes:"
echo "• Railway automatically detects the Dockerfile"
echo "• Make sure all environment variables are set"
echo "• PostgreSQL extensions (pgvector, pgrouting) may need manual installation"
echo "• Check Railway logs for any deployment issues"
echo ""

print_info "Helpful Railway Commands:"
echo "railway logs         # View application logs"
echo "railway status       # Check service status"
echo "railway shell        # Access application shell"
echo "railway run <cmd>    # Run commands in deployed environment"
echo ""

print_status "🎉 Deployment guide complete!"
print_info "Visit https://railway.app/docs for more detailed documentation"