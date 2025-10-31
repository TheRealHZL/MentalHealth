#!/bin/bash

###############################################################################
# MindBridge AI Platform - All-in-One Installer
#
# This script fully automates the installation of the MindBridge AI Platform
# including all dependencies, database setup, and deployment.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/YourOrg/MentalHealth/main/install.sh | bash
#   or
#   ./install.sh [options]
#
# Options:
#   --mode <local|docker|kubernetes>   Deployment mode (default: docker)
#   --domain <domain>                  Domain name for production
#   --email <email>                    Email for SSL certificates
#   --skip-deps                        Skip dependency installation
#   --no-models                        Skip AI model training
#   --help                             Show this help message
#
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="${INSTALL_DIR:-/opt/mindbridge}"
REPO_URL="${REPO_URL:-https://github.com/TheRealHZL/MentalHealth.git}"
BRANCH="${BRANCH:-main}"
DEPLOY_MODE="${DEPLOY_MODE:-docker}"
SKIP_DEPS=false
SKIP_MODELS=false
DOMAIN=""
EMAIL=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)
            DEPLOY_MODE="$2"
            shift 2
            ;;
        --domain)
            DOMAIN="$2"
            shift 2
            ;;
        --email)
            EMAIL="$2"
            shift 2
            ;;
        --skip-deps)
            SKIP_DEPS=true
            shift
            ;;
        --no-models)
            SKIP_MODELS=true
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
    echo -e "\n${MAGENTA}════════════════════════════════════════${NC}"
    echo -e "${MAGENTA}🚀 $1${NC}"
    echo -e "${MAGENTA}════════════════════════════════════════${NC}\n"
}

# Detect OS
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
    elif [[ -f /etc/redhat-release ]]; then
        OS="rhel"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    else
        OS="unknown"
    fi

    log_info "Detected OS: $OS $OS_VERSION"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]] && [[ "$DEPLOY_MODE" != "local" ]]; then
        log_warning "Running as root. This is OK for Docker/Kubernetes deployments."
    fi
}

# Install dependencies based on OS
install_dependencies() {
    if [[ "$SKIP_DEPS" == true ]]; then
        log_warning "Skipping dependency installation (--skip-deps)"
        return
    fi

    log_step "Installing System Dependencies"

    case $OS in
        ubuntu|debian)
            log_info "Installing dependencies for Ubuntu/Debian..."
            sudo apt-get update
            sudo apt-get install -y \
                curl \
                wget \
                git \
                build-essential \
                python3 \
                python3-pip \
                python3-venv \
                postgresql \
                postgresql-contrib \
                redis-server \
                nginx \
                certbot \
                python3-certbot-nginx
            log_success "System dependencies installed"
            ;;

        centos|rhel|fedora)
            log_info "Installing dependencies for CentOS/RHEL/Fedora..."
            sudo yum update -y
            sudo yum install -y \
                curl \
                wget \
                git \
                gcc \
                gcc-c++ \
                make \
                python3 \
                python3-pip \
                postgresql \
                postgresql-server \
                postgresql-contrib \
                redis \
                nginx \
                certbot \
                python3-certbot-nginx
            log_success "System dependencies installed"
            ;;

        macos)
            log_info "Installing dependencies for macOS..."
            if ! command -v brew &> /dev/null; then
                log_info "Installing Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            brew update
            brew install git python3 postgresql redis nginx
            log_success "System dependencies installed"
            ;;

        *)
            log_error "Unsupported OS: $OS"
            exit 1
            ;;
    esac
}

# Install Docker
install_docker() {
    if command -v docker &> /dev/null; then
        log_success "Docker already installed: $(docker --version)"
        return
    fi

    log_step "Installing Docker"

    case $OS in
        ubuntu|debian)
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            sudo usermod -aG docker $USER
            rm get-docker.sh
            ;;

        centos|rhel|fedora)
            sudo yum install -y yum-utils
            sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            sudo yum install -y docker-ce docker-ce-cli containerd.io
            sudo systemctl start docker
            sudo systemctl enable docker
            sudo usermod -aG docker $USER
            ;;

        macos)
            log_info "Please install Docker Desktop from https://www.docker.com/products/docker-desktop"
            log_warning "After installing, restart this script"
            exit 1
            ;;
    esac

    log_success "Docker installed successfully"
}

