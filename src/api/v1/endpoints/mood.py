"""
Mood Tracking Endpoints

Stimmungstagebuch-API für Selbsthilfe-Nutzer und Patienten.
Vollständige Funktionalität auch ohne Therapeut.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from datetime import date, datetime
import logging

from src.core.database import get_async_session
from src.core.security import get_current_user_id, create_rate_limit_dependency
from src.schemas.ai import (
    MoodEntryCreate, MoodEntryResponse, MoodEntryUpdate,
    PaginationParams, PaginatedResponse, SuccessResponse
)
from src.services.mood_service import MoodService
from src.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter()

# Rate limiting für Mood-Endpunkte
mood_rate_limit = create_rate_limit_dependency(limit=50, window_minutes=60)

@router.post("/", response_model=MoodEntryResponse)
async def create_mood_entry(
    mood_data: MoodEntryCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
    _rate_limit = Depends(mood_rate_limit)
) -> Dict[str, Any]:
    """
    Create Mood Entry
    
    Erstellt einen neuen Stimmungseintrag.
    Funktioniert für alle Nutzer (mit/ohne Therapeut).
    """
    try:
        mood_service = MoodService(db)
        
        # Prüfen ob bereits Eintrag für heute existiert
        existing_entry = await mood_service.get_mood_entry_by_date(
            user_id, mood_data.date, mood_data.time
        )
        
        if existing_entry:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Stimmungseintrag für diese Zeit existiert bereits"
            )
        
        # Mood Entry erstellen
        mood_entry = await mood_service.create_mood_entry(
            user_id=user_id,
            mood_data=mood_data
        )
        
        # AI-Analyse ausführen (falls aktiviert)
        ai_analysis = await mood_service.analyze_mood_entry(mood_entry)
        
        logger.info(f"Mood entry created for user {user_id}")
        
        return {
            **mood_entry.__dict__,
            "ai_analysis": ai_analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create mood entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stimmungseintrag konnte nicht erstellt werden"
        )

@router.get("/", response_model=PaginatedResponse)
async def get_mood_entries(
    pagination: PaginationParams = Depends(),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    min_mood: Optional[int] = Query(None, ge=1, le=10, description="Minimum mood score"),
    max_mood: Optional[int] = Query(None, ge=1, le=10, description="Maximum mood score"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Get Mood Entries
    
    Holt alle Stimmungseinträge mit Filteroptionen.
    """
    try:
        mood_service = MoodService(db)
        
        # Mood Entries mit Filtern holen
        entries, total_count = await mood_service.get_mood_entries_paginated(
            user_id=user_id,
            pagination=pagination,
            start_date=start_date,
            end_date=end_date,
            min_mood=min_mood,
            max_mood=max_mood
        )
        
        # Pagination Meta-Daten
        total_pages = (total_count + pagination.page_size - 1) // pagination.page_size
        has_next = pagination.page < total_pages
        has_prev = pagination.page > 1
        
        return {
            "items": entries,
            "total": total_count,
            "page": pagination.page,
            "page_size": pagination.page_size,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_prev": has_prev
        }
        
    except Exception as e:
        logger.error(f"Failed to get mood entries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stimmungseinträge konnten nicht geladen werden"
        )

@router.get("/{entry_id}", response_model=MoodEntryResponse)
async def get_mood_entry(
    entry_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Get Single Mood Entry
    """
    try:
        mood_service = MoodService(db)
        
        mood_entry = await mood_service.get_mood_entry_by_id(entry_id, user_id)
        
        if not mood_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Stimmungseintrag nicht gefunden"
            )
        
        return mood_entry.__dict__
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get mood entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stimmungseintrag konnte nicht geladen werden"
        )

@router.put("/{entry_id}", response_model=MoodEntryResponse)
async def update_mood_entry(
    entry_id: str,
    update_data: MoodEntryUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Update Mood Entry
    """
    try:
        mood_service = MoodService(db)
        
        # Prüfen ob Entry existiert und dem User gehört
        existing_entry = await mood_service.get_mood_entry_by_id(entry_id, user_id)
        if not existing_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Stimmungseintrag nicht gefunden"
            )
        
        # Update durchführen
        updated_entry = await mood_service.update_mood_entry(
            entry_id=entry_id,
            user_id=user_id,
            update_data=update_data
        )
        
        # AI-Analyse neu durchführen falls relevante Felder geändert
        ai_analysis = await mood_service.analyze_mood_entry(updated_entry)
        
        logger.info(f"Mood entry updated: {entry_id}")
        
        return {
            **updated_entry.__dict__,
            "ai_analysis": ai_analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update mood entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stimmungseintrag konnte nicht aktualisiert werden"
        )

