#!/bin/bash

###############################################################################
# MindBridge AI Platform - Automated Update Script
#
# This script automatically updates your MindBridge installation when
# new changes are pushed to GitHub.
#
# Usage:
#   ./update.sh [options]
#
# Options:
#   --check          Check for updates without applying them
#   --force          Force update even if already up to date
#   --no-restart     Don't restart services after update
#   --backup         Create backup before updating
#   --help           Show this help message
#
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHECK_ONLY=false
FORCE_UPDATE=false
NO_RESTART=false
CREATE_BACKUP=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --check)
            CHECK_ONLY=true
            shift
            ;;
        --force)
            FORCE_UPDATE=true
            shift
            ;;
        --no-restart)
            NO_RESTART=true
            shift
            ;;
        --backup)
            CREATE_BACKUP=true
            shift
            ;;
        --help)
            grep "^#" "$0" | grep -v "#!/bin/bash" | sed 's/^# //'
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Functions
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

log_step() {
    echo -e "\n${CYAN}═══════════════════════════════════════${NC}"
    echo -e "${CYAN}🔄 $1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════${NC}\n"
}

# Detect deployment mode
detect_deployment_mode() {
    cd "$SCRIPT_DIR"

    if systemctl is-active --quiet mindbridge-backend 2>/dev/null; then
        DEPLOY_MODE="local"
        log_info "Detected deployment mode: LOCAL"
    elif command -v docker-compose &> /dev/null && docker-compose ps 2>/dev/null | grep -q "mindbridge"; then
        DEPLOY_MODE="docker"
        log_info "Detected deployment mode: DOCKER"
    elif command -v kubectl &> /dev/null && kubectl get namespace mindbridge &> /dev/null 2>&1; then
        DEPLOY_MODE="kubernetes"
        log_info "Detected deployment mode: KUBERNETES"
    else
        log_error "Could not detect deployment mode"
        log_info "Please run the installation script first: ./install.sh"
        exit 1
    fi
}

# Check for updates
check_updates() {
    log_step "Checking for Updates"

    cd "$SCRIPT_DIR"

    # Fetch latest changes
    git fetch origin

    # Get current and remote commit
    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse @{u})
    BASE=$(git merge-base @ @{u})

    if [[ "$LOCAL" == "$REMOTE" ]]; then
        log_success "Already up to date!"

        if [[ "$FORCE_UPDATE" == false ]]; then
            echo -e "\n${GREEN}No updates available.${NC}"
            echo -e "Current version: $(git rev-parse --short HEAD)"
            exit 0
        else
            log_warning "Forcing update despite being up to date"
        fi
    elif [[ "$LOCAL" == "$BASE" ]]; then
        log_info "Updates available!"

        # Show what changed
        echo -e "\n${CYAN}Changes:${NC}"
        git log --oneline --decorate --graph HEAD..@{u} | head -10

        # Show files changed
        echo -e "\n${CYAN}Files changed:${NC}"
        git diff --stat HEAD..@{u}

        if [[ "$CHECK_ONLY" == true ]]; then
            echo -e "\n${YELLOW}Check-only mode. Run without --check to apply updates.${NC}"
            exit 0
        fi
    elif [[ "$REMOTE" == "$BASE" ]]; then
        log_warning "Local changes detected"
        log_info "Stashing local changes..."
        git stash
    else
        log_warning "Diverged from remote"
        log_info "This will reset to remote version"
    fi
}

# Create backup
create_backup() {
    if [[ "$CREATE_BACKUP" == false ]]; then
        return
    fi

    log_step "Creating Backup"

    BACKUP_DIR="$SCRIPT_DIR/backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"

    # Backup configuration
    cp .env "$BACKUP_DIR/" 2>/dev/null || true
    cp .db_password "$BACKUP_DIR/" 2>/dev/null || true

    # Backup database
    if [[ "$DEPLOY_MODE" == "docker" ]]; then
        log_info "Backing up database..."
        docker-compose exec -T postgres pg_dump -U mindbridge_user mindbridge_db | gzip > "$BACKUP_DIR/database.sql.gz"
    elif [[ "$DEPLOY_MODE" == "local" ]]; then
        log_info "Backing up database..."
        sudo -u postgres pg_dump mindbridge_db | gzip > "$BACKUP_DIR/database.sql.gz"
    fi

    # Backup AI models
    if [[ -d "data/models" ]]; then
        log_info "Backing up AI models..."
        cp -r data/models "$BACKUP_DIR/"
    fi

    log_success "Backup created: $BACKUP_DIR"
}

# Pull updates
pull_updates() {
    log_step "Pulling Updates from GitHub"

    cd "$SCRIPT_DIR"

    # Pull latest changes
    git pull origin main

    log_success "Updates pulled successfully"
}