# Install Docker Compose
install_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        log_success "Docker Compose already installed: $(docker-compose --version)"
        return
    fi

    log_step "Installing Docker Compose"

    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose

    log_success "Docker Compose installed successfully"
}

# Install kubectl (for Kubernetes mode)
install_kubectl() {
    if [[ "$DEPLOY_MODE" != "kubernetes" ]]; then
        return
    fi

    if command -v kubectl &> /dev/null; then
        log_success "kubectl already installed: $(kubectl version --client --short 2>/dev/null || kubectl version --client)"
        return
    fi

    log_step "Installing kubectl"

    case $OS in
        ubuntu|debian)
            sudo curl -fsSLo /usr/share/keyrings/kubernetes-archive-keyring.gpg https://packages.cloud.google.com/apt/doc/apt-key.gpg
            echo "deb [signed-by=/usr/share/keyrings/kubernetes-archive-keyring.gpg] https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list
            sudo apt-get update
            sudo apt-get install -y kubectl
            ;;

        centos|rhel|fedora)
            cat <<EOF | sudo tee /etc/yum.repos.d/kubernetes.repo
[kubernetes]
name=Kubernetes
baseurl=https://packages.cloud.google.com/yum/repos/kubernetes-el7-x86_64
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://packages.cloud.google.com/yum/doc/yum-key.gpg https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg
EOF
            sudo yum install -y kubectl
            ;;

        macos)
            brew install kubectl
            ;;
    esac

    log_success "kubectl installed successfully"
}

# Clone repository
clone_repository() {
    log_step "Cloning MindBridge Repository"

    if [[ -d "$INSTALL_DIR" ]]; then
        log_warning "Installation directory already exists: $INSTALL_DIR"
        read -p "Remove and re-clone? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo rm -rf "$INSTALL_DIR"
        else
            log_info "Using existing directory"
            cd "$INSTALL_DIR"
            git pull origin "$BRANCH"
            return
        fi
    fi

    sudo mkdir -p "$(dirname "$INSTALL_DIR")"
    sudo git clone -b "$BRANCH" "$REPO_URL" "$INSTALL_DIR"
    sudo chown -R $USER:$USER "$INSTALL_DIR"
    cd "$INSTALL_DIR"

    log_success "Repository cloned successfully"
}

# Generate configuration
generate_config() {
    log_step "Generating Configuration"

    cd "$INSTALL_DIR"

    # Generate strong secret key
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

    # Generate database password
    DB_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))")

    # Determine environment
    if [[ -n "$DOMAIN" ]]; then
        ENVIRONMENT="production"
        DEBUG="false"
        HTTPS_ONLY="true"
        CORS_ORIGINS="https://$DOMAIN,https://www.$DOMAIN"
        ALLOWED_HOSTS="$DOMAIN,www.$DOMAIN"
    else
        ENVIRONMENT="development"
        DEBUG="true"
        HTTPS_ONLY="false"
        CORS_ORIGINS="*"
        ALLOWED_HOSTS="*"
    fi

    # Create .env file
    cat > .env << EOF
# MindBridge AI Platform Configuration
# Auto-generated on $(date)

# Application
ENVIRONMENT=$ENVIRONMENT
DEBUG=$DEBUG

# Security
SECRET_KEY=$SECRET_KEY
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
DATABASE_URL=postgresql://mindbridge_user:$DB_PASSWORD@localhost:5432/mindbridge_db
DATABASE_ECHO=false

# CORS and Security
ALLOWED_HOSTS=$ALLOWED_HOSTS
CORS_ORIGINS=$CORS_ORIGINS
HTTPS_ONLY=$HTTPS_ONLY

