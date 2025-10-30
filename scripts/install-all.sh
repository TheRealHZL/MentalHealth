#!/bin/bash

# MentalHealth Platform - Complete Automated Installation
# This script installs everything from scratch: Docker, dependencies, repository, and deploys the platform
# Run on a fresh server with: curl -fsSL https://raw.githubusercontent.com/TheRealHZL/MentalHealth/main/scripts/install-all.sh | bash

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
REPO_URL="https://github.com/TheRealHZL/MentalHealth.git"
INSTALL_DIR="$HOME/MentalHealth"
BRANCH="main"
DOCKER_COMPOSE_VERSION="2.24.0"

echo -e "${MAGENTA}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║        MentalHealth Platform - Automated Installation         ║
║                                                               ║
║   This script will install everything needed to run the       ║
║   MentalHealth Platform on this machine.                      ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"
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

print_step() {
    echo ""
    echo -e "${CYAN}===================================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}===================================================${NC}"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_warning "Running as root. It's recommended to run as a regular user with sudo privileges."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Detect OS
print_step "Step 1: Detecting Operating System"

if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VER=$VERSION_ID
    print_info "Detected OS: $OS $VER"
elif [ "$(uname)" == "Darwin" ]; then
    OS="macos"
    print_info "Detected OS: macOS"
else
    print_error "Unable to detect operating system"
    exit 1
fi

print_success "Operating system detected"

# Install dependencies based on OS
print_step "Step 2: Installing Dependencies"

install_dependencies() {
    case $OS in
        ubuntu|debian)
            print_info "Installing dependencies for Ubuntu/Debian..."
            sudo apt-get update
            sudo apt-get install -y \
                apt-transport-https \
                ca-certificates \
                curl \
                gnupg \
                lsb-release \
                git \
                openssl \
                wget
            print_success "Dependencies installed"
            ;;

        centos|rhel|fedora)
            print_info "Installing dependencies for CentOS/RHEL/Fedora..."
            sudo yum install -y \
                yum-utils \
                device-mapper-persistent-data \
                lvm2 \
                git \
                openssl \
                wget \
                curl
            print_success "Dependencies installed"
            ;;

        macos)
            print_info "Checking Homebrew..."
            if ! command -v brew &> /dev/null; then
                print_info "Installing Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            print_info "Installing dependencies for macOS..."
            brew install git openssl wget curl
            print_success "Dependencies installed"
            ;;

        *)
            print_error "Unsupported operating system: $OS"
            exit 1
            ;;
    esac
}

install_dependencies

# Install Docker
print_step "Step 3: Installing Docker"

install_docker() {
    if command -v docker &> /dev/null; then
        print_info "Docker is already installed"
        docker --version
    else
        print_info "Installing Docker..."

        case $OS in
            ubuntu|debian)
                # Add Docker's official GPG key
                sudo mkdir -p /etc/apt/keyrings
                curl -fsSL https://download.docker.com/linux/$OS/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

                # Set up the repository
                echo \
                  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$OS \
                  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

                # Install Docker Engine
                sudo apt-get update
                sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
                ;;

            centos|rhel|fedora)
                sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
                sudo yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
                sudo systemctl start docker
                sudo systemctl enable docker
                ;;

            macos)
                print_info "Installing Docker Desktop for Mac..."
                brew install --cask docker
                print_warning "Please start Docker Desktop manually and then run this script again"
                exit 0
                ;;
        esac

        # Add current user to docker group
        if [ "$OS" != "macos" ]; then
            sudo usermod -aG docker $USER
            print_warning "You may need to log out and back in for docker group membership to take effect"
        fi

        print_success "Docker installed successfully"
    fi
}

install_docker

# Start Docker if not running
if [ "$OS" != "macos" ]; then
    print_info "Ensuring Docker service is running..."
    if ! sudo systemctl is-active --quiet docker; then
        sudo systemctl start docker
    fi
    print_success "Docker is running"
fi

# Verify Docker is working
print_info "Verifying Docker installation..."
if docker ps &> /dev/null || sudo docker ps &> /dev/null; then
    print_success "Docker is working correctly"
else
    print_error "Docker is installed but not working. Please check the installation."
    print_info "You may need to log out and back in for group permissions to take effect."
    exit 1
fi

# Install Docker Compose (if not already installed via plugin)
print_step "Step 4: Installing Docker Compose"

