"""
Dream Journal Endpoints

Traumtagebuch-API mit echter AI-Traumdeutung und Symbolanalyse.
Vollständige Selbsthilfe-Funktionalität ohne Therapeut.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from datetime import date, datetime
from pydantic import BaseModel, Field
import logging
import base64
import uuid

from src.core.database import get_async_session
from src.core.security import get_current_user_id, create_rate_limit_dependency
from src.schemas.ai import (
    DreamEntryCreate, DreamEntryResponse, DreamEntryUpdate,
    PaginationParams, PaginatedResponse, SuccessResponse
)
from src.services.dream_service import DreamService
from src.services.ai_integration_service import AIIntegrationService
from src.services.encryption_service import EncryptionService
from src.models.encrypted_models import EncryptedDreamEntry
from sqlalchemy import select, and_

logger = logging.getLogger(__name__)

router = APIRouter()

# Rate limiting
dream_rate_limit = create_rate_limit_dependency(limit=20, window_minutes=60)


# ========================================
# Encrypted Dream Entry Models
# ========================================

class EncryptedDreamPayload(BaseModel):
    """Encrypted dream entry payload from client"""
    ciphertext: str = Field(description="Base64-encoded encrypted data")
    nonce: str = Field(description="Base64-encoded nonce (12 bytes)")
    version: int = Field(default=1, description="Encryption version")


class EncryptedDreamEntryCreate(BaseModel):
    """Create encrypted dream entry"""
    encrypted_data: EncryptedDreamPayload = Field(description="Encrypted dream data")
    entry_type: str = Field(default="dream", description="Entry type")


class EncryptedDreamEntryResponse(BaseModel):
    """Encrypted dream entry response"""
    id: str = Field(description="Entry ID")
    user_id: str = Field(description="User ID")
    encrypted_data: EncryptedDreamPayload = Field(description="Encrypted data")
    entry_type: str = Field(description="Entry type")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    encryption_version: int = Field(description="Encryption version")


# ========================================
# Original Dream Endpoints (Unencrypted)
# ========================================

@router.post("/", response_model=DreamEntryResponse)
async def create_dream_entry(
    request: Request,
    dream_data: DreamEntryCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
    _rate_limit = Depends(dream_rate_limit)
) -> Dict[str, Any]:
    """
    Create Dream Entry
    
    Erstellt einen neuen Traumeintrag mit AI-Analyse.
    """
    try:
        dream_service = DreamService(db)
        
        # Dream Entry erstellen
        dream_entry = await dream_service.create_dream_entry(
            user_id=user_id,
            dream_data=dream_data
        )
        
        # AI-Analyse mit unserer Custom AI
        ai_engine = request.app.state.ai_engine
        if ai_engine and ai_engine.is_ready():
            ai_integration = AIIntegrationService(ai_engine)
            ai_analysis = await ai_integration.analyze_dream_entry(dream_entry)
            
            # Speichere AI-Analyse im Entry
            await dream_service.update_ai_analysis(dream_entry.id, ai_analysis)
        else:
            ai_analysis = {"ai_generated": False, "message": "AI temporär nicht verfügbar"}
        
        logger.info(f"Dream entry created for user {user_id}: {dream_data.dream_type}")
        
        return {
            **dream_entry.__dict__,
            "ai_dream_analysis": ai_analysis.get("ai_interpretation"),
            "symbol_interpretations": ai_analysis.get("symbol_meanings", {}),
            "emotional_insights": ai_analysis.get("psychological_insights", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create dream entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Traumeintrag konnte nicht erstellt werden"
        )

@router.get("/", response_model=PaginatedResponse)
async def get_dream_entries(
    pagination: PaginationParams = Depends(),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    dream_type: Optional[str] = Query(None, description="Dream type filter"),
    mood_range: Optional[str] = Query(None, description="Mood range: low,medium,high"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Get Dream Entries
    
    Holt alle Traumeinträge mit Filteroptionen.
    """
    try:
        dream_service = DreamService(db)
        
        # Dreams mit Filtern holen
        entries, total_count = await dream_service.get_dream_entries_paginated(
            user_id=user_id,
            pagination=pagination,
            start_date=start_date,
            end_date=end_date,
            dream_type=dream_type,
            mood_range=mood_range
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
        logger.error(f"Failed to get dream entries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Traumeinträge konnten nicht geladen werden"
        )

@router.get("/{entry_id}", response_model=DreamEntryResponse)
async def get_dream_entry(
    entry_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Get Single Dream Entry
    """
    try:
        dream_service = DreamService(db)
        
        dream_entry = await dream_service.get_dream_entry_by_id(entry_id, user_id)
        
        if not dream_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Traumeintrag nicht gefunden"
            )
        
        return dream_entry.__dict__
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dream entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Traumeintrag konnte nicht geladen werden"
        )

@router.put("/{entry_id}", response_model=DreamEntryResponse)
async def update_dream_entry(
    entry_id: str,
    request: Request,
    update_data: DreamEntryUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Update Dream Entry
    
    Bei Änderungen wird AI-Analyse neu durchgeführt.
    """
    try:
        dream_service = DreamService(db)
        
        # Prüfen ob Entry existiert
        existing_entry = await dream_service.get_dream_entry_by_id(entry_id, user_id)
        if not existing_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Traumeintrag nicht gefunden"
            )
        
        # Update durchführen
        updated_entry = await dream_service.update_dream_entry(
            entry_id=entry_id,
            user_id=user_id,
            update_data=update_data
        )
        
        # AI-Analyse neu durchführen falls Inhalt geändert
        content_changed = any(field in update_data.dict(exclude_unset=True) 
                            for field in ['description', 'symbols', 'emotions_felt'])
        
        if content_changed:
            ai_engine = request.app.state.ai_engine
            if ai_engine and ai_engine.is_ready():
                ai_integration = AIIntegrationService(ai_engine)
                ai_analysis = await ai_integration.analyze_dream_entry(updated_entry)
                await dream_service.update_ai_analysis(updated_entry.id, ai_analysis)
        
        logger.info(f"Dream entry updated: {entry_id}")
        
        return updated_entry.__dict__
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update dream entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Traumeintrag konnte nicht aktualisiert werden"
        )