# AI Configuration
AI_ENGINE_ENABLED=true
AI_DEVICE=cpu

# AI Model Configuration
AI_TEMPERATURE=0.7
AI_TOP_P=0.9
AI_TOP_K=50
AI_MAX_LENGTH=512
MAX_RESPONSE_LENGTH=300

# Model Paths
TOKENIZER_PATH=data/models/tokenizer.pkl
EMOTION_MODEL_PATH=data/models/emotion_classifier.pt
MOOD_MODEL_PATH=data/models/mood_predictor.pt
CHAT_MODEL_PATH=data/models/chat_generator.pt

# Rate Limiting
RATE_LIMIT_ENABLED=true
DEFAULT_RATE_LIMIT=100
AUTH_RATE_LIMIT=5

# Logging
LOG_LEVEL=INFO
ANALYTICS_ENABLED=true

# Feature Flags
THERAPIST_VERIFICATION_REQUIRED=true
EMAIL_VERIFICATION_REQUIRED=false
SHARING_ENABLED=true

# Business Logic
MAX_MOOD_ENTRIES_PER_DAY=10
MAX_DREAM_ENTRIES_PER_DAY=5
MAX_THERAPY_NOTES_PER_DAY=20
DEFAULT_SHARE_KEY_EXPIRY_DAYS=90
EOF

    # Save database password for later use
    echo "$DB_PASSWORD" > .db_password
    chmod 600 .db_password

    log_success "Configuration generated"
    log_info "Database password saved to .db_password"
}

# Setup PostgreSQL database
setup_database() {
    log_step "Setting up PostgreSQL Database"

    DB_PASSWORD=$(cat "$INSTALL_DIR/.db_password")

    case $OS in
        ubuntu|debian)
            sudo systemctl start postgresql
            sudo systemctl enable postgresql
            ;;

        centos|rhel|fedora)
            sudo postgresql-setup --initdb
            sudo systemctl start postgresql
            sudo systemctl enable postgresql
            ;;

        macos)
            brew services start postgresql
            ;;
    esac

    # Create database and user
    sudo -u postgres psql << EOF
CREATE DATABASE mindbridge_db;
CREATE USER mindbridge_user WITH ENCRYPTED PASSWORD '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE mindbridge_db TO mindbridge_user;
\q
EOF

    log_success "Database setup completed"
}

# Setup Redis
setup_redis() {
    log_step "Setting up Redis"

    case $OS in
        ubuntu|debian)
            sudo systemctl start redis-server
            sudo systemctl enable redis-server
            ;;

        centos|rhel|fedora)
            sudo systemctl start redis
            sudo systemctl enable redis
            ;;

        macos)
            brew services start redis
            ;;
    esac

    log_success "Redis setup completed"
}

# Install Python dependencies
install_python_deps() {
    log_step "Installing Python Dependencies"

    cd "$INSTALL_DIR"

    if [[ "$DEPLOY_MODE" == "local" ]]; then
        # Create virtual environment
        python3 -m venv venv
        source venv/bin/activate

        # Upgrade pip
        pip install --upgrade pip

        # Install dependencies
        pip install -r requirements.txt

        log_success "Python dependencies installed in virtual environment"
    else
        # For Docker/Kubernetes, dependencies are installed in container
        log_info "Python dependencies will be installed in Docker container"
    fi
}

# Install Node.js dependencies
install_node_deps() {
    log_step "Installing Node.js Dependencies"

    # Install Node.js if not present
    if ! command -v node &> /dev/null; then
        log_info "Installing Node.js..."

        case $OS in
            ubuntu|debian)
                curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
                sudo apt-get install -y nodejs
                ;;

            centos|rhel|fedora)
                curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
                sudo yum install -y nodejs
                ;;

            macos)
                brew install node
                ;;
        esac
    fi

    log_success "Node.js installed: $(node --version)"

    if [[ "$DEPLOY_MODE" == "local" ]]; then
        cd "$INSTALL_DIR/frontend"
        npm install
        log_success "Frontend dependencies installed"
    else
        log_info "Frontend dependencies will be installed in Docker container"
    fi
}

