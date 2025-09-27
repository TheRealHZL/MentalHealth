"""
Mood Service - Core Mood Operations

Kernfunktionalität für Mood Tracking ohne Therapeut-Abhängigkeit.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc, asc
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import date, datetime, time, timedelta
import uuid
import logging

from src.models import MoodEntry
from src.schemas.ai import MoodEntryCreate, MoodEntryUpdate, PaginationParams

logger = logging.getLogger(__name__)

class MoodService:
    """Core Mood Tracking Operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_mood_entry(
        self,
        user_id: str,
        mood_data: MoodEntryCreate
    ) -> MoodEntry:
        """Create new mood entry"""
        
        mood_entry = MoodEntry(
            user_id=uuid.UUID(user_id),
            entry_date=mood_data.date,
            entry_time=mood_data.time,
            mood_score=mood_data.mood_score.value,
            stress_level=mood_data.stress_level,
            energy_level=mood_data.energy_level,
            sleep_quality=mood_data.sleep_quality,
            sleep_hours=mood_data.sleep_hours,
            activities=[activity.value for activity in mood_data.activities],
            exercise_minutes=mood_data.exercise_minutes,
            notes=mood_data.notes,
            location=mood_data.location,
            symptoms=mood_data.symptoms,
            triggers=mood_data.triggers,
            took_medication=mood_data.took_medication,
            medication_notes=mood_data.medication_notes
        )
        
        self.db.add(mood_entry)
        await self.db.commit()
        await self.db.refresh(mood_entry)
        
        logger.info(f"Created mood entry for user {user_id}: {mood_data.mood_score}/10")
        return mood_entry
    
    async def create_quick_mood_entry(
        self,
        user_id: str,
        mood_score: int,
        note: Optional[str] = None
    ) -> MoodEntry:
        """Create quick mood entry with defaults"""
        
        now = datetime.now()
        
        mood_entry = MoodEntry(
            user_id=uuid.UUID(user_id),
            entry_date=now.date(),
            entry_time=now.time(),
            mood_score=mood_score,
            stress_level=5,  # Default neutral
            energy_level=5,  # Default neutral
            sleep_quality=5,  # Default neutral
            sleep_hours=8.0,  # Default
            activities=[],
            exercise_minutes=0,
            notes=note,
            took_medication=False
        )
        
        self.db.add(mood_entry)
        await self.db.commit()
        await self.db.refresh(mood_entry)
        
        return mood_entry
    
    async def get_mood_entry_by_id(
        self,
        entry_id: str,
        user_id: str
    ) -> Optional[MoodEntry]:
        """Get mood entry by ID (user-scoped)"""
        
        result = await self.db.execute(
            select(MoodEntry).where(
                and_(
                    MoodEntry.id == uuid.UUID(entry_id),
                    MoodEntry.user_id == uuid.UUID(user_id)
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_mood_entry_by_date(
        self,
        user_id: str,
        entry_date: date,
        entry_time: time
    ) -> Optional[MoodEntry]:
        """Check if mood entry exists for specific date/time"""
        
        result = await self.db.execute(
            select(MoodEntry).where(
                and_(
                    MoodEntry.user_id == uuid.UUID(user_id),
                    MoodEntry.entry_date == entry_date,
                    MoodEntry.entry_time == entry_time
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_mood_entries_paginated(
        self,
        user_id: str,
        pagination: PaginationParams,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        min_mood: Optional[int] = None,
        max_mood: Optional[int] = None
    ) -> Tuple[List[MoodEntry], int]:
        """Get paginated mood entries with filters"""
        
        # Base query
        query = select(MoodEntry).where(MoodEntry.user_id == uuid.UUID(user_id))
        count_query = select(func.count(MoodEntry.id)).where(MoodEntry.user_id == uuid.UUID(user_id))
        
        # Apply filters
        if start_date:
            query = query.where(MoodEntry.entry_date >= start_date)
            count_query = count_query.where(MoodEntry.entry_date >= start_date)
        
        if end_date:
            query = query.where(MoodEntry.entry_date <= end_date)
            count_query = count_query.where(MoodEntry.entry_date <= end_date)
        
        if min_mood:
            query = query.where(MoodEntry.mood_score >= min_mood)
            count_query = count_query.where(MoodEntry.mood_score >= min_mood)
        
        if max_mood:
            query = query.where(MoodEntry.mood_score <= max_mood)
            count_query = count_query.where(MoodEntry.mood_score <= max_mood)
        
        # Sorting
        if pagination.sort_by == "date":
            order_col = MoodEntry.entry_date
        elif pagination.sort_by == "mood":
            order_col = MoodEntry.mood_score
        else:
            order_col = MoodEntry.created_at
        
        if pagination.sort_order == "asc":
            query = query.order_by(asc(order_col))
        else:
            query = query.order_by(desc(order_col))
        
        # Pagination
        offset = (pagination.page - 1) * pagination.page_size
        query = query.offset(offset).limit(pagination.page_size)
        
        # Execute queries
        entries_result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        
        entries = list(entries_result.scalars().all())
        total_count = count_result.scalar()
        
        return entries, total_count
    
    async def update_mood_entry(
        self,
        entry_id: str,
        user_id: str,
        update_data: MoodEntryUpdate
    ) -> MoodEntry:
        """Update mood entry"""
        
        mood_entry = await self.get_mood_entry_by_id(entry_id, user_id)
        if not mood_entry:
            raise ValueError("Mood entry not found")
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        
        for field, value in update_dict.items():
            if hasattr(mood_entry, field):
                if field == "activities" and value:
                    setattr(mood_entry, field, [activity.value for activity in value])
                elif field == "mood_score" and value:
                    setattr(mood_entry, field, value.value)
                else:
                    setattr(mood_entry, field, value)
        
        await self.db.commit()
        await self.db.refresh(mood_entry)
        
        return mood_entry
    
    async def delete_mood_entry(self, entry_id: str, user_id: str) -> bool:
        """Delete mood entry"""
        
        mood_entry = await self.get_mood_entry_by_id(entry_id, user_id)
        if not mood_entry:
            return False
        
        await self.db.delete(mood_entry)
        await self.db.commit()
        
        return True
