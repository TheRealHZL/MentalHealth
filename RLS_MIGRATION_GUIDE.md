# RLS Migration Guide for API Endpoints

This guide shows how to migrate existing API endpoints to use Row-Level Security (RLS).

## Quick Summary

**Before (Unsafe):**
```python
@router.get("/mood")
async def get_moods(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)  # ❌ No RLS!
):
    # Must manually filter by user_id
    result = await db.execute(
        select(MoodEntry).where(MoodEntry.user_id == user_id)  # Manual filter
    )
    return result.scalars().all()
```

**After (Safe with RLS):**
```python
from src.core.rls_fastapi_middleware import get_rls_session, require_authentication

@router.get("/mood")
async def get_moods(
    user_id: UUID = Depends(require_authentication),  # ✅ Enforces auth
    db: AsyncSession = Depends(get_rls_session)      # ✅ RLS enabled!
):
    # No need to filter manually - RLS does it automatically!
    result = await db.execute(select(MoodEntry))  # Automatically filtered!
    return result.scalars().all()
```

---

## Step-by-Step Migration

### Step 1: Update Imports

```python
# Old imports:
from src.core.database import get_async_session
from src.core.security import get_current_user_id

# New imports:
from src.core.rls_fastapi_middleware import (
    get_rls_session,              # RLS-enabled session
    require_authentication,        # Enforces authentication
    get_admin_rls_session         # For admin endpoints
)
```

### Step 2: Update Endpoint Dependencies

```python
# Old:
@router.get("/mood")
async def get_moods(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
):
    ...

# New:
@router.get("/mood")
async def get_moods(
    user_id: UUID = Depends(require_authentication),  # ✅ Returns UUID, enforces auth
    db: AsyncSession = Depends(get_rls_session)      # ✅ RLS context set
):
    ...
```

### Step 3: Remove Manual Filtering

RLS automatically filters queries, so you can remove manual `where` clauses:

```python
# Before (manual filtering):
result = await db.execute(
    select(MoodEntry)
    .where(MoodEntry.user_id == user_id)  # ❌ Redundant with RLS!
    .order_by(MoodEntry.created_at.desc())
)

# After (RLS handles it):
result = await db.execute(
    select(MoodEntry)
    .order_by(MoodEntry.created_at.desc())  # ✅ Automatically filtered!
)
```

---

## Complete Examples

### Example 1: GET Endpoint (List)

**Before:**
```python
@router.get("/mood", response_model=List[MoodEntryResponse])
async def get_mood_entries(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
    skip: int = 0,
    limit: int = 20
):
    """Get user's mood entries"""

    # Manual filtering by user_id
    result = await db.execute(
        select(MoodEntry)
        .where(MoodEntry.user_id == user_id)  # Manual filter
        .offset(skip)
        .limit(limit)
    )

    moods = result.scalars().all()
    return [mood.to_dict() for mood in moods]
```

**After:**
```python
@router.get("/mood", response_model=List[MoodEntryResponse])
async def get_mood_entries(
    user_id: UUID = Depends(require_authentication),
    db: AsyncSession = Depends(get_rls_session),  # ✅ RLS enabled
    skip: int = 0,
    limit: int = 20
):
    """Get user's mood entries (RLS-protected)"""

    # No manual filtering needed - RLS does it!
    result = await db.execute(
        select(MoodEntry)
        .offset(skip)
        .limit(limit)  # ✅ Automatically filtered by RLS
    )

    moods = result.scalars().all()
    return [mood.to_dict() for mood in moods]
```

### Example 2: GET by ID

**Before:**
```python
@router.get("/mood/{mood_id}", response_model=MoodEntryResponse)
async def get_mood_entry(
    mood_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
):
    """Get specific mood entry"""

    result = await db.execute(
        select(MoodEntry)
        .where(
            and_(
                MoodEntry.id == mood_id,
                MoodEntry.user_id == user_id  # Manual authorization check
            )
        )
    )

    mood = result.scalar_one_or_none()

    if not mood:
        raise HTTPException(404, "Mood entry not found")

    return mood.to_dict()
```