# Train AI models
train_models() {
    if [[ "$SKIP_MODELS" == true ]]; then
        log_warning "Skipping AI model training (--no-models)"
        return
    fi

    log_step "Training AI Models"
    log_info "This may take 10-30 minutes depending on your hardware..."

    cd "$INSTALL_DIR"

    if [[ "$DEPLOY_MODE" == "local" ]]; then
        source venv/bin/activate

        # Generate sample training data
        log_info "Generating sample training data..."
        python -m src.ai.training.data.sample_data_generator

        # Train all models
        log_info "Training emotion classifier..."
        python -m src.ai.training.trainer --model emotion

        log_info "Training mood predictor..."
        python -m src.ai.training.trainer --model mood

        log_info "Training chat generator..."
        python -m src.ai.training.trainer --model chat

        log_info "Training sentiment analyzer..."
        python -m src.ai.training.trainer --model sentiment

        log_success "AI models trained successfully"
    else
        log_info "AI models will be trained after deployment"
    fi
}

# Deploy application
deploy_application() {
    log_step "Deploying MindBridge Application"

    cd "$INSTALL_DIR"

    case $DEPLOY_MODE in
        local)
            deploy_local
            ;;
        docker)
            deploy_docker
            ;;
        kubernetes)
            deploy_kubernetes
            ;;
        *)
            log_error "Unknown deployment mode: $DEPLOY_MODE"
            exit 1
            ;;
    esac
}

# Deploy locally (development)
deploy_local() {
    log_info "Deploying in LOCAL mode..."

    # Run database migrations
    source venv/bin/activate
    cd "$INSTALL_DIR"
    alembic upgrade head

    # Create systemd service for backend
    sudo tee /etc/systemd/system/mindbridge-backend.service > /dev/null << EOF
[Unit]
Description=MindBridge Backend API
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin"
ExecStart=$INSTALL_DIR/venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

    # Create systemd service for frontend
    sudo tee /etc/systemd/system/mindbridge-frontend.service > /dev/null << EOF
[Unit]
Description=MindBridge Frontend
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR/frontend
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/npm start
Restart=always

[Install]
WantedBy=multi-user.target
EOF

    # Start services
    sudo systemctl daemon-reload
    sudo systemctl enable mindbridge-backend
    sudo systemctl enable mindbridge-frontend
    sudo systemctl start mindbridge-backend
    sudo systemctl start mindbridge-frontend

    log_success "Local deployment completed"
    log_info "Backend: http://localhost:8000"
    log_info "Frontend: http://localhost:3000"
}

# Deploy with Docker Compose
deploy_docker() {
    log_info "Deploying with DOCKER COMPOSE..."

    cd "$INSTALL_DIR"

    # Build and start containers
    docker-compose up -d --build

    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    sleep 10

    # Run migrations
    docker-compose exec -T backend alembic upgrade head

    # Train models if not skipped
    if [[ "$SKIP_MODELS" != true ]]; then
        log_info "Training AI models in container..."
        docker-compose exec -T backend python -m src.ai.training.data.sample_data_generator
        docker-compose exec -T backend python -m src.ai.training.trainer --all
    fi

    log_success "Docker deployment completed"
    log_info "Backend: http://localhost:8000"
    log_info "Frontend: http://localhost:3000"
}

