#!/bin/bash
# Quick Deploy - Simplified one-command deployment for MentalHealth Platform

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  MentalHealth Platform - Quick Deploy   ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════╝${NC}"
echo ""

# Check Docker
echo -e "${BLUE}[1/5]${NC} Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}ERROR: Docker is not installed!${NC}"
    echo -e "${YELLOW}Install Docker first: https://docs.docker.com/get-docker/${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker is installed${NC}"

# Check Docker Compose
echo -e "${BLUE}[2/5]${NC} Checking Docker Compose..."
if ! docker compose version &> /dev/null && ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}ERROR: Docker Compose is not installed!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose is installed${NC}"

# Create .env if not exists
echo -e "${BLUE}[3/5]${NC} Creating configuration..."
if [ ! -f .env ]; then
    cat > .env <<EOF
DATABASE_HOST=postgres
DATABASE_PORT=5432
DATABASE_USER=mentalhealth
DATABASE_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
DATABASE_NAME=mentalhealth_db

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=

SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

CORS_ORIGINS=http://localhost:3000,http://localhost:8000
AI_DEVICE=cpu
DEBUG=false
LOG_LEVEL=info
ENVIRONMENT=production

NEXT_PUBLIC_API_URL=http://localhost:8000
NODE_ENV=production
EOF
    echo -e "${GREEN}✓ Configuration created${NC}"
else
    echo -e "${GREEN}✓ Configuration exists${NC}"
fi

# Deploy
echo -e "${BLUE}[4/5]${NC} Deploying platform..."
echo -e "${YELLOW}This will take 5-10 minutes on first run...${NC}"

# Stop existing
docker compose -f docker-compose.full.yaml down -v 2>/dev/null || true

# Build and start
docker compose -f docker-compose.full.yaml up -d --build

echo -e "${GREEN}✓ Services started${NC}"

# Wait for services
echo -e "${BLUE}[5/5]${NC} Waiting for services to be ready..."

# Wait for database
echo -n "  Waiting for database"
for i in {1..30}; do
    if docker compose -f docker-compose.full.yaml exec -T postgres pg_isready -U mentalhealth &> /dev/null; then
        break
    fi
    echo -n "."
    sleep 2
done
echo ""
echo -e "${GREEN}✓ Database is ready${NC}"

# Wait for backend
echo -n "  Waiting for backend"
for i in {1..30}; do
    if curl -sf http://localhost:8000/health &> /dev/null; then
        break
    fi
    echo -n "."
    sleep 2
done
echo ""
echo -e "${GREEN}✓ Backend is ready${NC}"

# Wait for frontend
echo -n "  Waiting for frontend"
for i in {1..30}; do
    if curl -sf http://localhost:3000 &> /dev/null; then
        break
    fi
    echo -n "."
    sleep 2
done
echo ""
echo -e "${GREEN}✓ Frontend is ready${NC}"

# Success
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         🎉 Deployment Complete! 🎉       ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Access your platform:${NC}"
echo -e "  🌐 Frontend:  ${BLUE}http://localhost:3000${NC}"
echo -e "  🔧 Backend:   ${BLUE}http://localhost:8000${NC}"
echo -e "  📚 API Docs:  ${BLUE}http://localhost:8000/docs${NC}"
echo -e "  👑 Admin:     ${BLUE}http://localhost:3000/admin${NC}"
echo ""
echo -e "${YELLOW}Create admin user:${NC}"
echo -e "  ${BLUE}./scripts/setup.sh${NC}"
echo ""
echo -e "${YELLOW}View logs:${NC}"
echo -e "  ${BLUE}docker compose -f docker-compose.full.yaml logs -f${NC}"
echo ""
