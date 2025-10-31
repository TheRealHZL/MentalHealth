#!/bin/bash

###############################################################################
# MindBridge AI Platform - Quick Start Script
#
# One-command installation for development and testing
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/TheRealHZL/MentalHealth/main/quickstart.sh | bash
#
###############################################################################

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   MindBridge AI Platform - Quick Start                       ║
║   Get up and running in 5 minutes!                           ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}\n"

# Ask for installation preferences
echo -e "${BLUE}Choose installation mode:${NC}"
echo "  1) Docker (Recommended) - Easiest, works everywhere"
echo "  2) Local - Direct installation on your machine"
echo "  3) Kubernetes - For production clusters"
echo ""
read -p "Enter choice [1-3] (default: 1): " CHOICE
CHOICE=${CHOICE:-1}

case $CHOICE in
    1)
        MODE="docker"
        echo -e "${GREEN}✓ Docker mode selected${NC}"
        ;;
    2)
        MODE="local"
        echo -e "${GREEN}✓ Local mode selected${NC}"
        ;;
    3)
        MODE="kubernetes"
        echo -e "${GREEN}✓ Kubernetes mode selected${NC}"
        ;;
    *)
        echo -e "${YELLOW}Invalid choice. Using Docker mode.${NC}"
        MODE="docker"
        ;;
esac

# Ask for domain (optional)
echo ""
echo -e "${BLUE}Domain configuration (optional, for production):${NC}"
read -p "Domain name (leave empty for localhost): " DOMAIN

EMAIL=""
if [[ -n "$DOMAIN" ]]; then
    read -p "Email for SSL certificate: " EMAIL
fi

# Download and run installer
echo ""
echo -e "${CYAN}Downloading installer...${NC}"

TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Download install script
curl -fsSL https://raw.githubusercontent.com/TheRealHZL/MentalHealth/main/install.sh -o install.sh
chmod +x install.sh

# Build command
CMD="./install.sh --mode $MODE"

if [[ -n "$DOMAIN" ]]; then
    CMD="$CMD --domain $DOMAIN"
fi

if [[ -n "$EMAIL" ]]; then
    CMD="$CMD --email $EMAIL"
fi

# Show what will be installed
echo ""
echo -e "${CYAN}Installation command:${NC}"
echo "$CMD"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

# Run installation
eval $CMD

# Cleanup
cd /
rm -rf "$TEMP_DIR"

echo -e "\n${GREEN}🎉 Quick Start completed!${NC}\n"
