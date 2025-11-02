# 🔄 Complete Migration Plan

**Problem**: Two parallel structures exist (`/src` and `/app`)

**Solution**: Clean migration with proper AI Engine integration

---

## Current State

```
/MentalHealth
├── /src                    # OLD - Still contains AI Engine!
│   ├── /ai                 # ← PyTorch AI Engine
│   │   ├── engine.py
│   │   ├── /models
│   │   ├── /training
│   │   ├── /preprocessing
│   │   └── /evaluation
│   ├── /api
│   ├── /core
│   ├── /models            # DB models
│   ├── /schemas
│   └── main.py
│
└── /app                   # NEW - Partial migration
    ├── /core              # Core utils (duplicated)
    ├── /modules           # Modular endpoints
    └── main.py            # Module-aware entry point
```

---

## Target State

```
/MentalHealth
├── /app                   # PRIMARY APPLICATION
│   ├── /core              # Core framework
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── security.py
│   │   └── module_loader.py
│   │
│   ├── /ai                # ⭐ AI Engine (moved from src/)
│   │   ├── engine.py
│   │   ├── /models        # PyTorch models
│   │   ├── /training      # Training scripts
│   │   ├── /preprocessing # Data preprocessing
│   │   └── /evaluation    # Model evaluation
│   │
│   ├── /models            # Database models (SQLAlchemy)
│   ├── /schemas           # Pydantic schemas (shared)
│   ├── /services          # Shared services (cross-module)
│   │
│   ├── /modules           # Feature modules
│   │   ├── /mood
│   │   ├── /dreams
│   │   ├── /therapy
│   │   ├── /admin
│   │   ├── /ai_training   # ← Uses app/ai/
│   │   ├── /analytics
│   │   ├── /sharing
│   │   └── /users
│   │
│   └── main.py            # Application entry point
│
├── /src                   # ⚠️ DEPRECATED (to be removed)
│
├── /tests                 # Tests
├── /scripts               # Utility scripts
├── /docs                  # Documentation
└── /alembic               # Database migrations
```

---

## Migration Steps

### Phase 1: Move AI Engine

```bash
# 1. Move AI Engine
mv src/ai app/ai

# 2. Update imports in AI modules
find app/ai -name "*.py" -exec sed -i 's/from src\./from app./g' {} +

# 3. Copy shared database models
cp -r src/models app/models

# 4. Copy shared schemas
cp -r src/schemas app/schemas

# 5. Copy shared services
cp -r src/services app/services
```

### Phase 2: Update Module Imports

All modules need to import from:
- `app.ai.engine` (instead of `src.ai.engine`)
- `app.models.*` (instead of `src.models.*`)
- `app.schemas.*` (instead of `src.schemas.*`)

### Phase 3: Update Entry Point

Update `app/main.py` to use:
```python
from app.ai.engine import AIEngine  # Instead of src.ai.engine
from app.models import *            # Instead of src.models
```

### Phase 4: Clean Up

```bash
# Archive old structure
mv src src_backup_$(date +%Y%m%d)

# Update Dockerfile
sed -i 's/src\./app./g' Dockerfile

# Update docker-compose.yml
sed -i 's/src\.main/app.main/g' docker-compose.yml
```

---

## Which Option?

### Option A: Clean Migration (Recommended)
- Move everything to `/app`
- Remove `/src` completely
- Update all imports
- **Time**: 30 minutes

### Option B: Hybrid Approach
- Keep AI Engine in `/src/ai`
- Use `/app` for modules only
- Both structures coexist
- **Time**: 5 minutes (update imports)

### Option C: Rollback to /src
- Remove `/app`
- Keep everything in `/src`
- Add module system to `/src`
- **Time**: 20 minutes

---

## Recommendation: Option A (Clean Migration)

**Why?**
- ✅ Clean, single source of truth
- ✅ No confusion about import paths
- ✅ Modern structure
- ✅ Easy to maintain

**When?**
- Now (if possible)
- Or: Schedule for next maintenance window

---

## Quick Fix for NOW

If you want to keep working immediately:

```bash
# 1. Update app/main.py to use src/ai
sed -i 's/from app\.ai/from src.ai/g' app/main.py

# 2. Create symlink for compatibility
ln -s ../src/ai app/ai

# 3. Restart
docker-compose restart backend
```

This allows both structures to coexist temporarily.

---

## Which option do you prefer?
