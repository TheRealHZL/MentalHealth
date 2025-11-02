"""
Calendar Models

Datenbank-Modelle für Kalender-Events und Erinnerungen.
"""

import enum
import uuid

from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Integer, String, Text)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


# =============================================================================
# Calendar Event Models
# =============================================================================


class EventType(enum.Enum):
    """Event type enumeration"""

    THERAPY_SESSION = "therapy_session"
    REMINDER = "reminder"
    PERSONAL = "personal"
    MEDICATION = "medication"
    APPOINTMENT = "appointment"


class RecurrencePattern(enum.Enum):
    """Recurrence pattern enumeration"""

    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class CalendarEvent(Base):
    """Calendar events and reminders"""

    __tablename__ = "calendar_events"

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Event details
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Time information
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False)

    # Event classification
    event_type = Column(String(50), nullable=False, index=True)  # therapy_session, reminder, etc.
    color = Column(String(7), nullable=True)  # Hex color code

    # Recurrence
    is_recurring = Column(Boolean, default=False, nullable=False)
    recurrence_pattern = Column(String(20), nullable=True)  # daily, weekly, monthly, yearly
    recurrence_end_date = Column(DateTime(timezone=True), nullable=True)

    # Reminder settings
    reminder_minutes = Column(Integer, nullable=True)  # Minutes before event
    reminder_sent = Column(Boolean, default=False, nullable=False)

    # Therapy note reference (optional)
    therapy_note_id = Column(UUID(as_uuid=True), ForeignKey("therapy_notes.id"), nullable=True)

    # Status and notes
    is_completed = Column(Boolean, default=False, nullable=False)
    is_cancelled = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="calendar_events")
    therapy_note = relationship("TherapyNote", back_populates="calendar_events")

    def __repr__(self):
        return f"<CalendarEvent(id={self.id}, title={self.title}, type={self.event_type}, start={self.start_time})>"

    @property
    def is_past(self):
        """Check if event is in the past"""
        from datetime import datetime, timezone
        return self.end_time < datetime.now(timezone.utc)

    @property
    def is_today(self):
        """Check if event is today"""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        return self.start_time.date() == now.date()

    @property
    def is_upcoming(self):
        """Check if event is upcoming"""
        from datetime import datetime, timezone
        return self.start_time > datetime.now(timezone.utc) and not self.is_cancelled