**After:**
```python
@router.get("/mood/{mood_id}", response_model=MoodEntryResponse)
async def get_mood_entry(
    mood_id: UUID,
    user_id: UUID = Depends(require_authentication),
    db: AsyncSession = Depends(get_rls_session)  # ✅ RLS enabled
):
    """Get specific mood entry (RLS-protected)"""

    result = await db.execute(
        select(MoodEntry)
        .where(MoodEntry.id == mood_id)  # ✅ Only ID check - RLS handles user_id!
    )

    mood = result.scalar_one_or_none()

    # If mood is None, it either doesn't exist OR doesn't belong to user
    # RLS automatically filters it out!
    if not mood:
        raise HTTPException(404, "Mood entry not found")

    return mood.to_dict()
```

### Example 3: POST (Create)

**Before:**
```python
@router.post("/mood", response_model=MoodEntryResponse)
async def create_mood_entry(
    mood_data: MoodEntryCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
):
    """Create mood entry"""

    # Manually set user_id
    mood = MoodEntry(
        id=uuid.uuid4(),
        user_id=user_id,  # Set from token
        mood_score=mood_data.mood_score,
        notes=mood_data.notes
    )

    db.add(mood)
    await db.commit()
    await db.refresh(mood)

    return mood.to_dict()
```

**After:**
```python
@router.post("/mood", response_model=MoodEntryResponse)
async def create_mood_entry(
    mood_data: MoodEntryCreate,
    user_id: UUID = Depends(require_authentication),
    db: AsyncSession = Depends(get_rls_session)  # ✅ RLS enabled
):
    """Create mood entry (RLS-protected)"""

    # Still set user_id explicitly (good practice)
    mood = MoodEntry(
        id=uuid.uuid4(),
        user_id=user_id,  # ✅ RLS policy ensures this matches authenticated user
        mood_score=mood_data.mood_score,
        notes=mood_data.notes
    )

    db.add(mood)
    await db.commit()
    await db.refresh(mood)

    return mood.to_dict()
```

**Note:** RLS INSERT policy will prevent users from creating records with a different user_id!

### Example 4: PUT (Update)

**Before:**
```python
@router.put("/mood/{mood_id}", response_model=MoodEntryResponse)
async def update_mood_entry(
    mood_id: UUID,
    mood_data: MoodEntryUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
):
    """Update mood entry"""

    # Get mood entry with manual authorization
    result = await db.execute(
        select(MoodEntry)
        .where(
            and_(
                MoodEntry.id == mood_id,
                MoodEntry.user_id == user_id  # Manual check
            )
        )
    )

    mood = result.scalar_one_or_none()

    if not mood:
        raise HTTPException(404, "Mood entry not found")

    # Update fields
    mood.mood_score = mood_data.mood_score
    mood.notes = mood_data.notes

    await db.commit()
    await db.refresh(mood)

    return mood.to_dict()
```

**After:**
```python
@router.put("/mood/{mood_id}", response_model=MoodEntryResponse)
async def update_mood_entry(
    mood_id: UUID,
    mood_data: MoodEntryUpdate,
    user_id: UUID = Depends(require_authentication),
    db: AsyncSession = Depends(get_rls_session)  # ✅ RLS enabled
):
    """Update mood entry (RLS-protected)"""

    # RLS automatically filters - can only update own moods
    result = await db.execute(
        select(MoodEntry)
        .where(MoodEntry.id == mood_id)  # ✅ No user_id check needed!
    )

    mood = result.scalar_one_or_none()

    if not mood:
        # Either doesn't exist OR doesn't belong to user (RLS filtered it)
        raise HTTPException(404, "Mood entry not found")

    # Update fields
    mood.mood_score = mood_data.mood_score
    mood.notes = mood_data.notes

    await db.commit()
    await db.refresh(mood)

    return mood.to_dict()
```

