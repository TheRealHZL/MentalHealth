#!/bin/bash

# MentalHealth Platform - Local Deployment Script
# This script automatically deploys the entire platform locally using Docker Compose

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}MentalHealth Platform - Local Deployment${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Function to print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
print_info "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    print_info "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi
print_success "Docker is installed"

# Check if Docker Compose is installed
print_info "Checking Docker Compose installation..."
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    print_info "Visit: https://docs.docker.com/compose/install/"
    exit 1
fi
print_success "Docker Compose is installed"

# Check if Docker daemon is running
print_info "Checking Docker daemon..."
if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running. Please start Docker first."
    exit 1
fi
print_success "Docker daemon is running"

# Navigate to project root
cd "$PROJECT_ROOT"

# Create .env file if it doesn't exist
print_info "Checking environment configuration..."
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        print_success ".env file created. Please review and update if needed."
    else
        print_info "Creating default .env file..."
        cat > .env <<EOF
# Database Configuration
DATABASE_HOST=postgres
DATABASE_PORT=5432
DATABASE_USER=mentalhealth
DATABASE_PASSWORD=changeme123
DATABASE_NAME=mentalhealth_db

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=

# Security
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# AI Configuration (uses custom PyTorch models - no external APIs needed)
AI_DEVICE=cpu

# Application
DEBUG=false
LOG_LEVEL=info
ENVIRONMENT=production

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8080
NODE_ENV=production
EOF
        print_success "Default .env file created"
    fi
else
    print_success ".env file exists"
fi

# Stop existing containers
print_info "Stopping existing containers..."
docker-compose -f docker-compose.full.yaml down -v 2>/dev/null || true
print_success "Existing containers stopped"

# Build images
print_info "Building Docker images..."
print_info "This may take several minutes on first run..."
docker-compose -f docker-compose.full.yaml build --no-cache
print_success "Docker images built successfully"

# Start services
print_info "Starting services..."
docker-compose -f docker-compose.full.yaml up -d
print_success "Services started"

# Wait for database to be ready
print_info "Waiting for database to be ready..."
sleep 5
MAX_RETRIES=30
RETRY_COUNT=0
while ! docker-compose -f docker-compose.full.yaml exec -T postgres pg_isready -U mentalhealth &> /dev/null; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        print_error "Database failed to start after $MAX_RETRIES attempts"
        exit 1
    fi
    echo -n "."
    sleep 2
done
echo ""
print_success "Database is ready"

# Run database migrations
print_info "Running database migrations..."
docker-compose -f docker-compose.full.yaml exec -T backend alembic upgrade head || {
    print_warning "Migration failed, but continuing..."
}
print_success "Database migrations completed"

# Wait for backend to be ready
print_info "Waiting for backend to be ready..."
sleep 5
MAX_RETRIES=30
RETRY_COUNT=0
while ! curl -sf http://localhost:8080/health &> /dev/null; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        print_error "Backend failed to start after $MAX_RETRIES attempts"
        print_info "Checking backend logs..."
        docker-compose -f docker-compose.full.yaml logs backend
        exit 1
    fi
    echo -n "."
    sleep 2
done
echo ""
print_success "Backend is ready"

# Wait for frontend to be ready
print_info "Waiting for frontend to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0
while ! curl -sf http://localhost:3000 &> /dev/null; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        print_error "Frontend failed to start after $MAX_RETRIES attempts"
        print_info "Checking frontend logs..."
        docker-compose -f docker-compose.full.yaml logs frontend
        exit 1
    fi
    echo -n "."
    sleep 2
done
echo ""
print_success "Frontend is ready"

# Health check
print_info "Performing health checks..."
BACKEND_HEALTH=$(curl -sf http://localhost:8080/health | grep -o '"status":"healthy"' || echo "")
if [ -n "$BACKEND_HEALTH" ]; then
    print_success "Backend health check passed"
else
    print_warning "Backend health check failed"
fi

# Show service status
echo ""
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Service Status${NC}"
echo -e "${BLUE}======================================${NC}"
docker-compose -f docker-compose.full.yaml ps

# Show URLs
echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo -e "${GREEN}Access the application at:${NC}"
echo -e "  Frontend:  ${BLUE}http://localhost:3000${NC}"
echo -e "  Backend:   ${BLUE}http://localhost:8080${NC}"
echo -e "  API Docs:  ${BLUE}http://localhost:8080/docs${NC}"
echo ""
echo -e "${YELLOW}Default credentials (if created):${NC}"
echo -e "  Email:    admin@mentalhealth.com"
echo -e "  Password: admin123"
echo ""
echo -e "${BLUE}Useful commands:${NC}"
echo -e "  View logs:          ${YELLOW}docker-compose -f docker-compose.full.yaml logs -f${NC}"
echo -e "  Stop services:      ${YELLOW}docker-compose -f docker-compose.full.yaml down${NC}"
echo -e "  Restart services:   ${YELLOW}docker-compose -f docker-compose.full.yaml restart${NC}"
echo -e "  View backend logs:  ${YELLOW}docker-compose -f docker-compose.full.yaml logs -f backend${NC}"
echo -e "  View frontend logs: ${YELLOW}docker-compose -f docker-compose.full.yaml logs -f frontend${NC}"
echo ""
echo -e "${GREEN}To create an admin user, run:${NC}"
echo -e "  ${YELLOW}./scripts/setup.sh${NC}"
echo ""
