"""
Schemas Module

Pydantic schemas for data validation and serialization
"""

from .base import BaseSchema
from .calendar import (
    CalendarEventCreate,
    CalendarEventResponse,
    CalendarEventsListResponse,
    CalendarEventUpdate,
)

__all__ = [
    "BaseSchema",
    "CalendarEventCreate",
    "CalendarEventResponse",
    "CalendarEventsListResponse",
    "CalendarEventUpdate",
]
