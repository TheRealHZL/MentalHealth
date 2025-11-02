"""
Calendar Event Schemas

Pydantic Schemas für Kalender-Events und Erinnerungen.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.core.sanitization import sanitize_html, sanitize_text


class CalendarEventCreate(BaseModel):
    """Create calendar event schema"""

    title: str = Field(..., min_length=1, max_length=200, description="Event title")
    description: Optional[str] = Field(None, max_length=2000, description="Event description")

    start_time: datetime = Field(..., description="Event start time (ISO format with timezone)")
    end_time: datetime = Field(..., description="Event end time (ISO format with timezone)")

    event_type: str = Field(..., description="Event type: therapy_session, reminder, personal, medication, appointment")
    color: Optional[str] = Field(None, max_length=7, description="Color hex code (#RRGGBB)")

    is_recurring: bool = Field(False, description="Is this a recurring event?")
    recurrence_pattern: Optional[str] = Field(None, description="Recurrence pattern: daily, weekly, monthly, yearly")
    recurrence_end_date: Optional[datetime] = Field(None, description="When does recurrence end?")

    reminder_minutes: Optional[int] = Field(None, ge=0, le=10080, description="Reminder minutes before event (max 1 week)")

    therapy_note_id: Optional[UUID] = Field(None, description="Associated therapy note ID")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")

    # Input Sanitization Validators (XSS Prevention)
    @field_validator("title", "description", "notes", mode="before")
    @classmethod
    def sanitize_text_fields(cls, v):
        """Sanitize text fields"""
        if v is not None:
            return sanitize_text(v)
        return v

    @field_validator("event_type", mode="before")
    @classmethod
    def validate_event_type(cls, v):
        """Validate event type"""
        valid_types = ["therapy_session", "reminder", "personal", "medication", "appointment"]
        if v not in valid_types:
            raise ValueError(f"event_type must be one of: {', '.join(valid_types)}")
        return v

    @field_validator("recurrence_pattern", mode="before")
    @classmethod
    def validate_recurrence_pattern(cls, v):
        """Validate recurrence pattern"""
        if v is not None:
            valid_patterns = ["daily", "weekly", "monthly", "yearly"]
            if v not in valid_patterns:
                raise ValueError(f"recurrence_pattern must be one of: {', '.join(valid_patterns)}")
        return v

    @field_validator("color", mode="before")
    @classmethod
    def validate_color(cls, v):
        """Validate hex color code"""
        if v is not None:
            if not v.startswith("#") or len(v) != 7:
                raise ValueError("color must be a valid hex color code (#RRGGBB)")
        return v


class CalendarEventUpdate(BaseModel):
    """Update calendar event schema"""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    event_type: Optional[str] = None
    color: Optional[str] = Field(None, max_length=7)

    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[str] = None
    recurrence_end_date: Optional[datetime] = None

    reminder_minutes: Optional[int] = Field(None, ge=0, le=10080)

    is_completed: Optional[bool] = None
    is_cancelled: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=1000)

    # Input Sanitization Validators (XSS Prevention)
    @field_validator("title", "description", "notes", mode="before")
    @classmethod
    def sanitize_text_fields(cls, v):
        """Sanitize text fields"""
        if v is not None:
            return sanitize_text(v)
        return v


class CalendarEventResponse(BaseModel):
    """Calendar event response schema"""

    id: str
    user_id: str

    title: str
    description: Optional[str] = None

    start_time: datetime
    end_time: datetime

    event_type: str
    color: Optional[str] = None

    is_recurring: bool
    recurrence_pattern: Optional[str] = None
    recurrence_end_date: Optional[datetime] = None

    reminder_minutes: Optional[int] = None
    reminder_sent: bool

    therapy_note_id: Optional[str] = None

    is_completed: bool
    is_cancelled: bool
    notes: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CalendarEventsListResponse(BaseModel):
    """List of calendar events response"""

    items: List[CalendarEventResponse]
    total: int
    page: int
    size: int
    pages: int