# Deploy to Kubernetes
deploy_kubernetes() {
    log_info "Deploying to KUBERNETES..."

    cd "$INSTALL_DIR/k8s"

    # Create namespace
    kubectl apply -f namespace.yaml

    # Create secrets
    kubectl create secret generic mindbridge-secrets \
        --from-literal=secret-key="$SECRET_KEY" \
        --from-literal=db-password="$(cat ../.db_password)" \
        -n mindbridge \
        --dry-run=client -o yaml | kubectl apply -f -

    # Deploy components
    kubectl apply -f configmaps/
    kubectl apply -f postgres/
    kubectl apply -f redis/
    kubectl apply -f backend/
    kubectl apply -f frontend/
    kubectl apply -f ingress/

    # Wait for pods to be ready
    log_info "Waiting for pods to be ready..."
    kubectl wait --for=condition=ready pod -l app=postgres -n mindbridge --timeout=300s
    kubectl wait --for=condition=ready pod -l app=backend -n mindbridge --timeout=300s
    kubectl wait --for=condition=ready pod -l app=frontend -n mindbridge --timeout=300s

    log_success "Kubernetes deployment completed"
    log_info "Access via Ingress at http://your-domain.com"
}

# Setup SSL with Let's Encrypt
setup_ssl() {
    if [[ -z "$DOMAIN" ]] || [[ -z "$EMAIL" ]]; then
        log_warning "Skipping SSL setup (no domain or email provided)"
        return
    fi

    log_step "Setting up SSL with Let's Encrypt"

    # Configure Nginx
    sudo tee /etc/nginx/sites-available/mindbridge > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

    sudo ln -sf /etc/nginx/sites-available/mindbridge /etc/nginx/sites-enabled/
    sudo nginx -t && sudo systemctl restart nginx

    # Obtain SSL certificate
    sudo certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" --email "$EMAIL" --agree-tos --non-interactive

    log_success "SSL setup completed"
}

# Create update script
create_update_script() {
    log_step "Creating Update Script"

    cat > "$INSTALL_DIR/update.sh" << 'EOF'
#!/bin/bash
# MindBridge Update Script
# Auto-generated by installer

set -e

INSTALL_DIR="$(dirname "$(readlink -f "$0")")"
cd "$INSTALL_DIR"

echo "🔄 Updating MindBridge AI Platform..."

# Pull latest changes
git pull origin main

# Update based on deployment mode
if systemctl is-active --quiet mindbridge-backend; then
    echo "📦 Updating local deployment..."
    source venv/bin/activate
    pip install -r requirements.txt
    cd frontend && npm install && cd ..
    alembic upgrade head
    sudo systemctl restart mindbridge-backend
    sudo systemctl restart mindbridge-frontend
elif docker-compose ps | grep -q mindbridge; then
    echo "🐳 Updating Docker deployment..."
    docker-compose down
    docker-compose up -d --build
    docker-compose exec -T backend alembic upgrade head
elif kubectl get namespace mindbridge &> /dev/null; then
    echo "☸️  Updating Kubernetes deployment..."
    kubectl apply -f k8s/
    kubectl rollout restart deployment/backend -n mindbridge
    kubectl rollout restart deployment/frontend -n mindbridge
else
    echo "❌ Could not detect deployment mode"
    exit 1
fi

echo "✅ Update completed successfully!"
EOF

    chmod +x "$INSTALL_DIR/update.sh"

    log_success "Update script created: $INSTALL_DIR/update.sh"
}