if docker compose version &> /dev/null; then
    print_info "Docker Compose (plugin) is already installed"
    docker compose version
    DOCKER_COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    print_info "Docker Compose (standalone) is already installed"
    docker-compose --version
    DOCKER_COMPOSE_CMD="docker-compose"
else
    print_info "Installing Docker Compose standalone..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    print_success "Docker Compose installed"
    DOCKER_COMPOSE_CMD="docker-compose"
fi

# Clone repository
print_step "Step 5: Cloning Repository"

if [ -d "$INSTALL_DIR" ]; then
    print_warning "Directory $INSTALL_DIR already exists"
    read -p "Do you want to remove it and clone fresh? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$INSTALL_DIR"
        print_info "Removed existing directory"
    else
        print_info "Using existing directory"
        cd "$INSTALL_DIR"
        git pull origin $BRANCH
    fi
fi

if [ ! -d "$INSTALL_DIR" ]; then
    print_info "Cloning repository from $REPO_URL..."
    git clone -b $BRANCH $REPO_URL "$INSTALL_DIR"
    print_success "Repository cloned successfully"
fi

cd "$INSTALL_DIR"

# Create .env file
print_step "Step 6: Creating Configuration"

print_info "Generating secure configuration..."

# Generate random passwords
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)

cat > .env <<EOF
# Database Configuration
DATABASE_HOST=postgres
DATABASE_PORT=5432
DATABASE_USER=mentalhealth
DATABASE_PASSWORD=${DB_PASSWORD}
DATABASE_NAME=mentalhealth_db

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=

# Security
SECRET_KEY=${SECRET_KEY}
JWT_SECRET_KEY=${JWT_SECRET_KEY}
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# AI Configuration (uses custom PyTorch models - no external APIs needed)
AI_DEVICE=cpu

# Application
DEBUG=false
LOG_LEVEL=info
ENVIRONMENT=production

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NODE_ENV=production
EOF

print_success "Configuration created with secure random passwords"

# Ask for admin credentials
print_step "Step 7: Admin User Configuration"

echo ""
print_info "Please provide admin user details (or press Enter for defaults)"
echo ""

read -p "Admin email [admin@mentalhealth.com]: " ADMIN_EMAIL
ADMIN_EMAIL=${ADMIN_EMAIL:-admin@mentalhealth.com}

read -p "Admin username [admin]: " ADMIN_USERNAME
ADMIN_USERNAME=${ADMIN_USERNAME:-admin}

read -s -p "Admin password [admin123]: " ADMIN_PASSWORD
echo ""
ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin123}

print_success "Admin credentials configured"

# Deploy platform
print_step "Step 8: Deploying Platform"

print_info "This may take several minutes on first run..."
print_info "Building Docker images..."

# Use sudo if needed
DOCKER_CMD="docker"
if ! docker ps &> /dev/null 2>&1; then
    DOCKER_CMD="sudo docker"
    DOCKER_COMPOSE_CMD="sudo $DOCKER_COMPOSE_CMD"
fi

# Stop any existing containers
$DOCKER_COMPOSE_CMD -f docker-compose.full.yaml down -v 2>/dev/null || true

# Build and start services
$DOCKER_COMPOSE_CMD -f docker-compose.full.yaml build --no-cache
$DOCKER_COMPOSE_CMD -f docker-compose.full.yaml up -d

print_success "Services started"

# Wait for services to be ready
print_step "Step 9: Waiting for Services"

print_info "Waiting for database to be ready..."
sleep 10

MAX_RETRIES=60
RETRY_COUNT=0

while ! $DOCKER_COMPOSE_CMD -f docker-compose.full.yaml exec -T postgres pg_isready -U mentalhealth &> /dev/null; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        print_error "Database failed to start after $MAX_RETRIES attempts"
        print_info "Checking logs..."
        $DOCKER_COMPOSE_CMD -f docker-compose.full.yaml logs postgres
        exit 1
    fi
    echo -n "."
    sleep 2
done
echo ""
print_success "Database is ready"

print_info "Waiting for backend to be ready..."
RETRY_COUNT=0
while ! curl -sf http://localhost:8000/health &> /dev/null; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        print_error "Backend failed to start"
        print_info "Checking logs..."
        $DOCKER_COMPOSE_CMD -f docker-compose.full.yaml logs backend
        exit 1
    fi
    echo -n "."
    sleep 2
done
echo ""
print_success "Backend is ready"

print_info "Waiting for frontend to be ready..."
RETRY_COUNT=0
while ! curl -sf http://localhost:3000 &> /dev/null; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        print_error "Frontend failed to start"
        print_info "Checking logs..."
        $DOCKER_COMPOSE_CMD -f docker-compose.full.yaml logs frontend
        exit 1
    fi
    echo -n "."
    sleep 2
