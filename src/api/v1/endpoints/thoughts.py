"""
Therapy Notes Endpoints

Therapie-Notizen-API für Selbstreflexion und professionelle Therapie.
Vollständige Funktionalität auch ohne Therapeut.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from datetime import date, datetime
import logging

from src.core.database import get_async_session
from src.core.security import get_current_user_id, create_rate_limit_dependency
from src.schemas.ai import (
    TherapyNoteCreate, TherapyNoteResponse, TherapyNoteUpdate,
    PaginationParams, PaginatedResponse, SuccessResponse
)
from src.services.therapy_service import TherapyService
from src.services.ai_integration_service import AIIntegrationService

logger = logging.getLogger(__name__)

router = APIRouter()

# Rate limiting
therapy_rate_limit = create_rate_limit_dependency(limit=30, window_minutes=60)

@router.post("/", response_model=TherapyNoteResponse)
async def create_therapy_note(
    note_data: TherapyNoteCreate,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
    _rate_limit = Depends(therapy_rate_limit)
) -> Dict[str, Any]:
    """
    Create Therapy Note
    
    Erstellt eine neue Therapie-Notiz mit AI-Analyse.
    Funktioniert für Selbstreflexion und professionelle Therapie.
    """
    try:
        therapy_service = TherapyService(db)
        
        # Therapy Note erstellen
        therapy_note = await therapy_service.create_therapy_note(
            user_id=user_id,
            note_data=note_data
        )
        
        # AI-Analyse mit unserer Custom AI
        ai_engine = request.app.state.ai_engine
        if ai_engine and ai_engine.is_ready():
            ai_integration = AIIntegrationService(ai_engine)
            ai_analysis = await ai_integration.analyze_therapy_note(therapy_note)
            
            # Speichere AI-Analyse
            await therapy_service.update_ai_analysis(therapy_note.id, ai_analysis)
        else:
            ai_analysis = {"ai_generated": False, "message": "AI temporär nicht verfügbar"}
        
        logger.info(f"Therapy note created for user {user_id}: {note_data.note_type}")
        
        return {
            **therapy_note.__dict__,
            "ai_insights": ai_analysis.get("progress_insights"),
            "progress_analysis": ai_analysis.get("goal_assessment"),
            "suggested_next_steps": ai_analysis.get("suggested_next_steps", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create therapy note: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Therapie-Notiz konnte nicht erstellt werden"
        )

@router.get("/", response_model=PaginatedResponse)
async def get_therapy_notes(
    pagination: PaginationParams = Depends(),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    note_type: Optional[str] = Query(None, description="Note type filter"),
    search: Optional[str] = Query(None, description="Search in title and content"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Get Therapy Notes
    
    Holt alle Therapie-Notizen mit Filteroptionen.
    """
    try:
        therapy_service = TherapyService(db)
        
        # Notes mit Filtern holen
        entries, total_count = await therapy_service.get_therapy_notes_paginated(
            user_id=user_id,
            pagination=pagination,
            start_date=start_date,
            end_date=end_date,
            note_type=note_type,
            search=search
        )
        
        # Pagination berechnen
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
        logger.error(f"Failed to get therapy notes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Therapie-Notizen konnten nicht geladen werden"
        )

@router.get("/{note_id}", response_model=TherapyNoteResponse)
async def get_therapy_note(
    note_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Get Single Therapy Note
    """
    try:
        therapy_service = TherapyService(db)
        
        therapy_note = await therapy_service.get_therapy_note_by_id(note_id, user_id)
        
        if not therapy_note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Therapie-Notiz nicht gefunden"
            )
        
        return therapy_note.__dict__
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get therapy note: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Therapie-Notiz konnte nicht geladen werden"
        )

@router.put("/{note_id}", response_model=TherapyNoteResponse)
async def update_therapy_note(
    note_id: str,
    update_data: TherapyNoteUpdate,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Update Therapy Note
    
    Bei Inhaltsänderungen wird AI-Analyse neu durchgeführt.
    """
    try:
        therapy_service = TherapyService(db)
        
        # Prüfen ob Note existiert
        existing_note = await therapy_service.get_therapy_note_by_id(note_id, user_id)
        if not existing_note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Therapie-Notiz nicht gefunden"
            )
        
        # Update durchführen
        updated_note = await therapy_service.update_therapy_note(
            note_id=note_id,
            user_id=user_id,
            update_data=update_data
        )
        
        # AI-Analyse neu durchführen falls Inhalt geändert
        content_changed = any(field in update_data.dict(exclude_unset=True) 
                            for field in ['content', 'key_insights', 'progress_made'])
        
        if content_changed:
            ai_engine = request.app.state.ai_engine
            if ai_engine and ai_engine.is_ready():
                ai_integration = AIIntegrationService(ai_engine)
                ai_analysis = await ai_integration.analyze_therapy_note(updated_note)
                await therapy_service.update_ai_analysis(updated_note.id, ai_analysis)
        
        logger.info(f"Therapy note updated: {note_id}")
        
        return updated_note.__dict__
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update therapy note: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Therapie-Notiz konnte nicht aktualisiert werden"
        )

