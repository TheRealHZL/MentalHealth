#!/bin/bash
# ============================================================================
# MindBridge AI Platform - Update Script
# ============================================================================
# Safe, repeatable updates with rollback capability
# Usage: ./scripts/update.sh [--skip-backup] [--skip-migrations]
# ============================================================================

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Helper Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# ============================================================================
# Configuration
# ============================================================================

SKIP_BACKUP=false
SKIP_MIGRATIONS=false
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --skip-migrations)
            SKIP_MIGRATIONS=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# ============================================================================
# Pre-Update Checks
# ============================================================================

log_info "Starting MindBridge AI Platform update..."

# Check if we're in the right directory
if [ ! -f "app/main.py" ]; then
    log_error "app/main.py not found. Are you in the project root?"
    exit 1
fi

# Check for uncommitted changes
if [ -d ".git" ]; then
    if ! git diff-index --quiet HEAD --; then
        log_warning "You have uncommitted changes"
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
fi

# ============================================================================
# Backup
# ============================================================================

if [ "$SKIP_BACKUP" = false ]; then
    log_info "Creating backup..."

    mkdir -p "$BACKUP_DIR"

    # Backup database
    if docker-compose ps db | grep -q "Up"; then
        log_info "Backing up database..."
        docker-compose exec -T db pg_dump -U postgres mindbridge > "$BACKUP_DIR/database.sql"
        log_success "Database backed up"
    else
        log_warning "Database container not running, skipping database backup"
    fi

    # Backup .env file
    if [ -f ".env" ]; then
        cp .env "$BACKUP_DIR/.env"
        log_success ".env backed up"
    fi

    # Backup uploads
    if [ -d "data/uploads" ]; then
        cp -r data/uploads "$BACKUP_DIR/uploads"
        log_success "Uploads backed up"
    fi

    log_success "Backup created at $BACKUP_DIR"
else
    log_warning "Skipping backup (--skip-backup flag)"
fi

# ============================================================================
# Git Pull
# ============================================================================

if [ -d ".git" ]; then
    log_info "Pulling latest changes..."

    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    log_info "Current branch: $CURRENT_BRANCH"

    git fetch origin
    git pull origin "$CURRENT_BRANCH"

    log_success "Git pull completed"
else
    log_warning "Not a git repository, skipping git pull"
fi

# ============================================================================
# Python Dependencies
# ============================================================================

log_info "Updating Python dependencies..."

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    log_error "Virtual environment not found. Run ./scripts/install.sh first"
    exit 1
fi

# Update pip
pip install --upgrade pip

# Install/update dependencies
pip install -r requirements.txt --upgrade

log_success "Python dependencies updated"

# ============================================================================
# Database Migrations
# ============================================================================

if [ "$SKIP_MIGRATIONS" = false ]; then
    log_info "Checking for database migrations..."

    # Check if database is running
    if ! docker-compose ps db | grep -q "Up"; then
        log_warning "Database container not running, starting it..."
        docker-compose up -d db
        sleep 5
    fi

    # Get current migration
    CURRENT_MIGRATION=$(alembic current 2>/dev/null | awk '{print $1}' || echo "none")
    log_info "Current migration: $CURRENT_MIGRATION"

    # Check for pending migrations
    PENDING_MIGRATIONS=$(alembic heads 2>/dev/null | awk '{print $1}' || echo "none")

    if [ "$CURRENT_MIGRATION" != "$PENDING_MIGRATIONS" ]; then
        log_info "Running database migrations..."

        # Run migrations
        if alembic upgrade head; then
            NEW_MIGRATION=$(alembic current | awk '{print $1}')
            log_success "Migrated from $CURRENT_MIGRATION to $NEW_MIGRATION"
        else
            log_error "Migration failed"

            # Offer rollback
            log_warning "Do you want to rollback to the previous migration?"
            read -p "Rollback? (y/N) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                alembic downgrade -1
                log_info "Rolled back to $CURRENT_MIGRATION"
            fi

            exit 1
        fi
    else
        log_info "No pending migrations"
    fi
else
    log_warning "Skipping migrations (--skip-migrations flag)"
fi

# ============================================================================
# Module Validation
# ============================================================================

log_info "Validating modules..."

# Count modules
MODULE_COUNT=$(find app/modules -name "manifest.json" | wc -l)
log_info "Found $MODULE_COUNT modules"

# Validate modules
python3 -c "
from app.core.module_loader import ModuleLoader
loader = ModuleLoader()
loader.load_all_modules()
print(f'✅ Loaded {len(loader.modules)} modules')
if loader.failed_count > 0:
    print(f'⚠️  {loader.failed_count} modules failed to load')
    exit(1)
"

log_success "All modules validated"

# ============================================================================
# Restart Services
# ============================================================================

log_info "Restarting services..."

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    # Rebuild and restart
    docker-compose build --no-cache backend frontend
    docker-compose up -d

    log_success "Services restarted"

    # Wait for services to be healthy
    log_info "Waiting for services to be ready..."
    sleep 5

    # Health check
    if curl -f http://localhost:8080/health > /dev/null 2>&1; then
        log_success "Backend is healthy"
    else
        log_error "Backend health check failed"
        exit 1
    fi

    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        log_success "Frontend is healthy"
    else
        log_warning "Frontend health check failed"
    fi
else
    log_info "Services not running. Start with: docker-compose up -d"
fi

# ============================================================================
# Code Quality (Optional)
# ============================================================================

if [ -d "venv" ] && [ -f "requirements-dev.txt" ]; then
    log_info "Running code quality checks..."

    # Black
    if command -v black &> /dev/null; then
        black --check app/ || log_warning "Code formatting issues found (run: black app/)"
    fi

    # Isort
    if command -v isort &> /dev/null; then
        isort --check-only app/ || log_warning "Import sorting issues found (run: isort app/)"
    fi

    # Flake8
    if command -v flake8 &> /dev/null; then
        flake8 app/ || log_warning "Linting issues found"
    fi

    # Bandit (Security)
    if command -v bandit &> /dev/null; then
        bandit -r app/ -ll || log_warning "Security issues found"
    fi
fi

# ============================================================================
# Summary
# ============================================================================

deactivate

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║       🎉 MindBridge AI Platform Updated Successfully! 🎉      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
log_info "Update Summary:"
echo "  • Backup: $([ "$SKIP_BACKUP" = false ] && echo "$BACKUP_DIR" || echo "Skipped")"
echo "  • Migrations: $([ "$SKIP_MIGRATIONS" = false ] && echo "Completed" || echo "Skipped")"
echo "  • Modules: $MODULE_COUNT loaded"
echo "  • Services: $(docker-compose ps | grep -c "Up" || echo "0") running"
echo ""
log_info "Check logs:"
echo "  • Backend: docker-compose logs -f backend"
echo "  • Frontend: docker-compose logs -f frontend"
echo "  • Database: docker-compose logs -f db"
echo ""
log_info "Rollback if needed:"
echo "  • Database: psql < $BACKUP_DIR/database.sql"
echo "  • Code: git reset --hard HEAD~1"
echo ""
