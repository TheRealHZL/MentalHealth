# Database Migrations Guide

## Overview

MindBridge uses **Alembic** for database schema migrations. This ensures:
- ✅ Version-controlled database changes
- ✅ Reproducible deployments
- ✅ Safe schema updates
- ✅ Rollback capability

## Migration Chain

Current migrations in order:

```
None → 001_initial_tables → 002_add_encrypted_models → 003 → 004 → 005
```

### Migration Details

| Revision | File | Description |
|----------|------|-------------|
| `001_initial_tables` | `001_initial_tables.py` | Creates all initial tables (users, moods, dreams, etc.) |
| `002_add_encrypted_models` | `002_add_encrypted_models.py` | Adds encryption metadata tables |
| `003` | `003_enable_rls.py` | Enables Row-Level Security (RLS) for user isolation |
| `004` | `004_add_audit_logging.py` | Adds audit logging tables and triggers |
| `005` | `005_add_user_context.py` | Adds user context for RLS policies |

## Common Commands

### Check Current Version
```bash
# In Docker
docker-compose exec backend alembic current

# Local
alembic current
```

### Upgrade to Latest
```bash
# In Docker
docker-compose exec backend alembic upgrade head

# Local
alembic upgrade head
```

### Downgrade One Version
```bash
# In Docker
docker-compose exec backend alembic downgrade -1

# Local
alembic downgrade -1
```

### Show Migration History
```bash
# In Docker
docker-compose exec backend alembic history

# Local
alembic history
```

### Generate New Migration
```bash
# Auto-generate from model changes
alembic revision --autogenerate -m "Description of change"

# Empty migration (manual)
alembic revision -m "Description of change"
```

## Common Issues & Solutions

### Issue 1: "relation 'users' already exists"

**Problem:** Database has tables, but Alembic doesn't know about them.

**Solution:** Use the fix script:
```bash
./fix_migrations.sh
```

Choose:
- **Option 1:** Reset database (dev/test) - **DELETES ALL DATA**
- **Option 2:** Stamp database (production) - **KEEPS DATA**
- **Option 3:** Check status (diagnostic)

### Issue 2: "KeyError: '002'" or broken migration chain

**Problem:** Migration references don't match.

**Solution:** Already fixed! Revision 003 now correctly references `002_add_encrypted_models`.

### Issue 3: Migration fails halfway

**Problem:** Database is in inconsistent state.

**Solution:**
```bash
# Option A: Rollback and retry
docker-compose exec backend alembic downgrade -1
docker-compose exec backend alembic upgrade head

# Option B: Reset (if dev/test environment)
./fix_migrations.sh
# Choose Option 1
```

### Issue 4: "Target database is not up to date"

**Problem:** Need to upgrade before making new migrations.

**Solution:**
```bash
docker-compose exec backend alembic upgrade head
```

## Production Deployment Workflow

### First Deployment (New Database)

```bash
# 1. Ensure database is empty
docker-compose exec postgres psql -U mindbridge_user -d mindbridge_db -c "\dt"

# 2. Run all migrations
docker-compose exec backend alembic upgrade head

# 3. Verify
docker-compose exec backend alembic current
```

### Updating Existing Deployment

```bash
# 1. Backup database first!
docker-compose exec postgres pg_dump -U mindbridge_user mindbridge_db > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Check current version
docker-compose exec backend alembic current

# 3. Pull latest code
git pull origin main

# 4. Run migrations
docker-compose exec backend alembic upgrade head

# 5. Verify
docker-compose exec backend alembic current

# 6. Restart backend
docker-compose restart backend
```

### Using update.sh Script

The `update.sh` script automatically handles migrations:

```bash
./update.sh
```

If migrations fail, it will show an error. Then use:
```bash
./fix_migrations.sh
```

## Development Workflow

### Making Schema Changes

1. **Modify SQLAlchemy models** in `src/models/`

2. **Generate migration:**
```bash
docker-compose exec backend alembic revision --autogenerate -m "Add user preferences table"
```

