#!/bin/bash

# MentalHealth Platform - Initial Setup Script
# This script sets up the initial configuration and creates an admin user

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
echo -e "${BLUE}MentalHealth Platform - Setup${NC}"
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

# Check if running in Docker or Kubernetes
if [ -f /.dockerenv ]; then
    print_info "Running inside Docker container"
    DEPLOYMENT_TYPE="docker"
elif [ -n "$KUBERNETES_SERVICE_HOST" ]; then
    print_info "Running inside Kubernetes pod"
    DEPLOYMENT_TYPE="k8s"
else
    print_info "Running on host system"
    DEPLOYMENT_TYPE="host"
fi

# Navigate to project root
cd "$PROJECT_ROOT"

# Check for .env file
if [ "$DEPLOYMENT_TYPE" = "host" ]; then
    print_info "Checking for .env file..."
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating default configuration..."

        cat > .env <<EOF
# Database Configuration
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USER=mentalhealth
DATABASE_PASSWORD=changeme123
DATABASE_NAME=mentalhealth_db

# Redis Configuration
REDIS_HOST=localhost
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
        print_success ".env file created"
        print_warning "Please review and update .env file with your configuration"
    else
        print_success ".env file exists"
    fi
fi

# Check Python dependencies
if [ "$DEPLOYMENT_TYPE" = "host" ]; then
    print_info "Checking Python installation..."
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.11 or higher."
        exit 1
    fi
    print_success "Python is installed"

    print_info "Checking pip..."
    if ! command -v pip3 &> /dev/null; then
        print_error "pip is not installed. Please install pip."
        exit 1
    fi
    print_success "pip is installed"

    # Install Python dependencies
    print_info "Installing Python dependencies..."
    pip3 install -r requirements.txt
    print_success "Python dependencies installed"
fi

# Run database migrations
print_info "Running database migrations..."

if [ "$DEPLOYMENT_TYPE" = "docker" ]; then
    docker-compose -f docker-compose.full.yaml exec -T backend alembic upgrade head
elif [ "$DEPLOYMENT_TYPE" = "k8s" ]; then
    BACKEND_POD=$(kubectl get pods -n mentalhealth -l app=backend -o jsonpath='{.items[0].metadata.name}')
    kubectl exec -n mentalhealth $BACKEND_POD -- alembic upgrade head
else
    # Running on host
    cd "$PROJECT_ROOT"
    alembic upgrade head
fi

print_success "Database migrations completed"

# Create admin user
echo ""
print_info "Creating admin user..."
echo ""

# Get admin user details
read -p "$(echo -e ${YELLOW}Enter admin email [admin@mentalhealth.com]: ${NC})" ADMIN_EMAIL
ADMIN_EMAIL=${ADMIN_EMAIL:-admin@mentalhealth.com}

read -p "$(echo -e ${YELLOW}Enter admin username [admin]: ${NC})" ADMIN_USERNAME
ADMIN_USERNAME=${ADMIN_USERNAME:-admin}

read -s -p "$(echo -e ${YELLOW}Enter admin password [admin123]: ${NC})" ADMIN_PASSWORD
echo ""
ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin123}

# Create Python script to create admin user
CREATE_ADMIN_SCRIPT="
import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from src.models.user import User
from src.core.security import get_password_hash
import os
from dotenv import load_dotenv

load_dotenv()

async def create_admin_user():
    # Get database URL from environment
    db_host = os.getenv('DATABASE_HOST', 'localhost')
    db_port = os.getenv('DATABASE_PORT', '5432')
    db_user = os.getenv('DATABASE_USER', 'mentalhealth')
    db_password = os.getenv('DATABASE_PASSWORD', 'changeme123')
    db_name = os.getenv('DATABASE_NAME', 'mentalhealth_db')

    database_url = f'postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'

    # Create engine and session
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Check if admin user exists
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.email == '${ADMIN_EMAIL}')
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                print('Admin user already exists!')
                return

            # Create admin user
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
            print(f'Email: ${ADMIN_EMAIL}')
            print(f'Username: ${ADMIN_USERNAME}')

        except Exception as e:
            print(f'Error creating admin user: {str(e)}')
            await session.rollback()
        finally:
            await engine.dispose()

if __name__ == '__main__':
    asyncio.run(create_admin_user())
"

# Write the script to a temporary file
TEMP_SCRIPT="/tmp/create_admin_user.py"
echo "$CREATE_ADMIN_SCRIPT" > "$TEMP_SCRIPT"

# Run the script based on deployment type
if [ "$DEPLOYMENT_TYPE" = "docker" ]; then
    docker-compose -f docker-compose.full.yaml cp "$TEMP_SCRIPT" backend:/tmp/create_admin_user.py
    docker-compose -f docker-compose.full.yaml exec -T backend python /tmp/create_admin_user.py
elif [ "$DEPLOYMENT_TYPE" = "k8s" ]; then
    BACKEND_POD=$(kubectl get pods -n mentalhealth -l app=backend -o jsonpath='{.items[0].metadata.name}')
    kubectl cp "$TEMP_SCRIPT" "mentalhealth/$BACKEND_POD:/tmp/create_admin_user.py"
    kubectl exec -n mentalhealth $BACKEND_POD -- python /tmp/create_admin_user.py
else
    python3 "$TEMP_SCRIPT"
fi

# Clean up
rm -f "$TEMP_SCRIPT"

print_success "Admin user setup completed"

# Show summary
echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo -e "${GREEN}Admin credentials:${NC}"
echo -e "  Email:    ${BLUE}${ADMIN_EMAIL}${NC}"
echo -e "  Username: ${BLUE}${ADMIN_USERNAME}${NC}"
echo -e "  Password: ${BLUE}${ADMIN_PASSWORD}${NC}"
echo ""
echo -e "${YELLOW}Important:${NC} Please change the admin password after first login!"
echo ""

if [ "$DEPLOYMENT_TYPE" = "docker" ]; then
    echo -e "${BLUE}Access the application at:${NC}"
    echo -e "  Frontend: ${YELLOW}http://localhost:3000${NC}"
    echo -e "  Backend:  ${YELLOW}http://localhost:8080${NC}"
    echo -e "  API Docs: ${YELLOW}http://localhost:8080/docs${NC}"
elif [ "$DEPLOYMENT_TYPE" = "k8s" ]; then
    echo -e "${BLUE}Access the application via:${NC}"
    echo -e "  ${YELLOW}kubectl port-forward -n mentalhealth svc/frontend-service 3000:3000${NC}"
    echo -e "  Then visit: ${YELLOW}http://localhost:3000${NC}"
fi

echo ""
echo -e "${GREEN}Next steps:${NC}"
echo -e "  1. Login with admin credentials"
echo -e "  2. Go to Admin Panel: ${YELLOW}http://localhost:3000/admin${NC}"
echo -e "  3. Upload training datasets"
echo -e "  4. Train AI models"
echo -e "  5. Activate trained models"
echo ""