@router.delete("/{entry_id}", response_model=SuccessResponse)
async def delete_mood_entry(
    entry_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Delete Mood Entry
    """
    try:
        mood_service = MoodService(db)
        
        # Prüfen ob Entry existiert und dem User gehört
        existing_entry = await mood_service.get_mood_entry_by_id(entry_id, user_id)
        if not existing_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Stimmungseintrag nicht gefunden"
            )
        
        # Löschen
        await mood_service.delete_mood_entry(entry_id, user_id)
        
        logger.info(f"Mood entry deleted: {entry_id}")
        
        return {
            "success": True,
            "message": "Stimmungseintrag erfolgreich gelöscht"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete mood entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stimmungseintrag konnte nicht gelöscht werden"
        )

@router.get("/analytics/trends")
async def get_mood_trends(
    days: int = Query(30, ge=7, le=365, description="Anzahl Tage für Trend-Analyse"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Get Mood Trends & Analytics
    
    Selbsthilfe-Analytics ohne Therapeut erforderlich.
    """
    try:
        analytics_service = AnalyticsService(db)
        
        # Mood Trend analysieren
        mood_trend = await analytics_service.get_mood_trend(user_id, days)
        
        # Zusätzliche Mood-spezifische Analytics
        mood_service = MoodService(db)
        correlations = await mood_service.analyze_mood_correlations(user_id, days)
        patterns = await mood_service.find_mood_patterns(user_id, days)
        
        return {
            "success": True,
            "data": {
                "mood_trend": mood_trend,
                "correlations": correlations,
                "patterns": patterns,
                "insights": await mood_service.generate_mood_insights(user_id),
                "recommendations": mood_service.get_mood_recommendations(mood_trend)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get mood trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stimmungstrends konnten nicht geladen werden"
        )

@router.get("/today/check-in")
async def todays_check_in(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Today's Check-In
    
    Heutiger Check-in Status und Empfehlungen.
    """
    try:
        mood_service = MoodService(db)
        
        # Heutigen Eintrag prüfen
        today = date.today()
        today_entry = await mood_service.get_mood_entries_by_date(user_id, today)
        
        # Check-in Status
        has_checked_in = len(today_entry) > 0
        
        if has_checked_in:
            latest_entry = today_entry[-1]  # Neuester Eintrag heute
            mood_score = latest_entry.mood_score
            
            # Tagesmuster analysieren
            day_analysis = await mood_service.analyze_daily_pattern(user_id, today)
            
            return {
                "success": True,
                "data": {
                    "has_checked_in": True,
                    "latest_mood": mood_score,
                    "entries_today": len(today_entry),
                    "day_analysis": day_analysis,
                    "next_suggestion": mood_service.suggest_next_check_in(mood_score),
                    "encouragement": mood_service.get_encouragement_message(mood_score)
                }
            }
        else:
            # Noch kein Check-in heute
            suggestions = await mood_service.get_check_in_suggestions(user_id)
            
            return {
                "success": True,
                "data": {
                    "has_checked_in": False,
                    "check_in_suggestions": suggestions,
                    "quick_mood_questions": mood_service.get_quick_mood_questions(),
                    "motivation": "Wie geht es dir heute? Ein kurzer Check-in hilft! 🌟"
                }
            }
        
    except Exception as e:
        logger.error(f"Failed to get today's check-in: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Heutiger Check-in konnte nicht geladen werden"
        )

@router.post("/quick-entry")
async def quick_mood_entry(
    mood_score: int = Query(..., ge=1, le=10, description="Schnelle Stimmungsbewertung"),
    note: Optional[str] = Query(None, max_length=200, description="Kurze Notiz"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
    _rate_limit = Depends(mood_rate_limit)
) -> Dict[str, Any]:
    """
    Quick Mood Entry
    
    Schneller Stimmungseintrag für zwischendurch.
    """
    try:
        mood_service = MoodService(db)
        
        # Quick Entry erstellen (mit Defaults)
        quick_entry = await mood_service.create_quick_mood_entry(
            user_id=user_id,
            mood_score=mood_score,
            note=note
        )
        
        # Sofortige Mini-Analyse
        mini_analysis = await mood_service.quick_mood_analysis(user_id, mood_score)
        
        logger.info(f"Quick mood entry created for user {user_id}: {mood_score}/10")
        
        return {
            "success": True,
            "data": {
                "entry_id": str(quick_entry.id),
                "mood_score": mood_score,
                "timestamp": quick_entry.created_at,
                "analysis": mini_analysis,
                "encouragement": mood_service.get_encouragement_message(mood_score),
                "next_steps": mood_service.suggest_follow_up_actions(mood_score)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to create quick mood entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Schneller Stimmungseintrag fehlgeschlagen"
        )

@router.get("/statistics/personal")
async def get_personal_mood_stats(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Personal Mood Statistics
    
    Persönliche Stimmungsstatistiken für Selbstreflexion.
    """
    try:
        mood_service = MoodService(db)
        analytics_service = AnalyticsService(db)
        
        # Verschiedene Zeiträume analysieren
        weekly_stats = await mood_service.get_mood_statistics(user_id, 7)
        monthly_stats = await mood_service.get_mood_statistics(user_id, 30)
        
        # Achievements und Insights
        achievements = await analytics_service.get_achievements(user_id)
        insights = await analytics_service.get_self_help_insights(user_id)
        
        return {
            "success": True,
            "data": {
                "weekly_stats": weekly_stats,
                "monthly_stats": monthly_stats,
                "achievements": achievements,
                "insights": insights,
                "progress_summary": await mood_service.generate_progress_summary(user_id),
                "motivational_message": mood_service.get_motivational_message(weekly_stats)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get personal mood stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Persönliche Statistiken konnten nicht geladen werden"
        )
