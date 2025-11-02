"""
Calendar Service - Core Calendar Operations

Kernfunktionalität für Kalenderverwaltung, Termine und Erinnerungen.
"""

import logging
import uuid
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calendar import CalendarEvent
from app.schemas.calendar import CalendarEventCreate, CalendarEventUpdate

logger = logging.getLogger(__name__)


class CalendarService:
    """Core Calendar Operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_event(
        self, user_id: str, event_data: CalendarEventCreate
    ) -> CalendarEvent:
        """Create new calendar event"""

        # Validate end_time is after start_time
        if event_data.end_time <= event_data.start_time:
            raise ValueError("end_time must be after start_time")

        # Validate recurrence settings
        if event_data.is_recurring and not event_data.recurrence_pattern:
            raise ValueError("recurrence_pattern is required for recurring events")

        event = CalendarEvent(
            user_id=uuid.UUID(user_id),
            title=event_data.title,
            description=event_data.description,
            start_time=event_data.start_time,
            end_time=event_data.end_time,
            event_type=event_data.event_type,
            color=event_data.color,
            is_recurring=event_data.is_recurring,
            recurrence_pattern=event_data.recurrence_pattern,
            recurrence_end_date=event_data.recurrence_end_date,
            reminder_minutes=event_data.reminder_minutes,
            therapy_note_id=uuid.UUID(event_data.therapy_note_id) if event_data.therapy_note_id else None,
            notes=event_data.notes,
        )

        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)

        logger.info(f"Created calendar event for user {user_id}: {event_data.title}")
        return event

    async def get_event_by_id(
        self, event_id: str, user_id: str
    ) -> Optional[CalendarEvent]:
        """Get calendar event by ID (user-scoped)"""

        result = await self.db.execute(
            select(CalendarEvent).where(
                and_(
                    CalendarEvent.id == uuid.UUID(event_id),
                    CalendarEvent.user_id == uuid.UUID(user_id),
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_events_by_date_range(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
        event_type: Optional[str] = None,
        include_cancelled: bool = False,
    ) -> List[CalendarEvent]:
        """Get calendar events within date range"""

        conditions = [
            CalendarEvent.user_id == uuid.UUID(user_id),
            CalendarEvent.start_time >= start_date,
            CalendarEvent.start_time <= end_date,
        ]

        if event_type:
            conditions.append(CalendarEvent.event_type == event_type)

        if not include_cancelled:
            conditions.append(CalendarEvent.is_cancelled == False)

        result = await self.db.execute(
            select(CalendarEvent)
            .where(and_(*conditions))
            .order_by(CalendarEvent.start_time)
        )
        return list(result.scalars().all())

    async def get_upcoming_events(
        self,
        user_id: str,
        limit: int = 10,
        days_ahead: int = 30,
    ) -> List[CalendarEvent]:
        """Get upcoming events for user"""

        now = datetime.now()
        end_date = now + timedelta(days=days_ahead)

        result = await self.db.execute(
            select(CalendarEvent)
            .where(
                and_(
                    CalendarEvent.user_id == uuid.UUID(user_id),
                    CalendarEvent.start_time >= now,
                    CalendarEvent.start_time <= end_date,
                    CalendarEvent.is_cancelled == False,
                )
            )
            .order_by(CalendarEvent.start_time)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_events_paginated(
        self,
        user_id: str,
        page: int = 1,
        size: int = 50,
        event_type: Optional[str] = None,
    ) -> Tuple[List[CalendarEvent], int]:
        """Get paginated calendar events"""

        conditions = [CalendarEvent.user_id == uuid.UUID(user_id)]

        if event_type:
            conditions.append(CalendarEvent.event_type == event_type)

        # Count total
        count_result = await self.db.execute(
            select(func.count()).select_from(CalendarEvent).where(and_(*conditions))
        )
        total = count_result.scalar_one()

        # Get page
        offset = (page - 1) * size
        result = await self.db.execute(
            select(CalendarEvent)
            .where(and_(*conditions))
            .order_by(CalendarEvent.start_time.desc())
            .offset(offset)
            .limit(size)
        )
        events = list(result.scalars().all())

        return events, total

    async def update_event(
        self, event_id: str, user_id: str, event_data: CalendarEventUpdate
    ) -> Optional[CalendarEvent]:
        """Update calendar event"""

        event = await self.get_event_by_id(event_id, user_id)
        if not event:
            return None

        # Update fields
        update_data = event_data.model_dump(exclude_unset=True)

        # Validate time changes
        if "start_time" in update_data or "end_time" in update_data:
            start = update_data.get("start_time", event.start_time)
            end = update_data.get("end_time", event.end_time)
            if end <= start:
                raise ValueError("end_time must be after start_time")

        for field, value in update_data.items():
            setattr(event, field, value)

        event.updated_at = datetime.now()

        await self.db.commit()
        await self.db.refresh(event)

        logger.info(f"Updated calendar event {event_id} for user {user_id}")
        return event

    async def delete_event(self, event_id: str, user_id: str) -> bool:
        """Delete calendar event"""

        event = await self.get_event_by_id(event_id, user_id)
        if not event:
            return False

        await self.db.delete(event)
        await self.db.commit()

        logger.info(f"Deleted calendar event {event_id} for user {user_id}")
        return True

    async def mark_event_completed(
        self, event_id: str, user_id: str
    ) -> Optional[CalendarEvent]:
        """Mark event as completed"""

        event = await self.get_event_by_id(event_id, user_id)
        if not event:
            return None

        event.is_completed = True
        event.updated_at = datetime.now()

        await self.db.commit()
        await self.db.refresh(event)

        logger.info(f"Marked event {event_id} as completed for user {user_id}")
        return event

    async def cancel_event(
        self, event_id: str, user_id: str
    ) -> Optional[CalendarEvent]:
        """Cancel event"""

        event = await self.get_event_by_id(event_id, user_id)
        if not event:
            return None

        event.is_cancelled = True
        event.updated_at = datetime.now()

        await self.db.commit()
        await self.db.refresh(event)

        logger.info(f"Cancelled event {event_id} for user {user_id}")
        return event

    async def get_events_needing_reminders(
        self, minutes_ahead: int = 15
    ) -> List[CalendarEvent]:
        """Get events that need reminder notifications"""

        now = datetime.now()
        target_time = now + timedelta(minutes=minutes_ahead)

        result = await self.db.execute(
            select(CalendarEvent).where(
                and_(
                    CalendarEvent.reminder_minutes.isnot(None),
                    CalendarEvent.reminder_sent == False,
                    CalendarEvent.is_cancelled == False,
                    CalendarEvent.start_time > now,
                    CalendarEvent.start_time <= target_time,
                )
            )
        )
        return list(result.scalars().all())

    async def mark_reminder_sent(self, event_id: str) -> None:
        """Mark reminder as sent"""

        result = await self.db.execute(
            select(CalendarEvent).where(CalendarEvent.id == uuid.UUID(event_id))
        )
        event = result.scalar_one_or_none()

        if event:
            event.reminder_sent = True
            await self.db.commit()
            logger.info(f"Marked reminder sent for event {event_id}")