@router.delete("/{entry_id}", response_model=SuccessResponse)
async def delete_dream_entry(
    entry_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Delete Dream Entry
    """
    try:
        dream_service = DreamService(db)
        
        existing_entry = await dream_service.get_dream_entry_by_id(entry_id, user_id)
        if not existing_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Traumeintrag nicht gefunden"
            )
        
        await dream_service.delete_dream_entry(entry_id, user_id)
        
        logger.info(f"Dream entry deleted: {entry_id}")
        
        return {
            "success": True,
            "message": "Traumeintrag erfolgreich gelöscht"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete dream entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Traumeintrag konnte nicht gelöscht werden"
        )

@router.post("/interpret")
async def interpret_dream_symbols(
    request: Request,
    symbols: List[str] = Query(..., description="Dream symbols to interpret"),
    dream_context: Optional[str] = Query(None, description="Additional dream context"),
    user_id: str = Depends(get_current_user_id),
    _rate_limit = Depends(dream_rate_limit)
) -> Dict[str, Any]:
    """
    AI Dream Symbol Interpretation
    
    Interpretiert spezifische Traumsymbole mit unserer AI.
    """
    try:
        ai_engine = request.app.state.ai_engine
        
        if not ai_engine or not ai_engine.is_ready():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI-Traumdeutung temporär nicht verfügbar"
            )
        
        interpretations = {}
        
        for symbol in symbols[:5]:  # Limit zu 5 Symbolen
            # Prompt für Symbolinterpretation
            symbol_prompt = f"""Interpretiere das Traumsymbol '{symbol}' psychologisch.
            
Kontext: {dream_context or 'Kein zusätzlicher Kontext'}

Gib eine kurze, einfühlsame psychologische Interpretation. Erkläre mögliche Bedeutungen und Verbindungen zum Unterbewusstsein."""
            
            # AI-Interpretation
            interpretation_response = await ai_engine.generate_chat_response(
                user_message=symbol_prompt,
                user_context={
                    "mode": "dream_symbol_interpretation",
                    "symbol": symbol
                }
            )
            
            interpretations[symbol] = {
                "interpretation": interpretation_response["response"],
                "confidence": interpretation_response.get("confidence", 0.8)
            }
        
        logger.info(f"Dream symbols interpreted for user {user_id}: {symbols}")
        
        return {
            "success": True,
            "data": {
                "interpretations": interpretations,
                "general_advice": "Traumsymbole sind sehr persönlich. Diese Interpretationen sind Anregungen für deine eigene Reflexion.",
                "ai_generated": True
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dream symbol interpretation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Traumsymbol-Interpretation fehlgeschlagen"
        )

@router.get("/analytics/patterns")
async def get_dream_patterns(
    request: Request,
    days: int = Query(30, ge=7, le=365, description="Anzahl Tage für Analyse"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Dream Pattern Analysis
    
    Analysiert Traummuster mit AI-Unterstützung.
    """
    try:
        dream_service = DreamService(db)
        
        # Basis-Patterns
        patterns = await dream_service.analyze_dream_patterns(user_id, days)
        
        # AI-Enhanced Pattern Analysis
        ai_engine = request.app.state.ai_engine
        if ai_engine and ai_engine.is_ready() and patterns.get("total_dreams", 0) > 3:
            
            # Pattern Summary für AI
            pattern_summary = dream_service.build_pattern_summary(patterns)
            
            # AI Pattern Insights
            pattern_prompt = f"""Analysiere diese Traummuster und gib psychologische Insights:

{pattern_summary}

Erkenne Muster, mögliche Bedeutungen und gib einfühlsame Einblicke in die psychische Verfassung."""
            
            ai_insights_response = await ai_engine.generate_chat_response(
                user_message=pattern_prompt,
                user_context={"mode": "dream_pattern_analysis"}
            )
            
            patterns["ai_insights"] = ai_insights_response["response"]
            patterns["ai_generated"] = True
        
        return {
            "success": True,
            "data": patterns
        }
        
    except Exception as e:
        logger.error(f"Failed to get dream patterns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Traummuster-Analyse fehlgeschlagen"
        )

@router.post("/quick-entry")
async def quick_dream_entry(
    request: Request,
    dream_description: str = Query(..., min_length=10, max_length=500),
    dream_type: str = Query("normal", description="Dream type"),
    mood_after: int = Query(..., ge=1, le=10, description="Mood after waking"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
    _rate_limit = Depends(dream_rate_limit)
) -> Dict[str, Any]:
    """
    Quick Dream Entry
    
    Schneller Traumeintrag mit sofortiger AI-Analyse.
    """
    try:
        dream_service = DreamService(db)
        
        # Quick Dream Entry erstellen
        quick_dream = await dream_service.create_quick_dream_entry(
            user_id=user_id,
            description=dream_description,
            dream_type=dream_type,
            mood_after=mood_after
        )
        
        # Sofortige AI-Analyse
        ai_engine = request.app.state.ai_engine
        if ai_engine and ai_engine.is_ready():
            
            # Quick Analysis Prompt
            quick_analysis_prompt = f"""Kurze Traumanalyse:

Traum: {dream_description}
Stimmung nach dem Aufwachen: {mood_after}/10

Gib 2-3 kurze Insights über mögliche Bedeutung und emotionale Botschaft."""
            
            quick_analysis_response = await ai_engine.generate_chat_response(
                user_message=quick_analysis_prompt,
                user_context={"mode": "quick_dream_analysis"}
            )
            
            ai_analysis = {
                "quick_insights": quick_analysis_response["response"],
                "confidence": quick_analysis_response.get("confidence", 0.7)
            }
        else:
            ai_analysis = {"message": "AI-Analyse nicht verfügbar"}
        
        logger.info(f"Quick dream entry created for user {user_id}")
        
        return {
            "success": True,
            "data": {
                "dream_id": str(quick_dream.id),
                "ai_analysis": ai_analysis,
                "encouragement": "Traumtagebuch führen hilft beim Verstehen deines Unterbewusstseins! 🌙",
                "next_steps": [
                    "Füge später Details hinzu",
                    "Achte auf wiederkehrende Symbole",
                    "Verknüpfe mit deiner aktuellen Lebenssituation"
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to create quick dream entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Schneller Traumeintrag fehlgeschlagen"
        )

@router.get("/statistics/personal")
async def get_personal_dream_stats(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Personal Dream Statistics
    
    Persönliche Traumstatistiken für Selbstreflexion.
    """
    try:
        dream_service = DreamService(db)
        
        # Verschiedene Zeiträume
        weekly_stats = await dream_service.get_dream_statistics(user_id, 7)
        monthly_stats = await dream_service.get_dream_statistics(user_id, 30)
        
        # Most common elements
        common_elements = await dream_service.get_common_dream_elements(user_id)
        
        # Dream quality trends
        quality_trends = await dream_service.analyze_dream_quality_trends(user_id)
        
        return {
            "success": True,
            "data": {
                "weekly_stats": weekly_stats,
                "monthly_stats": monthly_stats,
                "common_elements": common_elements,
                "quality_trends": quality_trends,
                "insights": [
                    f"Du hast {monthly_stats.get('total_dreams', 0)} Träume im letzten Monat dokumentiert",
                    f"Häufigste Traumart: {monthly_stats.get('most_common_type', 'Normal')}",
                    f"Durchschnittliche Stimmung nach Träumen: {monthly_stats.get('avg_mood_after', 5):.1f}/10"
                ],
                "dream_journal_benefits": [
                    "🧠 Besseres Verständnis des Unterbewusstseins",
                    "🔍 Erkennung von Lebensmustern",
                    "💡 Kreative Inspiration durch Traumsymbole",
                    "🌙 Verbesserung der Traumerinnerung"
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get personal dream stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Persönliche Traumstatistiken konnten nicht geladen werden"
        )


# ========================================
# Encrypted Dream Endpoints (Zero-Knowledge)
# ========================================

@router.post("/encrypted", response_model=EncryptedDreamEntryResponse)
async def create_encrypted_dream_entry(
    dream_data: EncryptedDreamEntryCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
    _rate_limit = Depends(dream_rate_limit)
) -> Dict[str, Any]:
    """
    Create Encrypted Dream Entry (Zero-Knowledge)

    Accepts client-side encrypted dream data. The server CANNOT read the dream content!
    Only metadata (timestamps, user_id) is stored unencrypted for queries.

    **Zero-Knowledge:**
    - Dreams are encrypted in the browser
    - Server stores encrypted blobs
    - Server NEVER sees dream content, symbols, or emotions
    """
    try:
        # Validate encrypted payload structure
        payload_dict = {
            "ciphertext": dream_data.encrypted_data.ciphertext,
            "nonce": dream_data.encrypted_data.nonce,
            "version": dream_data.encrypted_data.version
        }

        is_valid, error_msg = EncryptionService.validate_encrypted_payload(payload_dict)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid encrypted payload: {error_msg}"
            )

        # Decode base64 to binary for storage
        ciphertext_bytes = base64.b64decode(dream_data.encrypted_data.ciphertext)
        nonce_bytes = base64.b64decode(dream_data.encrypted_data.nonce)

        # Combine ciphertext + nonce for storage
        encrypted_data = ciphertext_bytes + nonce_bytes

        # Validate size
        is_size_valid, size_error = EncryptionService.validate_encrypted_data_size(encrypted_data)
        if not is_size_valid:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=size_error
            )

        # Create encrypted dream entry
        entry = EncryptedDreamEntry(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            encrypted_data=encrypted_data,
            entry_type=dream_data.entry_type,
            encryption_version=dream_data.encrypted_data.version,
            is_deleted=False
        )

        db.add(entry)
        await db.commit()
        await db.refresh(entry)

        logger.info(f"Encrypted dream entry created for user {user_id}")

        # Extract nonce for response (last 12 bytes)
        stored_ciphertext = entry.encrypted_data[:-12]
        stored_nonce = entry.encrypted_data[-12:]

        return {
            "id": str(entry.id),
            "user_id": str(entry.user_id),
            "encrypted_data": {
                "ciphertext": base64.b64encode(stored_ciphertext).decode('utf-8'),
                "nonce": base64.b64encode(stored_nonce).decode('utf-8'),
                "version": entry.encryption_version
            },
            "entry_type": entry.entry_type,
            "created_at": entry.created_at,
            "updated_at": entry.updated_at,
            "encryption_version": entry.encryption_version
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create encrypted dream entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verschlüsselter Traumeintrag konnte nicht erstellt werden"
        )


@router.get("/encrypted", response_model=List[EncryptedDreamEntryResponse])
async def get_encrypted_dream_entries(
    limit: int = Query(50, ge=1, le=100, description="Max number of entries"),
    offset: int = Query(0, ge=0, description="Number of entries to skip"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
) -> List[Dict[str, Any]]:
    """
    Get Encrypted Dream Entries (Zero-Knowledge)

    Returns encrypted dream entries. Client must decrypt them.
    """
    try:
        # Query encrypted entries
        result = await db.execute(
            select(EncryptedDreamEntry)
            .where(
                and_(
                    EncryptedDreamEntry.user_id == uuid.UUID(user_id),
                    EncryptedDreamEntry.is_deleted == False
                )
            )
            .order_by(EncryptedDreamEntry.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        entries = result.scalars().all()

        # Format response
        response = []
        for entry in entries:
            # Extract nonce (last 12 bytes)
            stored_ciphertext = entry.encrypted_data[:-12]
            stored_nonce = entry.encrypted_data[-12:]

            response.append({
                "id": str(entry.id),
                "user_id": str(entry.user_id),
                "encrypted_data": {
                    "ciphertext": base64.b64encode(stored_ciphertext).decode('utf-8'),
                    "nonce": base64.b64encode(stored_nonce).decode('utf-8'),
                    "version": entry.encryption_version
                },
                "entry_type": entry.entry_type,
                "created_at": entry.created_at,
                "updated_at": entry.updated_at,
                "encryption_version": entry.encryption_version
            })

        return response

    except Exception as e:
        logger.error(f"Failed to get encrypted dream entries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verschlüsselte Traumeinträge konnten nicht geladen werden"
        )


@router.get("/encrypted/{entry_id}", response_model=EncryptedDreamEntryResponse)
async def get_encrypted_dream_entry(
    entry_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Get Single Encrypted Dream Entry

    Returns encrypted entry by ID. Client must decrypt.
    """
    try:
        result = await db.execute(
            select(EncryptedDreamEntry)
            .where(
                and_(
                    EncryptedDreamEntry.id == uuid.UUID(entry_id),
                    EncryptedDreamEntry.user_id == uuid.UUID(user_id),
                    EncryptedDreamEntry.is_deleted == False
                )
            )
        )

        entry = result.scalar_one_or_none()

        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Verschlüsselter Traumeintrag nicht gefunden"
            )

        # Extract nonce
        stored_ciphertext = entry.encrypted_data[:-12]
        stored_nonce = entry.encrypted_data[-12:]

        return {
            "id": str(entry.id),
            "user_id": str(entry.user_id),
            "encrypted_data": {
                "ciphertext": base64.b64encode(stored_ciphertext).decode('utf-8'),
                "nonce": base64.b64encode(stored_nonce).decode('utf-8'),
                "version": entry.encryption_version
            },
            "entry_type": entry.entry_type,
            "created_at": entry.created_at,
            "updated_at": entry.updated_at,
            "encryption_version": entry.encryption_version
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get encrypted dream entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verschlüsselter Traumeintrag konnte nicht geladen werden"
        )


@router.delete("/encrypted/{entry_id}", response_model=SuccessResponse)
async def delete_encrypted_dream_entry(
    entry_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Delete Encrypted Dream Entry (Soft Delete)

    Marks entry as deleted (GDPR compliance).
    """
    try:
        result = await db.execute(
            select(EncryptedDreamEntry)
            .where(
                and_(
                    EncryptedDreamEntry.id == uuid.UUID(entry_id),
                    EncryptedDreamEntry.user_id == uuid.UUID(user_id),
                    EncryptedDreamEntry.is_deleted == False
                )
            )
        )

        entry = result.scalar_one_or_none()

        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Verschlüsselter Traumeintrag nicht gefunden"
            )

        # Soft delete
        entry.is_deleted = True
        entry.deleted_at = datetime.utcnow()

        await db.commit()

        logger.info(f"Encrypted dream entry soft-deleted: {entry_id}")

        return {
            "success": True,
            "message": "Verschlüsselter Traumeintrag erfolgreich gelöscht"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete encrypted dream entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verschlüsselter Traumeintrag konnte nicht gelöscht werden"
        )
