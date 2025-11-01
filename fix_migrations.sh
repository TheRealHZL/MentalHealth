#!/bin/bash

###############################################################################
# MindBridge Migration Fix Script
# Fixes alembic migration issues when database already has tables
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
echo -e "${CYAN}║   MindBridge Database Migration Fix Script            ║${NC}"
echo -e "${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
echo ""

# Check if running in docker-compose
if command -v docker-compose &> /dev/null; then
    IN_DOCKER=true
    BACKEND_CMD="docker-compose exec -T backend"
else
    IN_DOCKER=false
    BACKEND_CMD=""
fi

echo -e "${YELLOW}⚠️  Database Migration Problem Detected!${NC}"
echo ""
echo "Your database already has tables, but Alembic doesn't know about them."
echo "This happens when:"
echo "  - Database was created by SQLAlchemy ORM directly"
echo "  - Old migrations were run and alembic_version table is missing/wrong"
echo "  - Database was manually created"
echo ""
echo -e "${BLUE}Choose a fix option:${NC}"
echo ""
echo -e "${GREEN}Option 1: RESET DATABASE (Recommended for Dev/Test)${NC}"
echo "  - Drops all tables and data"
echo "  - Runs all migrations from scratch"
echo "  - Clean slate, guaranteed to work"
echo "  ⚠️  WARNING: ALL DATA WILL BE LOST!"
echo ""
echo -e "${GREEN}Option 2: STAMP DATABASE (For Production/Keep Data)${NC}"
echo "  - Keeps all existing data"
echo "  - Tells Alembic: 'Database is already at latest version'"
echo "  - Only works if your schema matches the migrations"
echo "  ✅ Safe: No data loss"
echo ""
echo -e "${GREEN}Option 3: CHECK STATUS (Diagnostic)${NC}"
echo "  - Shows current database state"
echo "  - Shows alembic version"
echo "  - Helps diagnose the issue"
echo ""

read -p "Enter your choice (1/2/3): " choice

case $choice in
    1)
        echo ""
        echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${RED}⚠️  WARNING: This will DELETE ALL DATA!${NC}"
        echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        read -p "Are you ABSOLUTELY sure? Type 'DELETE ALL DATA' to confirm: " confirm

        if [ "$confirm" != "DELETE ALL DATA" ]; then
            echo -e "${YELLOW}Aborted. No changes made.${NC}"
            exit 0
        fi

        echo ""
        echo -e "${CYAN}🔄 Resetting database...${NC}"

        # Drop all tables using SQL
        if [ "$IN_DOCKER" = true ]; then
            echo -e "${BLUE}Dropping all tables via Docker...${NC}"
            docker-compose exec -T backend python <<'PYTHON'
import asyncio
from sqlalchemy import text
from src.core.database import AsyncSessionLocal

async def drop_all():
    async with AsyncSessionLocal() as session:
        # Disable foreign key checks temporarily
        await session.execute(text("SET session_replication_role = 'replica';"))

        # Get all tables
        result = await session.execute(text("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename != 'spatial_ref_sys'
        """))
        tables = [row[0] for row in result]

        # Drop all tables
        for table in tables:
            print(f"Dropping table: {table}")
            await session.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))

        # Re-enable foreign key checks
        await session.execute(text("SET session_replication_role = 'origin';"))
        await session.commit()
        print("✅ All tables dropped successfully")

asyncio.run(drop_all())
PYTHON
        else
            python <<'PYTHON'
import asyncio
from sqlalchemy import text
from src.core.database import AsyncSessionLocal

async def drop_all():
    async with AsyncSessionLocal() as session:
        await session.execute(text("SET session_replication_role = 'replica';"))
        result = await session.execute(text("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename != 'spatial_ref_sys'
        """))
        tables = [row[0] for row in result]
        for table in tables:
            print(f"Dropping table: {table}")
            await session.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
        await session.execute(text("SET session_replication_role = 'origin';"))
        await session.commit()
        print("✅ All tables dropped successfully")

asyncio.run(drop_all())
PYTHON
        fi

        echo ""
        echo -e "${CYAN}🔄 Running migrations from scratch...${NC}"

        if [ "$IN_DOCKER" = true ]; then
            docker-compose exec -T backend alembic upgrade head
        else
            alembic upgrade head
        fi

        echo ""
        echo -e "${GREEN}✅ Database reset complete!${NC}"
        echo -e "${GREEN}✅ All migrations applied successfully!${NC}"
        ;;

    2)
        echo ""
        echo -e "${CYAN}🔖 Stamping database at 'head' (latest version)...${NC}"
        echo ""

        if [ "$IN_DOCKER" = true ]; then
            docker-compose exec -T backend alembic stamp head
        else
            alembic stamp head
        fi

        echo ""
        echo -e "${GREEN}✅ Database stamped successfully!${NC}"
        echo ""
        echo -e "${YELLOW}Note: This tells Alembic your database is up-to-date.${NC}"
        echo -e "${YELLOW}Make sure your actual schema matches the migrations!${NC}"
        echo ""
        echo "To verify, run: alembic current"
        ;;

    3)
        echo ""
        echo -e "${CYAN}📊 Checking database status...${NC}"
        echo ""

        echo -e "${BLUE}=== Alembic Version ===${NC}"
        if [ "$IN_DOCKER" = true ]; then
            docker-compose exec -T backend alembic current || echo "No version info (fresh database)"
        else
            alembic current || echo "No version info (fresh database)"
        fi

        echo ""
        echo -e "${BLUE}=== Migration History ===${NC}"
        if [ "$IN_DOCKER" = true ]; then
            docker-compose exec -T backend alembic history
        else
            alembic history
        fi

        echo ""
        echo -e "${BLUE}=== Existing Tables ===${NC}"
        if [ "$IN_DOCKER" = true ]; then
            docker-compose exec -T backend python <<'PYTHON'
import asyncio
from sqlalchemy import text
from src.core.database import AsyncSessionLocal

async def show_tables():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """))
        tables = [row[0] for row in result]
        for table in tables:
            print(f"  - {table}")
        print(f"\nTotal: {len(tables)} tables")

asyncio.run(show_tables())
PYTHON
        else
            python <<'PYTHON'
import asyncio
from sqlalchemy import text
from src.core.database import AsyncSessionLocal

async def show_tables():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """))
        tables = [row[0] for row in result]
        for table in tables:
            print(f"  - {table}")
        print(f"\nTotal: {len(tables)} tables")

asyncio.run(show_tables())
PYTHON
        fi

        echo ""
        echo -e "${YELLOW}Run this script again and choose Option 1 or 2 to fix.${NC}"
        ;;

    *)
        echo -e "${RED}Invalid choice. Exiting.${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Done!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