# Print completion message
print_completion() {
    log_step "Installation Completed Successfully! 🎉"

    echo -e "${GREEN}"
    cat << "EOF"
    ███╗   ███╗██╗███╗   ██╗██████╗ ██████╗ ██████╗ ██╗██████╗  ██████╗ ███████╗
    ████╗ ████║██║████╗  ██║██╔══██╗██╔══██╗██╔══██╗██║██╔══██╗██╔════╝ ██╔════╝
    ██╔████╔██║██║██╔██╗ ██║██║  ██║██████╔╝██████╔╝██║██║  ██║██║  ███╗█████╗
    ██║╚██╔╝██║██║██║╚██╗██║██║  ██║██╔══██╗██╔══██╗██║██║  ██║██║   ██║██╔══╝
    ██║ ╚═╝ ██║██║██║ ╚████║██████╔╝██████╔╝██║  ██║██║██████╔╝╚██████╔╝███████╗
    ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝╚═════╝  ╚═════╝ ╚══════╝
EOF
    echo -e "${NC}"

    echo -e "\n${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}   MindBridge AI Platform - Installation Summary${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}\n"

    echo -e "${BLUE}📦 Installation Details:${NC}"
    echo -e "   Location: $INSTALL_DIR"
    echo -e "   Mode: $DEPLOY_MODE"
    echo -e "   Environment: $(grep ENVIRONMENT $INSTALL_DIR/.env | cut -d= -f2)"

    echo -e "\n${BLUE}🔗 Access URLs:${NC}"
    if [[ -n "$DOMAIN" ]]; then
        echo -e "   Frontend: https://$DOMAIN"
        echo -e "   Backend API: https://$DOMAIN/api"
        echo -e "   API Docs: https://$DOMAIN/docs"
    else
        echo -e "   Frontend: http://localhost:3000"
        echo -e "   Backend API: http://localhost:8000"
        echo -e "   API Docs: http://localhost:8000/docs"
    fi

    echo -e "\n${BLUE}📝 Useful Commands:${NC}"
    echo -e "   Update: $INSTALL_DIR/update.sh"

    case $DEPLOY_MODE in
        local)
            echo -e "   View Backend Logs: sudo journalctl -u mindbridge-backend -f"
            echo -e "   View Frontend Logs: sudo journalctl -u mindbridge-frontend -f"
            echo -e "   Restart Backend: sudo systemctl restart mindbridge-backend"
            echo -e "   Restart Frontend: sudo systemctl restart mindbridge-frontend"
            ;;
        docker)
            echo -e "   View Logs: docker-compose logs -f"
            echo -e "   Restart: docker-compose restart"
            echo -e "   Stop: docker-compose down"
            echo -e "   Start: docker-compose up -d"
            ;;
        kubernetes)
            echo -e "   View Logs: kubectl logs -n mindbridge -l app=backend"
            echo -e "   View Pods: kubectl get pods -n mindbridge"
            echo -e "   Restart: kubectl rollout restart deployment -n mindbridge"
            ;;
    esac

    echo -e "\n${BLUE}📚 Documentation:${NC}"
    echo -e "   Deployment Guide: $INSTALL_DIR/docs/PRODUCTION_DEPLOYMENT.md"
    echo -e "   API Documentation: $INSTALL_DIR/docs/API.md"

    echo -e "\n${BLUE}🔐 Security Notes:${NC}"
    echo -e "   Database password: $INSTALL_DIR/.db_password"
    echo -e "   Secret key: Stored in $INSTALL_DIR/.env"

    if [[ "$DEPLOY_MODE" == "local" ]] && [[ -z "$DOMAIN" ]]; then
        echo -e "\n${YELLOW}⚠️  Development Mode Warning:${NC}"
        echo -e "   This is a development installation."
        echo -e "   For production, run with --domain and --email options."
    fi

    echo -e "\n${GREEN}✨ MindBridge AI Platform is ready to use!${NC}\n"
}

# Main installation flow
main() {
    echo -e "${CYAN}"
    cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   MindBridge AI Platform - Automated Installer               ║
║   Privacy-first mental health with AI-powered insights       ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}\n"

    log_info "Starting installation..."
    log_info "Mode: $DEPLOY_MODE"

    # Pre-installation checks
    detect_os
    check_root

    # Installation steps
    if [[ "$DEPLOY_MODE" == "docker" ]] || [[ "$DEPLOY_MODE" == "kubernetes" ]]; then
        install_docker
        install_docker_compose
    fi

    if [[ "$DEPLOY_MODE" == "kubernetes" ]]; then
        install_kubectl
    fi

    if [[ "$DEPLOY_MODE" == "local" ]]; then
        install_dependencies
        setup_database
        setup_redis
    fi

    clone_repository
    generate_config

    if [[ "$DEPLOY_MODE" == "local" ]]; then
        install_python_deps
        install_node_deps
        train_models
    fi

    deploy_application

    if [[ -n "$DOMAIN" ]]; then
        setup_ssl
    fi

    create_update_script

    # Completion
    print_completion
}

# Run main installation
main "$@"
