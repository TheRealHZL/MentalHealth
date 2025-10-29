#!/bin/bash

# MindBridge Docker Management Script
# Einfache Befehle für Docker-Verwaltung

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        error "Docker is not running. Please start Docker Desktop."
        exit 1
    fi
    info "Docker is running ✓"
}

# Build containers
build() {
    info "Building Docker containers..."
    docker-compose build
    info "Build complete ✓"
}

# Start all services
start() {
    info "Starting MindBridge services..."
    docker-compose up -d
    info "Services started ✓"
    info "API available at: http://localhost:8000"
    info "API Docs at: http://localhost:8000/docs"
}

# Stop all services
stop() {
    info "Stopping MindBridge services..."
    docker-compose down
    info "Services stopped ✓"
}

# View logs
logs() {
    info "Showing logs (Ctrl+C to exit)..."
    docker-compose logs -f "$@"
}

# Restart services
restart() {
    info "Restarting MindBridge services..."
    docker-compose restart
    info "Services restarted ✓"
}

# Show status
status() {
    info "Service Status:"
    docker-compose ps
}

# Clean up
clean() {
    warn "This will remove all containers, volumes, and images!"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        info "Cleaning up..."
        docker-compose down -v
        docker system prune -f
        info "Cleanup complete ✓"
    else
        info "Cleanup cancelled"
    fi
}

# Database setup
db_setup() {
    info "Setting up database..."
    docker-compose exec api alembic upgrade head
    info "Database setup complete ✓"
}

# Run database migrations
db_migrate() {
    info "Running database migrations..."
    docker-compose exec api alembic upgrade head
    info "Migrations complete ✓"
}

# Access database shell
db_shell() {
    info "Opening database shell..."
    docker-compose exec postgres psql -U mindbridge -d mindbridge
}

# Execute command in API container
exec_api() {
    docker-compose exec api "$@"
}

# Show help
help() {
    cat << EOF
MindBridge Docker Management

Usage: ./docker.sh [command]

Commands:
    build       Build Docker containers
    start       Start all services
    stop        Stop all services
    restart     Restart all services
    logs        Show service logs (add service name for specific logs)
    status      Show status of all services
    clean       Clean up containers, volumes, and images
    
    db-setup    Setup database (run migrations)
    db-migrate  Run database migrations
    db-shell    Open database shell
    
    exec        Execute command in API container
    help        Show this help message

Examples:
    ./docker.sh build
    ./docker.sh start
    ./docker.sh logs api
    ./docker.sh db-migrate
    ./docker.sh exec python --version

EOF
}

# Main
case "$1" in
    build)
        check_docker
        build
        ;;
    start)
        check_docker
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    logs)
        shift
        logs "$@"
        ;;
    status)
        status
        ;;
    clean)
        clean
        ;;
    db-setup)
        db_setup
        ;;
    db-migrate)
        db_migrate
        ;;
    db-shell)
        db_shell
        ;;
    exec)
        shift
        exec_api "$@"
        ;;
    help|--help|-h)
        help
        ;;
    *)
        if [ -z "$1" ]; then
            help
        else
            error "Unknown command: $1"
            echo
            help
            exit 1
        fi
        ;;
esac