# Update local deployment
update_local() {
    log_step "Updating Local Deployment"

    cd "$SCRIPT_DIR"

    # Activate virtual environment
    if [[ -f "venv/bin/activate" ]]; then
        source venv/bin/activate
    else
        log_error "Virtual environment not found"
        exit 1
    fi

    # Update backend dependencies
    log_info "Updating backend dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt

    # Update frontend dependencies
    log_info "Updating frontend dependencies..."
    cd frontend
    npm install
    npm run build
    cd ..

    # Run database migrations
    log_info "Running database migrations..."
    alembic upgrade head

    # Restart services
    if [[ "$NO_RESTART" == false ]]; then
        log_info "Restarting services..."
        sudo systemctl restart mindbridge-backend
        sudo systemctl restart mindbridge-frontend

        # Wait for services to start
        sleep 5

        # Check status
        if systemctl is-active --quiet mindbridge-backend && systemctl is-active --quiet mindbridge-frontend; then
            log_success "Services restarted successfully"
        else
            log_error "Service restart failed. Check logs with: sudo journalctl -u mindbridge-backend -f"
            exit 1
        fi
    fi

    log_success "Local deployment updated"
}

# Update Docker deployment
update_docker() {
    log_step "Updating Docker Deployment"

    cd "$SCRIPT_DIR"

    # Stop containers
    log_info "Stopping containers..."
    docker-compose down

    # Pull latest images
    log_info "Pulling latest images..."
    docker-compose pull

    # Rebuild containers
    log_info "Rebuilding containers..."
    docker-compose build --no-cache

    # Start containers
    log_info "Starting containers..."
    docker-compose up -d

    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 15

    # Run database migrations
    log_info "Running database migrations..."
    docker-compose exec -T backend alembic upgrade head

    # Check health
    if docker-compose ps | grep -q "Up"; then
        log_success "Docker deployment updated successfully"
    else
        log_error "Container startup failed. Check logs with: docker-compose logs"
        exit 1
    fi
}

# Update Kubernetes deployment
update_kubernetes() {
    log_step "Updating Kubernetes Deployment"

    cd "$SCRIPT_DIR"

    # Build and push new images (if you have a registry)
    # log_info "Building and pushing new images..."
    # docker build -t your-registry/mindbridge-backend:latest backend/
    # docker build -t your-registry/mindbridge-frontend:latest frontend/
    # docker push your-registry/mindbridge-backend:latest
    # docker push your-registry/mindbridge-frontend:latest

    # Apply updated manifests
    log_info "Applying updated Kubernetes manifests..."
    kubectl apply -f k8s/

    # Restart deployments to pick up changes
    if [[ "$NO_RESTART" == false ]]; then
        log_info "Rolling out updates..."
        kubectl rollout restart deployment/backend -n mindbridge
        kubectl rollout restart deployment/frontend -n mindbridge

        # Wait for rollout to complete
        log_info "Waiting for rollout to complete..."
        kubectl rollout status deployment/backend -n mindbridge --timeout=5m
        kubectl rollout status deployment/frontend -n mindbridge --timeout=5m
    fi

    # Run database migrations
    log_info "Running database migrations..."
    BACKEND_POD=$(kubectl get pod -n mindbridge -l app=backend -o jsonpath='{.items[0].metadata.name}')
    kubectl exec -n mindbridge "$BACKEND_POD" -- alembic upgrade head

    log_success "Kubernetes deployment updated successfully"
}

# Verify update
verify_update() {
    log_step "Verifying Update"

    cd "$SCRIPT_DIR"

    case $DEPLOY_MODE in
        local)
            # Check if services are running
            if systemctl is-active --quiet mindbridge-backend && systemctl is-active --quiet mindbridge-frontend; then
                log_success "Services are running"
            else
                log_error "Services are not running"
                return 1
            fi

            # Check backend health
            if curl -sf http://localhost:8080/ping > /dev/null; then
                log_success "Backend is healthy"
            else
                log_warning "Backend health check failed"
            fi
            ;;

        docker)
            # Check if containers are running
            if docker-compose ps | grep -q "Up"; then
                log_success "Containers are running"
            else
                log_error "Containers are not running"
                return 1
            fi

            # Check backend health
            if docker-compose exec -T backend curl -sf http://localhost:8080/ping > /dev/null; then
                log_success "Backend is healthy"
            else
                log_warning "Backend health check failed"
            fi
            ;;

        kubernetes)
            # Check if pods are ready
            if kubectl get pods -n mindbridge | grep -q "Running"; then
                log_success "Pods are running"
            else
                log_error "Pods are not running"
                return 1
            fi
            ;;
    esac

    # Display current version
    CURRENT_VERSION=$(git rev-parse --short HEAD)
    CURRENT_COMMIT=$(git log -1 --pretty=format:"%s")

    echo -e "\n${GREEN}Update completed successfully!${NC}"
    echo -e "${CYAN}Current version:${NC} $CURRENT_VERSION"
    echo -e "${CYAN}Latest commit:${NC} $CURRENT_COMMIT"
}

# Main update flow
main() {
    echo -e "${CYAN}"
    cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   MindBridge AI Platform - Update Manager                    ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}\n"

    # Detect deployment mode
    detect_deployment_mode

    # Check for updates
    check_updates

    # Create backup if requested
    create_backup

    # Pull updates
    pull_updates

    # Update based on deployment mode
    case $DEPLOY_MODE in
        local)
            update_local
            ;;
        docker)
            update_docker
            ;;
        kubernetes)
            update_kubernetes
            ;;
    esac

    # Verify update
    verify_update

    echo -e "\n${GREEN}✨ Update completed successfully!${NC}\n"
}

# Run main
main "$@"