@router.delete("/{note_id}", response_model=SuccessResponse)
async def delete_therapy_note(
    note_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Delete Therapy Note
    """
    try:
        therapy_service = TherapyService(db)
        
        existing_note = await therapy_service.get_therapy_note_by_id(note_id, user_id)
        if not existing_note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Therapie-Notiz nicht gefunden"
            )
        
        await therapy_service.delete_therapy_note(note_id, user_id)
        
        logger.info(f"Therapy note deleted: {note_id}")
        
        return {
            "success": True,
            "message": "Therapie-Notiz erfolgreich gelöscht"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete therapy note: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Therapie-Notiz konnte nicht gelöscht werden"
        )

@router.post("/quick-reflection")
async def quick_reflection(
    reflection_text: str = Query(..., min_length=10, max_length=1000, description="Schnelle Reflexion"),
    current_mood: int = Query(..., ge=1, le=10, description="Aktuelle Stimmung"),
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
    _rate_limit = Depends(therapy_rate_limit)
) -> Dict[str, Any]:
    """
    Quick Self-Reflection
    
    Schnelle Selbstreflexion mit AI-Feedback.
    Perfekt für Nutzer ohne Therapeut.
    """
    try:
        therapy_service = TherapyService(db)
        
        # Quick Reflection Entry erstellen
        quick_note = await therapy_service.create_quick_reflection(
            user_id=user_id,
            reflection_text=reflection_text,
            current_mood=current_mood
        )
        
        # AI-Feedback für Selbstreflexion
        ai_engine = request.app.state.ai_engine
        if ai_engine and ai_engine.is_ready():
            
            # Reflexions-Prompt für AI
            reflection_prompt = f"""Ich habe gerade über mich reflektiert:

"{reflection_text}"

Meine aktuelle Stimmung: {current_mood}/10

Gib mir einfühlsames Feedback und 2-3 konkrete Anregungen für weitere Selbstreflexion oder Selbstfürsorge."""
            
            feedback_response = await ai_engine.generate_chat_response(
                user_message=reflection_prompt,
                user_context={
                    "mode": "self_reflection_feedback",
                    "mood": current_mood
                }
            )
            
            ai_feedback = {
                "reflection_feedback": feedback_response["response"],
                "confidence": feedback_response.get("confidence", 0.8)
            }
        else:
            ai_feedback = {"message": "AI-Feedback nicht verfügbar"}
        
        logger.info(f"Quick reflection created for user {user_id}")
        
        return {
            "success": True,
            "data": {
                "reflection_id": str(quick_note.id),
                "ai_feedback": ai_feedback,
                "encouragement": "Selbstreflexion ist ein wichtiger Schritt zur persönlichen Entwicklung! 🌱",
                "next_steps": [
                    "Überlege, was du aus dieser Reflexion mitnimmst",
                    "Setze dir ein kleines Ziel für heute",
                    "Wiederhole Reflexionen regelmäßig"
                ],
                "self_care_tips": therapy_service.get_self_care_suggestions(current_mood)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to create quick reflection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Schnelle Reflexion fehlgeschlagen"
        )

@router.get("/analytics/progress")
async def get_therapy_progress(
    days: int = Query(30, ge=7, le=365, description="Anzahl Tage für Analyse"),
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Therapy Progress Analysis
    
    Analysiert Therapie-Fortschritte mit AI-Unterstützung.
    Funktioniert auch für Selbsthilfe ohne Therapeut.
    """
    try:
        therapy_service = TherapyService(db)
        
        # Basis-Fortschrittsanalyse
        progress = await therapy_service.analyze_therapy_progress(user_id, days)
        
        # AI-Enhanced Progress Analysis
        ai_engine = request.app.state.ai_engine
        if ai_engine and ai_engine.is_ready() and progress.get("total_notes", 0) > 2:
            
            # Progress Summary für AI
            progress_summary = therapy_service.build_progress_summary(progress)
            
            # AI Progress Insights
            progress_prompt = f"""Analysiere diesen Therapie-/Selbsthilfe-Fortschritt:

{progress_summary}

Erkenne Entwicklungsmuster, Fortschritte und Bereiche für weiteres Wachstum. Gib ermutigende und konstruktive Insights."""
            
            ai_insights_response = await ai_engine.generate_chat_response(
                user_message=progress_prompt,
                user_context={"mode": "therapy_progress_analysis"}
            )
            
            progress["ai_insights"] = ai_insights_response["response"]
            progress["ai_generated"] = True
        
        return {
            "success": True,
            "data": progress
        }
        
    except Exception as e:
        logger.error(f"Failed to get therapy progress: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Therapie-Fortschritt konnte nicht analysiert werden"
        )

@router.get("/tools/self-help")
async def get_self_help_tools(
    request: Request,
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """
    Self-Help Tools & Techniques
    
    Sammlung von Selbsthilfe-Tools und Techniken mit AI-Personalisierung.
    """
    try:
        # Standard Selbsthilfe-Tools
        base_tools = {
            "thought_challenging": {
                "name": "Gedanken hinterfragen",
                "description": "Negative Gedanken identifizieren und umformulieren",
                "steps": [
                    "Identifiziere den negativen Gedanken",
                    "Frage: Ist dieser Gedanke wirklich wahr?",
                    "Suche nach Beweisen für und gegen den Gedanken",
                    "Formuliere einen ausgewogeneren Gedanken"
                ]
            },
            "mood_monitoring": {
                "name": "Stimmungsmonitoring",
                "description": "Regelmäßige Stimmungsverfolgung für Selbstbewusstsein",
                "steps": [
                    "Täglich Stimmung bewerten (1-10)",
                    "Auslöser und Muster identifizieren",
                    "Zusammenhänge erkennen",
                    "Strategien für schwierige Zeiten entwickeln"
                ]
            },
            "grounding_techniques": {
                "name": "Erdungstechniken",
                "description": "Bei Angst oder Überforderung im Moment ankommen",
                "steps": [
                    "5 Dinge die du siehst",
                    "4 Dinge die du hörst", 
                    "3 Dinge die du fühlst",
                    "2 Dinge die du riechst",
                    "1 Ding das du schmeckst"
                ]
            },
            "progressive_relaxation": {
                "name": "Progressive Muskelentspannung",
                "description": "Körperliche Anspannung gezielt lösen",
                "steps": [
                    "Bequeme Position einnehmen",
                    "Bei den Füßen beginnen",
                    "Muskelgruppen 5 Sekunden anspannen",
                    "Entspannung 10 Sekunden spüren",
                    "Systematisch durch den Körper arbeiten"
                ]
            }
        }
        
        # AI-personalisierte Empfehlungen
        ai_engine = request.app.state.ai_engine
        ai_recommendations = None
        
        if ai_engine and ai_engine.is_ready():
            try:
                # Hol aktuelle Stimmungslage (vereinfacht)
                personalization_prompt = """Welche Selbsthilfe-Techniken sind besonders hilfreich für jemanden, der:
- Regelmäßig Stimmung trackt
- An persönlicher Entwicklung interessiert ist
- Eigenverantwortlich an mentaler Gesundheit arbeitet

Gib 3 konkrete, umsetzbare Empfehlungen."""
                
                ai_response = await ai_engine.generate_chat_response(
                    user_message=personalization_prompt,
                    user_context={"mode": "self_help_recommendations"}
                )
                
                ai_recommendations = ai_response["response"]
                
            except Exception as e:
                logger.warning(f"AI recommendations failed: {e}")
        
        return {
            "success": True,
            "data": {
                "tools": base_tools,
                "ai_recommendations": ai_recommendations,
                "daily_practices": [
                    "🌅 Morgenreflexion: Wie geht es mir heute?",
                    "📝 Abendnotiz: Was war gut heute?",
                    "🧘 5-Minuten Achtsamkeit",
                    "💪 Eine kleine Selbstfürsorge-Handlung"
                ],
                "crisis_resources": {
                    "emergency_contacts": [
                        {"name": "Telefonseelsorge", "phone": "0800 111 0 111"},
                        {"name": "Nummer gegen Kummer", "phone": "116 123"}
                    ],
                    "immediate_help": [
                        "Tiefe Atemzüge nehmen",
                        "Einen Vertrauensmenschen anrufen",
                        "Notfallkontakte nutzen",
                        "Professionelle Hilfe suchen"
                    ]
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get self-help tools: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Selbsthilfe-Tools konnten nicht geladen werden"
        )

@router.get("/statistics/personal")
async def get_personal_therapy_stats(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Personal Therapy Statistics
    
    Persönliche Therapie-/Selbsthilfe-Statistiken.
    """
    try:
        therapy_service = TherapyService(db)
        
        # Verschiedene Zeiträume
        weekly_stats = await therapy_service.get_therapy_statistics(user_id, 7)
        monthly_stats = await therapy_service.get_therapy_statistics(user_id, 30)
        
        # Goal tracking
        goal_progress = await therapy_service.analyze_goal_progress(user_id)
        
        # Insight patterns
        insight_patterns = await therapy_service.analyze_insight_patterns(user_id)
        
        return {
            "success": True,
            "data": {
                "weekly_stats": weekly_stats,
                "monthly_stats": monthly_stats,
                "goal_progress": goal_progress,
                "insight_patterns": insight_patterns,
                "motivation_message": therapy_service.get_motivation_message(monthly_stats),
                "self_development_tips": [
                    "📚 Reflektiere regelmäßig über deine Fortschritte",
                    "🎯 Setze dir kleine, erreichbare Ziele", 
                    "🌱 Feiere auch kleine Erfolge",
                    "💭 Schreibe Erkenntnisse auf, um sie zu vertiefen"
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get personal therapy stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Persönliche Therapie-Statistiken konnten nicht geladen werden"
        )
