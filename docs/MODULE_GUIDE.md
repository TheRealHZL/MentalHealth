# 📦 Module Guide

**MindBridge AI Platform - Modular Architecture**

The MindBridge platform uses a plug-and-play module system that allows easy extension and maintainability.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Module Structure](#module-structure)
3. [Creating a New Module](#creating-a-new-module)
4. [Module Manifest](#module-manifest)
5. [Module Loader](#module-loader)
6. [Best Practices](#best-practices)
7. [Examples](#examples)

---

## Architecture Overview

```
/app
  /core                    # Core functionality
    config.py              # Settings & configuration
    database.py            # Database connection
    module_loader.py       # Auto-load modules
    security.py            # Authentication & security
    utils.py               # Utilities
  /modules                 # All modules here
    /module_name/
      manifest.json        # Module metadata ⭐
      routes.py            # FastAPI routes (required)
      models.py            # Database models (optional)
      schemas.py           # Pydantic schemas (optional)
      service.py           # Business logic (optional)
      __init__.py
  main.py                  # Application entry point
```

## Module Structure

Every module **MUST** have:
- ✅ `manifest.json` - Module metadata
- ✅ `routes.py` - FastAPI router with API endpoints
- ✅ `__init__.py` - Python package marker

Optional files:
- `models.py` - SQLAlchemy database models
- `schemas.py` - Pydantic request/response schemas
- `service.py` - Business logic layer
- `tests/` - Module-specific tests

---

## Creating a New Module

### Step 1: Create Module Directory

```bash
mkdir -p app/modules/my_module
cd app/modules/my_module
```

### Step 2: Create `manifest.json`

```json
{
  "name": "my_module",
  "version": "1.0.0",
  "description": "Description of what this module does",
  "enabled": true,
  "routes_prefix": "/api/v1/my-module",
  "tags": ["my-module"],
  "dependencies": [],
  "author": "Your Name"
}
```

### Step 3: Create `routes.py`

```python
"""
My Module Routes

API endpoints for my_module functionality.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.security import get_current_user_id

router = APIRouter()


@router.get("/")
async def get_items(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
):
    """Get all items"""
    return {"message": "Hello from my_module", "user_id": user_id}


@router.post("/")
async def create_item(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
):
    """Create new item"""
    return {"message": "Item created", "user_id": user_id}
```

### Step 4: Create `__init__.py`

```python
"""My Module"""
__version__ = "1.0.0"
```

### Step 5: Test Your Module

```bash
# Start the application
python3 -m app.main

# Check if module loaded
curl http://localhost:8080/api/v1/modules

# Test your endpoint
curl http://localhost:8080/api/v1/my-module/
```

---

## Module Manifest

The `manifest.json` file defines module metadata and configuration.

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Module identifier (lowercase, underscores) |
| `version` | string | Semantic version (e.g., "1.0.0") |
| `description` | string | Brief description of module functionality |
| `routes_prefix` | string | API route prefix (e.g., "/api/v1/module") |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `enabled` | boolean | Enable/disable module (default: true) |
| `tags` | array | OpenAPI tags for documentation |
| `dependencies` | array | List of required module names |
| `author` | string | Module author/team |
| `permissions` | array | Required permissions (e.g., ["admin"]) |
| `features` | array | List of module features |

### Full Example

```json
{
  "name": "mood",
  "version": "1.0.0",
  "description": "Mood tracking and analysis with AI-powered insights",
  "enabled": true,
  "routes_prefix": "/api/v1/mood",
  "tags": ["mood-tracking"],
  "dependencies": [],
  "author": "MindBridge Team",
  "features": [
    "Create and track mood entries",
    "AI-powered mood analysis",
    "Mood patterns and trends",
    "Activity correlation"
  ],
  "permissions": ["authenticated"]
}
```

---

## Module Loader

The module loader automatically discovers and loads modules at startup.

### How It Works

1. **Discovery**: Scans `app/modules/` for directories with `manifest.json`
2. **Validation**: Validates manifest and checks dependencies
3. **Loading**: Imports `routes.py` and extracts the `router`
4. **Registration**: Registers router with FastAPI app

### Module Loading Order

Modules are loaded based on their dependencies:

```
Module A (no dependencies) → Loaded first
Module B (depends on A)    → Loaded second
Module C (depends on B)    → Loaded third
```

### Checking Loaded Modules

```bash
# Via API
curl http://localhost:8080/api/v1/modules

# Via logs
docker-compose logs backend | grep "Loaded module"

# Via Python
from app.core.module_loader import get_module_loader
loader = get_module_loader()
print(loader.get_modules_info())
```

---

## Best Practices

### 1. Module Independence

Modules should be **self-contained** and **loosely coupled**.

❌ **Bad**: Direct imports between modules
```python
from app.modules.mood.service import MoodService  # Don't do this
```

✅ **Good**: Use shared services or events
```python
from app.core.events import publish_event
publish_event("mood.created", data)
```

### 2. Database Models

Keep database models in `models.py`:

```python
# app/modules/mood/models.py
from sqlalchemy import Column, String, Integer, DateTime
from app.core.database import Base

class MoodEntry(Base):
    __tablename__ = "mood_entries"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    mood_score = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False)
```

### 3. Service Layer

Separate business logic from routes:

```python
# app/modules/mood/service.py
class MoodService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_mood_entry(self, user_id: str, mood_score: int):
        # Business logic here
        pass

# app/modules/mood/routes.py
@router.post("/")
async def create_mood(
    data: MoodCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
):
    service = MoodService(db)
    return await service.create_mood_entry(user_id, data.mood_score)
```

### 4. Error Handling

Use consistent error handling:

```python
from fastapi import HTTPException, status

@router.get("/{item_id}")
async def get_item(item_id: str):
    item = await get_item_from_db(item_id)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found"
        )

    return item
```

### 5. Testing

Create module-specific tests:

```python
# tests/unit/test_mood.py
import pytest
from app.modules.mood.service import MoodService

@pytest.mark.asyncio
async def test_create_mood_entry():
    service = MoodService(db)
    entry = await service.create_mood_entry("user1", 8)
    assert entry.mood_score == 8
```

---

## Examples

### Example 1: Apple Health Integration Module

```
app/modules/apple_health/
├── manifest.json
├── __init__.py
├── routes.py           # Endpoints for uploading/syncing data
├── schemas.py          # HealthKit data schemas
├── service.py          # Parsing & storage logic
└── parser.py           # XML/JSON parser for HealthKit export
```

**manifest.json**:
```json
{
  "name": "apple_health",
  "version": "1.0.0",
  "description": "Import and analyze Apple Health data",
  "enabled": true,
  "routes_prefix": "/api/v1/apple-health",
  "tags": ["integrations", "health-data"],
  "dependencies": ["mood", "analytics"],
  "author": "MindBridge Team",
  "features": [
    "Import HealthKit XML exports",
    "Parse heart rate, steps, sleep data",
    "Correlate with mood entries",
    "Generate health insights"
  ]
}
```

### Example 2: Emotion Tracking Module

```
app/modules/emotions/
├── manifest.json
├── __init__.py
├── routes.py
├── models.py          # EmotionEntry model
├── schemas.py         # Request/response schemas
└── service.py         # Emotion analysis logic
```

**Key features**:
- Track multiple emotions per entry
- AI-powered emotion detection from text
- Emotion wheel visualization
- Correlation with mood and activities

---

## Module Lifecycle

### 1. Development
```bash
# Create module structure
mkdir -p app/modules/my_module

# Write code
vim app/modules/my_module/routes.py

# Test locally
python3 -m pytest tests/unit/test_my_module.py
```

### 2. Testing
```bash
# Run module tests
pytest tests/unit/test_my_module.py -v

# Run integration tests
pytest tests/integration/test_my_module.py -v

# Check code quality
black app/modules/my_module/
flake8 app/modules/my_module/
mypy app/modules/my_module/
```

### 3. Deployment
```bash
# Commit changes
git add app/modules/my_module/
git commit -m "Add my_module"

# Update and restart
./scripts/update.sh
```

### 4. Monitoring
```bash
# Check if module loaded
curl http://localhost:8080/api/v1/modules | jq '.modules[] | select(.name=="my_module")'

# Monitor logs
docker-compose logs -f backend | grep "my_module"

# Check metrics
curl http://localhost:8080/metrics | grep my_module
```

---

## Troubleshooting

### Module Not Loading

**Issue**: Module not appearing in `/api/v1/modules`

**Solutions**:
1. Check `manifest.json` is valid JSON
2. Verify `enabled: true` in manifest
3. Check for syntax errors in `routes.py`
4. Ensure `router` variable exists in `routes.py`
5. Check logs: `docker-compose logs backend | grep ERROR`

### Import Errors

**Issue**: `ModuleNotFoundError` when importing

**Solutions**:
1. Ensure `__init__.py` exists in module directory
2. Use absolute imports: `from app.modules.mood import ...`
3. Install missing dependencies: `pip install -r requirements.txt`

### Dependency Conflicts

**Issue**: Module depends on another module

**Solutions**:
1. Add dependency to `manifest.json`:
   ```json
   {
     "dependencies": ["mood", "analytics"]
   }
   ```
2. Ensure dependent module is enabled
3. Check load order in logs

---

## Advanced Topics

### Module Events

Use events for inter-module communication:

```python
# app/modules/mood/routes.py
from app.core.events import publish_event

@router.post("/")
async def create_mood(data: MoodCreate):
    mood = await create_mood_entry(data)

    # Publish event for other modules
    await publish_event("mood.created", {
        "user_id": mood.user_id,
        "mood_score": mood.mood_score
    })

    return mood
```

### Module Configuration

Add module-specific settings:

```python
# app/modules/mood/config.py
from pydantic_settings import BaseSettings

class MoodModuleSettings(BaseSettings):
    AI_ENABLED: bool = True
    MAX_ENTRIES_PER_DAY: int = 10

    class Config:
        env_prefix = "MOOD_"

# Usage
settings = MoodModuleSettings()
```

### Module Permissions

Implement permission checks:

```python
from app.core.security import require_permission

@router.delete("/{entry_id}")
async def delete_entry(
    entry_id: str,
    user_id: str = Depends(require_permission("mood.delete"))
):
    # Only users with "mood.delete" permission can access
    pass
```

---

## Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Pydantic Models**: https://docs.pydantic.dev/
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **MindBridge Platform Docs**: `/docs/`

---

**Need Help?**

- 📖 Read the docs: `/docs/`
- 🐛 Report issues: GitHub Issues
- 💬 Ask questions: support@mindbridge.app