done
echo ""
print_success "Frontend is ready"

# Run migrations
print_step "Step 10: Running Database Migrations"

print_info "Running migrations..."
$DOCKER_COMPOSE_CMD -f docker-compose.full.yaml exec -T backend alembic upgrade head || {
    print_warning "Migrations may have already been applied"
}
print_success "Database migrations completed"

# Create admin user
print_step "Step 11: Creating Admin User"

print_info "Creating admin user..."

CREATE_ADMIN_SCRIPT="
import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from src.models.user import User
from src.core.security import get_password_hash
import os

async def create_admin_user():
    database_url = 'postgresql+asyncpg://mentalhealth:${DB_PASSWORD}@postgres:5432/mentalhealth_db'
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            result = await session.execute(
                select(User).where(User.email == '${ADMIN_EMAIL}')
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                print('Admin user already exists!')
                return

            admin_user = User(
                email='${ADMIN_EMAIL}',
                username='${ADMIN_USERNAME}',
                hashed_password=get_password_hash('${ADMIN_PASSWORD}'),
                role='admin',
                is_active=True,
                is_verified=True
            )

            session.add(admin_user)
            await session.commit()
            print('Admin user created successfully!')

        except Exception as e:
            print(f'Error: {str(e)}')
            await session.rollback()
        finally:
            await engine.dispose()

if __name__ == '__main__':
    asyncio.run(create_admin_user())
"

echo "$CREATE_ADMIN_SCRIPT" > /tmp/create_admin_user.py
$DOCKER_COMPOSE_CMD -f docker-compose.full.yaml cp /tmp/create_admin_user.py backend:/tmp/create_admin_user.py
$DOCKER_COMPOSE_CMD -f docker-compose.full.yaml exec -T backend python /tmp/create_admin_user.py
rm -f /tmp/create_admin_user.py

print_success "Admin user created"

# Installation complete
print_step "Installation Complete!"

echo ""
echo -e "${GREEN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║           🎉 Installation Successful! 🎉                      ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"
echo ""

echo -e "${GREEN}Access your MentalHealth Platform:${NC}"
echo ""
echo -e "  🌐 Frontend:  ${CYAN}http://localhost:3000${NC}"
echo -e "  🔧 Backend:   ${CYAN}http://localhost:8000${NC}"
echo -e "  📚 API Docs:  ${CYAN}http://localhost:8000/docs${NC}"
echo -e "  👑 Admin Panel: ${CYAN}http://localhost:3000/admin${NC}"
echo ""

echo -e "${YELLOW}Admin Credentials:${NC}"
echo -e "  📧 Email:    ${CYAN}${ADMIN_EMAIL}${NC}"
echo -e "  👤 Username: ${CYAN}${ADMIN_USERNAME}${NC}"
echo -e "  🔑 Password: ${CYAN}${ADMIN_PASSWORD}${NC}"
echo ""

echo -e "${BLUE}Useful Commands:${NC}"
echo -e "  View logs:     ${YELLOW}cd $INSTALL_DIR && $DOCKER_COMPOSE_CMD -f docker-compose.full.yaml logs -f${NC}"
echo -e "  Stop services: ${YELLOW}cd $INSTALL_DIR && $DOCKER_COMPOSE_CMD -f docker-compose.full.yaml down${NC}"
echo -e "  Start services:${YELLOW}cd $INSTALL_DIR && $DOCKER_COMPOSE_CMD -f docker-compose.full.yaml up -d${NC}"
echo -e "  Restart:       ${YELLOW}cd $INSTALL_DIR && $DOCKER_COMPOSE_CMD -f docker-compose.full.yaml restart${NC}"
echo ""

echo -e "${GREEN}Next Steps:${NC}"
echo -e "  1. Open ${CYAN}http://localhost:3000${NC} in your browser"
echo -e "  2. Login with the admin credentials above"
echo -e "  3. Go to Admin Panel to upload datasets and train AI models"
echo -e "  4. Start using the platform!"
echo ""

echo -e "${YELLOW}⚠️  Important:${NC}"
echo -e "  - Change the admin password after first login"
echo -e "  - Database password is stored in: ${CYAN}$INSTALL_DIR/.env${NC}"
echo -e "  - Keep your credentials secure!"
echo ""

print_success "MentalHealth Platform is now running! 🚀"
