#!/bin/bash

###############################################################################
# MindBridge Frontend Rebuild Script
# Clears Next.js cache and rebuilds the frontend container
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   MindBridge Frontend Rebuild Script                  ║${NC}"
echo -e "${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
echo ""

# Step 1: Clear Next.js cache in frontend directory
echo -e "${BLUE}🧹 Clearing Next.js build cache...${NC}"
if [ -d "frontend/.next" ]; then
    rm -rf frontend/.next
    echo -e "${GREEN}✓ Removed frontend/.next${NC}"
else
    echo -e "${YELLOW}⚠ frontend/.next not found (already clean)${NC}"
fi

# Step 2: Clear node_modules/.cache if it exists
if [ -d "frontend/node_modules/.cache" ]; then
    rm -rf frontend/node_modules/.cache
    echo -e "${GREEN}✓ Removed frontend/node_modules/.cache${NC}"
fi

# Step 3: Stop the frontend container
echo ""
echo -e "${BLUE}🛑 Stopping frontend container...${NC}"
docker-compose stop frontend || echo -e "${YELLOW}⚠ Frontend container not running${NC}"

# Step 4: Remove the frontend container
echo -e "${BLUE}🗑️  Removing frontend container...${NC}"
docker-compose rm -f frontend || echo -e "${YELLOW}⚠ Frontend container not found${NC}"

# Step 5: Remove the frontend image to force rebuild
echo -e "${BLUE}🗑️  Removing frontend image...${NC}"
docker rmi mindbridge-frontend || docker rmi $(docker images -q mindbridge-frontend) 2>/dev/null || echo -e "${YELLOW}⚠ Frontend image not found${NC}"

# Step 6: Rebuild and start the frontend
echo ""
echo -e "${BLUE}🔨 Rebuilding frontend container (this may take a few minutes)...${NC}"
docker-compose up -d --build frontend

# Step 7: Show logs
echo ""
echo -e "${GREEN}✅ Frontend rebuild complete!${NC}"
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}📋 To view frontend logs, run:${NC}"
echo -e "${CYAN}   docker-compose logs -f frontend${NC}"
echo ""
echo -e "${YELLOW}🌐 Frontend should be available at:${NC}"
echo -e "${CYAN}   http://localhost:3000${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
