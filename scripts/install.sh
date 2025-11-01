#!/bin/bash
# ============================================================================
# MindBridge AI Platform - Installation Script
# ============================================================================
# Enterprise-Ready installation with error handling and validation
# Usage: ./scripts/install.sh [--dev]
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

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 is not installed"
        return 1
    fi
    return 0
}

# ============================================================================
# Pre-flight Checks
# ============================================================================

log_info "Starting MindBridge AI Platform installation..."

# Check required commands
log_info "Checking system requirements..."

REQUIRED_COMMANDS=("python3" "pip3" "docker" "docker-compose" "git")
MISSING_COMMANDS=()

for cmd in "${REQUIRED_COMMANDS[@]}"; do
    if ! check_command "$cmd"; then
        MISSING_COMMANDS+=("$cmd")
    fi
done

if [ ${#MISSING_COMMANDS[@]} -ne 0 ]; then
    log_error "Missing required commands: ${MISSING_COMMANDS[*]}"
    log_info "Please install the missing dependencies and try again"
    exit 1
fi

log_success "All required commands found"

# Check Python version
PYTHON_VERSION=$(python3 --version | awk '{print $2}')
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    log_error "Python $REQUIRED_VERSION or higher required (found $PYTHON_VERSION)"
    exit 1
fi

log_success "Python version OK ($PYTHON_VERSION)"

# ============================================================================
# Environment Setup
# ============================================================================

log_info "Setting up environment..."

# Check for development mode
DEV_MODE=false
if [ "${1:-}" == "--dev" ]; then
    DEV_MODE=true
    log_info "Development mode enabled"
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        log_info "Creating .env from .env.example..."
        cp .env.example .env

        # Generate random SECRET_KEY
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
        sed -i "s/your-secret-key-here/$SECRET_KEY/g" .env

        log_success ".env file created"
        log_warning "Please review and update .env file with your configuration"
    else
        log_error ".env.example not found"
        exit 1
    fi
else
    log_info ".env file already exists"
fi

# ============================================================================
# Directory Structure
# ============================================================================

log_info "Creating directory structure..."

DIRECTORIES=(
    "data/uploads"
    "data/licenses"
    "data/exports"
    "data/models"
    "data/static"
    "logs"
    "tests/unit"
    "tests/integration"
    "tests/e2e"
)

for dir in "${DIRECTORIES[@]}"; do
    mkdir -p "$dir"
done

log_success "Directory structure created"

# ============================================================================
# Python Virtual Environment
# ============================================================================

log_info "Setting up Python virtual environment..."

if [ ! -d "venv" ]; then
    python3 -m venv venv
    log_success "Virtual environment created"
else
    log_info "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
log_info "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# ============================================================================
# Python Dependencies
# ============================================================================

log_info "Installing Python dependencies..."

# Install production dependencies
pip install -r requirements.txt

if [ "$DEV_MODE" = true ]; then
    log_info "Installing development dependencies..."
    pip install -r requirements-dev.txt
    log_success "Development dependencies installed"
fi

log_success "Python dependencies installed"

# ============================================================================
# Database Setup
# ============================================================================

log_info "Setting up database..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    log_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Start database container
log_info "Starting database container..."
docker-compose up -d db

# Wait for database to be ready
log_info "Waiting for database to be ready..."
sleep 5

MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if docker-compose exec -T db pg_isready -U postgres > /dev/null 2>&1; then
        log_success "Database is ready"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        log_error "Database failed to start after $MAX_RETRIES attempts"
        exit 1
    fi

    sleep 2
done

# ============================================================================
# Database Migrations
# ============================================================================

log_info "Running database migrations..."

# Check if alembic is configured
if [ ! -f "alembic.ini" ]; then
    log_error "alembic.ini not found"
    exit 1
fi

# Run migrations
alembic upgrade head

log_success "Database migrations completed"

# ============================================================================
# Module Validation
# ============================================================================

log_info "Validating modules..."

# Check if modules directory exists
if [ ! -d "app/modules" ]; then
    log_error "app/modules directory not found"
    exit 1
fi

# Count modules
MODULE_COUNT=$(find app/modules -name "manifest.json" | wc -l)
log_info "Found $MODULE_COUNT modules"

# Validate each module
INVALID_MODULES=()

for manifest in app/modules/*/manifest.json; do
    module_dir=$(dirname "$manifest")
    module_name=$(basename "$module_dir")

    # Check for required files
    if [ ! -f "$module_dir/routes.py" ]; then
        log_warning "Module $module_name: missing routes.py"
        INVALID_MODULES+=("$module_name")
    fi

    # Validate manifest JSON
    if ! python3 -m json.tool "$manifest" > /dev/null 2>&1; then
        log_warning "Module $module_name: invalid manifest.json"
        INVALID_MODULES+=("$module_name")
    fi
done

if [ ${#INVALID_MODULES[@]} -ne 0 ]; then
    log_warning "Some modules have issues: ${INVALID_MODULES[*]}"
    log_warning "These modules may not load correctly"
else
    log_success "All modules validated successfully"
fi

# ============================================================================
# Code Quality Setup (Dev Mode Only)
# ============================================================================

if [ "$DEV_MODE" = true ]; then
    log_info "Setting up code quality tools..."

    # Install pre-commit hooks
    if check_command "pre-commit"; then
        pre-commit install
        log_success "Pre-commit hooks installed"
    fi

    # Create .pre-commit-config.yaml if it doesn't exist
    if [ ! -f ".pre-commit-config.yaml" ]; then
        cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
      - id: check-toml
      - id: detect-private-key

  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: ['--max-line-length=88', '--extend-ignore=E203,W503']

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ['-c', 'pyproject.toml']
EOF
        log_success "Pre-commit configuration created"
    fi
fi

# ============================================================================
# Test Installation
# ============================================================================

log_info "Testing installation..."

# Test module loader
python3 -c "from app.core.module_loader import ModuleLoader; loader = ModuleLoader(); loader.load_all_modules(); print(f'✅ Loaded {len(loader.modules)} modules')"

# Test database connection
python3 -c "from app.core.database import init_database; import asyncio; asyncio.run(init_database()); print('✅ Database connection OK')"

log_success "Installation tests passed"

# ============================================================================
# Summary
# ============================================================================

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        🎉 MindBridge AI Platform Installed Successfully! 🎉    ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
log_info "Installation Summary:"
echo "  • Python: $PYTHON_VERSION"
echo "  • Modules: $MODULE_COUNT loaded"
echo "  • Database: PostgreSQL (Docker)"
echo "  • Environment: $([ "$DEV_MODE" = true ] && echo "Development" || echo "Production")"
echo ""
log_info "Next Steps:"
echo "  1. Review and update .env file"
echo "  2. Create admin user: python3 create_admin.py"
echo "  3. Start application: ./scripts/start.sh"
echo "  4. Access API docs: http://localhost:8080/docs"
echo ""
log_info "For more information, see:"
echo "  • README.md"
echo "  • docs/MODULE_GUIDE.md"
echo "  • docs/INSTALLATION.md"
echo ""

deactivate