3. **Review generated migration** in `alembic/versions/`
   - Check upgrade() function
   - Check downgrade() function
   - Verify SQL operations

4. **Test migration:**
```bash
# Upgrade
docker-compose exec backend alembic upgrade head

# Test downgrade
docker-compose exec backend alembic downgrade -1

# Upgrade again
docker-compose exec backend alembic upgrade head
```

5. **Commit migration:**
```bash
git add alembic/versions/XXXXXXXX_add_user_preferences_table.py
git commit -m "Add migration: user preferences table"
```

## Manual Migration Fix (Advanced)

### Stamp Database to Specific Version

If you know your database matches a specific migration:

```bash
# Stamp to latest
docker-compose exec backend alembic stamp head

# Stamp to specific version
docker-compose exec backend alembic stamp 003

# Stamp to base (empty database)
docker-compose exec backend alembic stamp base
```

### Skip Problematic Migration

⚠️ **Dangerous - only for emergencies!**

```bash
# Fake upgrade without running SQL
docker-compose exec backend alembic stamp head

# Then manually fix database schema to match
```

### Completely Reset Alembic

```bash
# 1. Drop alembic_version table
docker-compose exec postgres psql -U mindbridge_user -d mindbridge_db -c "DROP TABLE alembic_version;"

# 2. Re-stamp to current state
docker-compose exec backend alembic stamp head
```

## Best Practices

### DO ✅

- **Always backup** before migrations in production
- **Test migrations** in dev/staging first
- **Review auto-generated** migrations before committing
- **Keep migrations small** and focused
- **Write both upgrade** and downgrade functions
- **Document complex migrations** with comments

### DON'T ❌

- **Don't skip migrations** - run them in order
- **Don't modify** existing migrations after they're in production
- **Don't delete** old migration files
- **Don't run migrations** directly in production without testing
- **Don't ignore** migration errors - fix them properly

## Troubleshooting Commands

### Check Database Tables
```bash
docker-compose exec postgres psql -U mindbridge_user -d mindbridge_db -c "\dt"
```

### Check Alembic Version Table
```bash
docker-compose exec postgres psql -U mindbridge_user -d mindbridge_db -c "SELECT * FROM alembic_version;"
```

### Check Database Connections
```bash
docker-compose exec postgres psql -U mindbridge_user -d mindbridge_db -c "SELECT count(*) FROM pg_stat_activity;"
```

### Force Close All Connections
```bash
docker-compose exec postgres psql -U mindbridge_user -d mindbridge_db -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'mindbridge_db'
AND pid <> pg_backend_pid();"
```

## Emergency Recovery

### Scenario: Production database corrupted by failed migration

```bash
# 1. Stop backend to prevent new connections
docker-compose stop backend

# 2. Restore from backup
docker-compose exec postgres psql -U mindbridge_user -d mindbridge_db < backup_YYYYMMDD_HHMMSS.sql

# 3. Verify alembic version
docker-compose exec postgres psql -U mindbridge_user -d mindbridge_db -c "SELECT * FROM alembic_version;"

# 4. If needed, stamp to correct version
docker-compose exec backend alembic stamp <version>

# 5. Start backend
docker-compose start backend
```

## Getting Help

### Check Migration Status
```bash
./fix_migrations.sh
# Choose Option 3 (Check Status)
```

### View Logs
```bash
# Backend logs
docker-compose logs backend | grep -i alembic

# Database logs
docker-compose logs postgres | grep -i error
```

### Contact Information

For migration issues:
1. Check this guide first
2. Run `./fix_migrations.sh` diagnostic (Option 3)
3. Check logs for detailed error messages
4. Review the specific migration file causing issues

## File Locations

- **Migrations:** `alembic/versions/`
- **Alembic Config:** `alembic.ini`
- **Alembic Environment:** `alembic/env.py`
- **Database Models:** `src/models/`
- **Fix Script:** `fix_migrations.sh`