### Example 5: DELETE

**Before:**
```python
@router.delete("/mood/{mood_id}")
async def delete_mood_entry(
    mood_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
):
    """Delete mood entry"""

    result = await db.execute(
        select(MoodEntry)
        .where(
            and_(
                MoodEntry.id == mood_id,
                MoodEntry.user_id == user_id  # Manual authorization
            )
        )
    )

    mood = result.scalar_one_or_none()

    if not mood:
        raise HTTPException(404, "Mood entry not found")

    await db.delete(mood)
    await db.commit()

    return {"success": True, "message": "Mood entry deleted"}
```

**After:**
```python
@router.delete("/mood/{mood_id}")
async def delete_mood_entry(
    mood_id: UUID,
    user_id: UUID = Depends(require_authentication),
    db: AsyncSession = Depends(get_rls_session)  # ✅ RLS enabled
):
    """Delete mood entry (RLS-protected)"""

    result = await db.execute(
        select(MoodEntry)
        .where(MoodEntry.id == mood_id)  # ✅ No user_id check needed!
    )

    mood = result.scalar_one_or_none()

    if not mood:
        # RLS ensures user can only see/delete their own moods
        raise HTTPException(404, "Mood entry not found")

    await db.delete(mood)
    await db.commit()

    return {"success": True, "message": "Mood entry deleted"}
```

---

## Admin Endpoints

For admin endpoints that need to see all users' data:

```python
from src.core.rls_fastapi_middleware import get_admin_rls_session

@router.get("/admin/all-moods")
async def get_all_moods(
    user_id: UUID = Depends(require_authentication),
    db: AsyncSession = Depends(get_admin_rls_session)  # ✅ Admin session!
):
    """Admin endpoint - see all moods"""

    # TODO: Add admin permission check
    # if not is_admin(user_id):
    #     raise HTTPException(403, "Admin access required")

    # This query sees ALL moods (RLS bypassed for admin)
    result = await db.execute(select(MoodEntry))
    return result.scalars().all()
```

---

## Migration Checklist

For each endpoint:

- [ ] Update imports
- [ ] Change `get_async_session` → `get_rls_session`
- [ ] Change `get_current_user_id` → `require_authentication`
- [ ] Remove manual `.where(user_id == ...)` filters
- [ ] Test that users can only access their own data
- [ ] Test that 404 is returned for other users' data

---

## Security Benefits

✅ **Defense in Depth**: Even if application logic is buggy, database enforces isolation

✅ **SQL Injection Protection**: Attackers can't bypass RLS with injection

✅ **Simpler Code**: Less boilerplate for authorization checks

✅ **Guaranteed Consistency**: All queries automatically filtered

✅ **Audit Trail**: All access is logged by database triggers

---

## Testing RLS

Test that user isolation works:

```python
async def test_user_cannot_access_other_user_data():
    # User A creates mood
    mood_a = await create_mood(user_a_id, "Happy")

    # User B tries to access it
    with pytest.raises(HTTPException) as exc:
        await get_mood(user_b_id, mood_a.id)

    assert exc.value.status_code == 404  # Not found (RLS filtered it)
```

---

## Performance Notes

RLS has minimal performance impact (<5ms per query). Indexes on `user_id` columns ensure fast filtering.

---

## Rollback Plan

If issues occur, you can disable RLS temporarily:

```sql
-- Disable RLS on a table (for debugging only!)
ALTER TABLE mood_entries DISABLE ROW LEVEL SECURITY;

-- Re-enable when fixed:
ALTER TABLE mood_entries ENABLE ROW LEVEL SECURITY;
```

**Note:** Never disable RLS in production!

---

## Summary

**Migration is simple:**
1. Change 2 imports
2. Remove manual `user_id` filters
3. Test

**Result: Database-level user isolation! 🔒**
