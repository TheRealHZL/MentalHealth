"""
Calendar Endpoints

Kalenderverwaltung für Termine, Therapiesitzungen und Erinnerungen.
"""

import logging
import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.security import create_rate_limit_dependency, get_current_user_id
from app.modules.calendar.service import CalendarService
from app.schemas.calendar import (
    CalendarEventCreate,
    CalendarEventResponse,
    CalendarEventsListResponse,
    CalendarEventUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Rate limiting for calendar endpoints
calendar_rate_limit = create_rate_limit_dependency(limit=100, window_minutes=60)


# ========================================
# Calendar Event Endpoints
# ========================================


@router.post("/events", response_model=CalendarEventResponse, status_code=status.HTTP_201_CREATED)
async def create_calendar_event(
    event_data: CalendarEventCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
    _rate_limit=Depends(calendar_rate_limit),
) -> Dict[str, Any]:
    """
    Create Calendar Event

    Erstellt einen neuen Kalendereintrag (Termin, Therapiesitzung, Erinnerung, etc.).

    **Event Types:**
    - `therapy_session`: Therapiesitzung
    - `reminder`: Erinnerung
    - `personal`: Persönlicher Termin
    - `medication`: Medikamenteneinnahme
    - `appointment`: Allgemeiner Termin

    **Recurrence Patterns:**
    - `daily`: Täglich
    - `weekly`: Wöchentlich
    - `monthly`: Monatlich
    - `yearly`: Jährlich
    """
    try:
        calendar_service = CalendarService(db)
        event = await calendar_service.create_event(user_id, event_data)

        return CalendarEventResponse.model_validate(event)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error creating calendar event: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Erstellen des Kalendereintrags",
        )


@router.get("/events/{event_id}", response_model=CalendarEventResponse)
async def get_calendar_event(
    event_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
    _rate_limit=Depends(calendar_rate_limit),
) -> Dict[str, Any]:
    """
    Get Calendar Event

    Ruft einen spezifischen Kalendereintrag ab.
    """
    try:
        calendar_service = CalendarService(db)
        event = await calendar_service.get_event_by_id(event_id, user_id)

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Kalendereintrag nicht gefunden",
            )

        return CalendarEventResponse.model_validate(event)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting calendar event: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Abrufen des Kalendereintrags",
        )


@router.get("/events", response_model=CalendarEventsListResponse)
async def list_calendar_events(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
    _rate_limit=Depends(calendar_rate_limit),
) -> Dict[str, Any]:
    """
    List Calendar Events

    Ruft alle Kalendereinträge des Benutzers ab (paginiert).

    **Query Parameters:**
    - `page`: Seitennummer (Standard: 1)
    - `size`: Anzahl pro Seite (Standard: 50, Max: 100)
    - `event_type`: Filter nach Event-Typ (optional)
    """
    try:
        calendar_service = CalendarService(db)
        events, total = await calendar_service.get_events_paginated(
            user_id, page, size, event_type
        )

        return CalendarEventsListResponse(
            items=[CalendarEventResponse.model_validate(event) for event in events],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total > 0 else 0,
        )

    except Exception as e:
        logger.error(f"Error listing calendar events: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Abrufen der Kalendereinträge",
        )


@router.get("/events/range", response_model=List[CalendarEventResponse])
async def get_events_by_date_range(
    start_date: datetime = Query(..., description="Start date (ISO format)"),
    end_date: datetime = Query(..., description="End date (ISO format)"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    include_cancelled: bool = Query(False, description="Include cancelled events"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
    _rate_limit=Depends(calendar_rate_limit),
) -> List[Dict[str, Any]]:
    """
    Get Events by Date Range

    Ruft Kalendereinträge innerhalb eines Datumsbereichs ab.

    **Query Parameters:**
    - `start_date`: Startdatum (ISO 8601 Format)
    - `end_date`: Enddatum (ISO 8601 Format)
    - `event_type`: Filter nach Event-Typ (optional)
    - `include_cancelled`: Abgesagte Events einschließen (Standard: false)
    """
    try:
        if end_date <= start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="end_date must be after start_date",
            )

        calendar_service = CalendarService(db)
        events = await calendar_service.get_events_by_date_range(
            user_id, start_date, end_date, event_type, include_cancelled
        )

        return [CalendarEventResponse.model_validate(event) for event in events]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting events by date range: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Abrufen der Kalendereinträge",
        )


@router.get("/events/upcoming", response_model=List[CalendarEventResponse])
async def get_upcoming_events(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of events"),
    days_ahead: int = Query(30, ge=1, le=365, description="Days to look ahead"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
    _rate_limit=Depends(calendar_rate_limit),
) -> List[Dict[str, Any]]:
    """
    Get Upcoming Events

    Ruft kommende Kalendereinträge ab.

    **Query Parameters:**
    - `limit`: Maximale Anzahl (Standard: 10, Max: 50)
    - `days_ahead`: Tage im Voraus (Standard: 30, Max: 365)
    """
    try:
        calendar_service = CalendarService(db)
        events = await calendar_service.get_upcoming_events(user_id, limit, days_ahead)

        return [CalendarEventResponse.model_validate(event) for event in events]

    except Exception as e:
        logger.error(f"Error getting upcoming events: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Abrufen kommender Events",
        )


@router.put("/events/{event_id}", response_model=CalendarEventResponse)
async def update_calendar_event(
    event_id: str,
    event_data: CalendarEventUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
    _rate_limit=Depends(calendar_rate_limit),
) -> Dict[str, Any]:
    """
    Update Calendar Event

    Aktualisiert einen bestehenden Kalendereintrag.
    """
    try:
        calendar_service = CalendarService(db)
        event = await calendar_service.update_event(event_id, user_id, event_data)

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Kalendereintrag nicht gefunden",
            )

        return CalendarEventResponse.model_validate(event)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error updating calendar event: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Aktualisieren des Kalendereintrags",
        )


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_calendar_event(
    event_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
    _rate_limit=Depends(calendar_rate_limit),
) -> None:
    """
    Delete Calendar Event

    Löscht einen Kalendereintrag permanent.
    """
    try:
        calendar_service = CalendarService(db)
        deleted = await calendar_service.delete_event(event_id, user_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Kalendereintrag nicht gefunden",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting calendar event: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Löschen des Kalendereintrags",
        )


@router.post("/events/{event_id}/complete", response_model=CalendarEventResponse)
async def mark_event_completed(
    event_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
    _rate_limit=Depends(calendar_rate_limit),
) -> Dict[str, Any]:
    """
    Mark Event as Completed

    Markiert einen Kalendereintrag als abgeschlossen.
    """
    try:
        calendar_service = CalendarService(db)
        event = await calendar_service.mark_event_completed(event_id, user_id)

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Kalendereintrag nicht gefunden",
            )

        return CalendarEventResponse.model_validate(event)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking event completed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Aktualisieren des Events",
        )


@router.post("/events/{event_id}/cancel", response_model=CalendarEventResponse)
async def cancel_event(
    event_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
    _rate_limit=Depends(calendar_rate_limit),
) -> Dict[str, Any]:
    """
    Cancel Event

    Markiert einen Kalendereintrag als abgesagt.
    """
    try:
        calendar_service = CalendarService(db)
        event = await calendar_service.cancel_event(event_id, user_id)

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Kalendereintrag nicht gefunden",
            )

        return CalendarEventResponse.model_validate(event)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling event: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Absagen des Events",
        )
