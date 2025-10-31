"""
Sharing & Therapist Access Endpoints

Optionale Therapeuten-Integration mit granularer Kontrolle.
Patienten entscheiden vollständig, was geteilt wird.
"""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_session
from src.core.security import create_rate_limit_dependency, get_current_user_id
from src.schemas.ai import (PaginatedResponse, PaginationParams,
                            PatientOverview, ShareKeyCreate, ShareKeyResponse,
                            SuccessResponse, TherapistAccessRequest)
from src.services.sharing_service import SharingService
from src.services.user_service import UserService

logger = logging.getLogger(__name__)

router = APIRouter()

# Rate limiting
sharing_rate_limit = create_rate_limit_dependency(limit=10, window_minutes=60)


@router.post("/create-share-key", response_model=ShareKeyResponse)
async def create_share_key(
    share_data: ShareKeyCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
    _rate_limit=Depends(sharing_rate_limit),
) -> Dict[str, Any]:
    """
    Create Share Key for Therapist

    Patient erstellt einen sicheren Zugangsschlüssel für Therapeuten.
    Vollständige Kontrolle über was geteilt wird.
    """
    try:
        sharing_service = SharingService(db)
        user_service = UserService(db)

        # Prüfen ob User existiert
        patient = await user_service.get_user_by_id(user_id)
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Patient nicht gefunden"
            )

        # Prüfen ob Therapeut-Email existiert
        therapist = await user_service.get_user_by_email(share_data.therapist_email)
        if not therapist:
            # Therapist noch nicht registriert - das ist OK, Key wird später aktiviert
            logger.info(
                f"Share key created for unregistered therapist: {share_data.therapist_email}"
            )
        elif therapist.role.value != "therapist":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email gehört nicht zu einem registrierten Therapeuten",
            )

        # Share Key erstellen
        share_key = await sharing_service.create_share_key(
            patient_id=user_id,
            therapist_email=share_data.therapist_email,
            permission_level=share_data.permission_level,
            include_mood_entries=share_data.include_mood_entries,
            include_dream_entries=share_data.include_dream_entries,
            include_therapy_notes=share_data.include_therapy_notes,
            expires_at=share_data.expires_at,
            max_sessions=share_data.max_sessions,
            notes=share_data.notes,
        )

        logger.info(
            f"Share key created by patient {user_id} for therapist {share_data.therapist_email}"
        )

        return {
            **share_key.__dict__,
            "instructions": {
                "for_patient": [
                    f"Teile diesen Schlüssel mit deinem Therapeuten: {share_key.share_key}",
                    "Du kannst den Zugang jederzeit widerrufen",
                    "Du siehst alle Zugriffe in deinem Dashboard",
                ],
                "for_therapist": [
                    "Therapeut muss sich zuerst bei MindBridge registrieren",
                    "Dann den Share-Key in seinem Dashboard eingeben",
                    "Zugriff ist auf die gewählten Bereiche beschränkt",
                ],
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create share key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Share-Key konnte nicht erstellt werden",
        )


@router.post("/accept-share-key", response_model=SuccessResponse)
async def accept_share_key(
    access_request: TherapistAccessRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
    _rate_limit=Depends(sharing_rate_limit),
) -> Dict[str, Any]:
    """
    Accept Share Key (Therapist)

    Therapeut akzeptiert einen Share-Key von einem Patienten.
    """
    try:
        sharing_service = SharingService(db)
        user_service = UserService(db)

        # Prüfen ob User ein Therapeut ist
        therapist = await user_service.get_user_by_id(user_id)
        if not therapist or therapist.role.value != "therapist":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nur registrierte Therapeuten können Share-Keys akzeptieren",
            )

        # Share Key validieren und akzeptieren
        share_key = await sharing_service.accept_share_key(
            share_key=access_request.share_key,
            therapist_id=user_id,
            therapist_email=therapist.email,
            message=access_request.message,
        )

        # Patient über Akzeptierung informieren (optional)
        await sharing_service.notify_patient_of_acceptance(
            share_key_id=share_key.id,
            therapist_name=f"{therapist.first_name} {therapist.last_name}",
            message=access_request.message,
        )

        logger.info(
            f"Share key accepted by therapist {user_id}: {access_request.share_key[:8]}..."
        )

        return {
            "success": True,
            "message": f"Zugang zu Patient-Daten erfolgreich eingerichtet",
            "data": {
                "patient_name": share_key.patient.first_name,  # Nur Vorname für Privacy
                "permission_level": share_key.permission_level.value,
                "access_areas": {
                    "mood_entries": share_key.include_mood_entries,
                    "dream_entries": share_key.include_dream_entries,
                    "therapy_notes": share_key.include_therapy_notes,
                },
                "expires_at": share_key.expires_at,
                "max_sessions": share_key.max_sessions,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to accept share key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Share-Key konnte nicht akzeptiert werden",
        )


@router.get("/my-share-keys", response_model=PaginatedResponse)
async def get_my_share_keys(
    pagination: PaginationParams = Depends(),
    status_filter: Optional[str] = Query(None, description="active, inactive, expired"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Get My Share Keys (Patient View)

    Patient sieht alle seine Share-Keys und deren Status.
    """
    try:
        sharing_service = SharingService(db)

        # Share Keys des Patienten holen
        share_keys, total_count = await sharing_service.get_patient_share_keys(
            patient_id=user_id, pagination=pagination, status_filter=status_filter
        )

        # Pagination berechnen
        total_pages = (total_count + pagination.page_size - 1) // pagination.page_size
        has_next = pagination.page < total_pages
        has_prev = pagination.page > 1

        return {
            "items": share_keys,
            "total": total_count,
            "page": pagination.page,
            "page_size": pagination.page_size,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_prev": has_prev,
        }

    except Exception as e:
        logger.error(f"Failed to get share keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Share-Keys konnten nicht geladen werden",
        )


@router.get("/my-patients", response_model=List[PatientOverview])
async def get_my_patients(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
) -> List[Dict[str, Any]]:
    """
    Get My Patients (Therapist View)

    Therapeut sieht Übersicht seiner Patienten.
    """
    try:
        sharing_service = SharingService(db)
        user_service = UserService(db)

        # Prüfen ob User ein Therapeut ist
        therapist = await user_service.get_user_by_id(user_id)
        if not therapist or therapist.role.value != "therapist":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nur Therapeuten können Patienten-Übersicht einsehen",
            )

        # Patienten des Therapeuten holen
        patients = await sharing_service.get_therapist_patients(user_id)

        return patients

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get patients: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Patienten-Übersicht konnte nicht geladen werden",
        )


@router.put("/share-key/{share_key_id}/revoke", response_model=SuccessResponse)
async def revoke_share_key(
    share_key_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Revoke Share Key (Patient)

    Patient kann jederzeit den Therapeuten-Zugang widerrufen.
    """
    try:
        sharing_service = SharingService(db)

        # Share Key widerrufen
        revoked_key = await sharing_service.revoke_share_key(
            share_key_id=share_key_id, patient_id=user_id
        )

        if not revoked_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Share-Key nicht gefunden oder bereits widerrufen",
            )

        # Therapeut über Widerruf informieren
        await sharing_service.notify_therapist_of_revocation(
            share_key_id=share_key_id, patient_name=revoked_key.patient.first_name
        )

        logger.info(f"Share key revoked by patient {user_id}: {share_key_id}")

        return {
            "success": True,
            "message": "Therapeuten-Zugang erfolgreich widerrufen",
            "data": {
                "revoked_at": datetime.utcnow(),
                "therapist_email": revoked_key.therapist_email,
                "note": "Der Therapeut wurde über den Widerruf informiert",
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to revoke share key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Share-Key konnte nicht widerrufen werden",
        )


@router.get("/patient/{patient_id}/data")
async def get_patient_data(
    patient_id: str,
    data_type: str = Query(..., description="mood, dreams, therapy_notes"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Get Patient Data (Therapist Access)

    Therapeut kann freigegebene Patientendaten einsehen.
    """
    try:
        sharing_service = SharingService(db)
        user_service = UserService(db)

        # Prüfen ob User ein Therapeut ist
        therapist = await user_service.get_user_by_id(user_id)
        if not therapist or therapist.role.value != "therapist":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nur Therapeuten können Patientendaten einsehen",
            )

        # Prüfen ob Zugriff berechtigt ist
        has_access = await sharing_service.verify_therapist_access(
            therapist_id=user_id, patient_id=patient_id, data_type=data_type
        )

        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Kein Zugriff auf diese Patientendaten",
            )

        # Patientendaten holen (anonymisiert)
        patient_data = await sharing_service.get_patient_data_for_therapist(
            patient_id=patient_id,
            data_type=data_type,
            start_date=start_date,
            end_date=end_date,
            therapist_id=user_id,  # Für Logging
        )

        return {
            "success": True,
            "data": patient_data,
            "privacy_note": "Daten sind anonymisiert und DSGVO-konform übertragen",
            "access_logged": True,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get patient data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Patientendaten konnten nicht geladen werden",
        )


@router.get("/access-logs/{share_key_id}")
async def get_access_logs(
    share_key_id: str,
    pagination: PaginationParams = Depends(),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Get Access Logs (Patient View)

    Patient kann alle Zugriffe des Therapeuten einsehen.
    """
    try:
        sharing_service = SharingService(db)

        # Prüfen ob Share Key dem Patienten gehört
        share_key = await sharing_service.get_share_key_by_id(share_key_id, user_id)
        if not share_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Share-Key nicht gefunden"
            )

        # Access Logs holen
        logs, total_count = await sharing_service.get_access_logs(
            share_key_id=share_key_id, pagination=pagination
        )

        # Pagination berechnen
        total_pages = (total_count + pagination.page_size - 1) // pagination.page_size
        has_next = pagination.page < total_pages
        has_prev = pagination.page > 1

        return {
            "items": logs,
            "total": total_count,
            "page": pagination.page,
            "page_size": pagination.page_size,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_prev": has_prev,
            "summary": {
                "total_accesses": share_key.access_count,
                "last_access": share_key.last_accessed,
                "therapist_name": (
                    f"Dr. {share_key.therapist.last_name}"
                    if share_key.therapist
                    else "Unbekannt"
                ),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get access logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Zugriffs-Logs konnten nicht geladen werden",
        )


@router.post("/emergency-revoke-all", response_model=SuccessResponse)
async def emergency_revoke_all(
    confirmation: str = Query(..., description="Muss 'ALLE_WIDERRUFEN' sein"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Emergency: Revoke All Share Keys

    Patient kann im Notfall alle Therapeuten-Zugriffe sofort widerrufen.
    """
    try:
        if confirmation != "ALLE_WIDERRUFEN":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bestätigung erforderlich: 'ALLE_WIDERRUFEN'",
            )

        sharing_service = SharingService(db)

        # Alle aktiven Share Keys widerrufen
        revoked_count = await sharing_service.emergency_revoke_all_share_keys(user_id)

        logger.warning(
            f"EMERGENCY: Patient {user_id} revoked ALL share keys ({revoked_count} keys)"
        )

        return {
            "success": True,
            "message": f"Alle {revoked_count} Therapeuten-Zugriffe wurden sofort widerrufen",
            "data": {
                "revoked_count": revoked_count,
                "revoked_at": datetime.utcnow(),
                "security_note": "Alle Therapeuten wurden über den Widerruf informiert",
                "next_steps": [
                    "Du kannst jederzeit neue Share-Keys erstellen",
                    "Kontaktiere bei Bedarf unseren Support",
                    "Deine Daten bleiben vollständig geschützt",
                ],
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed emergency revoke: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Notfall-Widerruf fehlgeschlagen",
        )


@router.get("/sharing-statistics")
async def get_sharing_statistics(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Get Sharing Statistics

    Übersicht über alle Sharing-Aktivitäten.
    """
    try:
        sharing_service = SharingService(db)
        user_service = UserService(db)

        user = await user_service.get_user_by_id(user_id)

        if user.role.value == "patient":
            # Patient Statistics
            stats = await sharing_service.get_patient_sharing_stats(user_id)
        elif user.role.value == "therapist":
            # Therapist Statistics
            stats = await sharing_service.get_therapist_sharing_stats(user_id)
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sharing-Statistiken nur für Patienten und Therapeuten",
            )

        return {"success": True, "data": stats, "user_role": user.role.value}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get sharing statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sharing-Statistiken konnten nicht geladen werden",
        )
