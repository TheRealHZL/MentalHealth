"""
User Management Endpoints

Benutzer-Registrierung, Profile und Rollen-Management.
Getrennte Workflows für Patienten und Therapeuten.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import (APIRouter, Depends, File, HTTPException, Query, Request,
                     UploadFile, status)
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_session
from src.core.security import (create_access_token,
                               create_rate_limit_dependency,
                               get_current_user_id, hash_password,
                               verify_password)
from src.schemas.ai import (PasswordChange, SuccessResponse,
                            TherapistRegistration, TherapistVerification,
                            TokenResponse, UserLogin, UserProfileResponse,
                            UserProfileUpdate, UserRegistration)
from src.services.email_service import EmailService
from src.services.user_service import UserService

logger = logging.getLogger(__name__)

router = APIRouter()

# Rate limiting
auth_rate_limit = create_rate_limit_dependency(limit=5, window_minutes=15)
general_rate_limit = create_rate_limit_dependency(limit=30, window_minutes=60)


@router.post("/register/patient", response_model=TokenResponse)
async def register_patient(
    user_data: UserRegistration,
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    _rate_limit=Depends(auth_rate_limit),
) -> Dict[str, Any]:
    """
    Register Patient

    Einfache Registrierung für Patienten - sofort nutzbar.
    """
    try:
        user_service = UserService(db)

        # Prüfen ob Email bereits existiert
        existing_user = await user_service.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email bereits registriert",
            )

        # Patient erstellen
        user = await user_service.create_patient(
            email=user_data.email,
            password=user_data.password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            date_of_birth=user_data.date_of_birth,
            timezone=user_data.timezone or "Europe/Berlin",
        )

        # Willkommens-Email senden
        email_service = EmailService()
        await email_service.send_welcome_email(
            to_email=user.email, first_name=user.first_name
        )

        # Access Token erstellen
        access_token = create_access_token(
            data={"sub": str(user.id), "role": "patient"}
        )

        logger.info(f"Patient registered: {user.email}")

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "is_verified": user.is_verified,
            },
            "message": "Registrierung erfolgreich! Du kannst sofort loslegen.",
            "next_steps": [
                "📝 Erstelle deinen ersten Stimmungseintrag",
                "🌙 Beginne ein Traumtagebuch",
                "💭 Nutze Selbstreflexions-Tools",
                "👨‍⚕️ Optional: Lade später einen Therapeuten ein",
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Patient registration failed: {e}", exc_info=True)
        # In development, return detailed error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registrierung fehlgeschlagen: {str(e)}",
        )


@router.post("/register/therapist", response_model=SuccessResponse)
async def register_therapist(
    therapist_data: TherapistRegistration,
    license_file: UploadFile = File(..., description="Therapielizenz PDF"),
    db: AsyncSession = Depends(get_async_session),
    _rate_limit=Depends(auth_rate_limit),
) -> Dict[str, Any]:
    """
    Register Therapist

    Therapeuten-Registrierung mit Lizenz-Verifizierung.
    Account wird erst nach Verifizierung aktiviert.
    """
    try:
        user_service = UserService(db)

        # Prüfen ob Email bereits existiert
        existing_user = await user_service.get_user_by_email(therapist_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email bereits registriert",
            )

        # Lizenz-Datei validieren
        if not license_file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lizenz muss als PDF hochgeladen werden",
            )

        # Lizenz-Datei speichern
        license_content = await license_file.read()
        license_filename = await user_service.save_license_file(
            email=therapist_data.email,
            filename=license_file.filename,
            content=license_content,
        )

        # Therapeut erstellen (zunächst unverifiziert)
        therapist = await user_service.create_therapist(
            email=therapist_data.email,
            password=therapist_data.password,
            first_name=therapist_data.first_name,
            last_name=therapist_data.last_name,
            license_number=therapist_data.license_number,
            specializations=therapist_data.specializations,
            practice_address=therapist_data.practice_address,
            phone_number=therapist_data.phone_number,
            bio=therapist_data.bio,
            license_filename=license_filename,
        )

        # Admin-Benachrichtigung für Verifizierung
        await user_service.notify_admin_for_verification(therapist.id)

        # Bestätigungs-Email an Therapeut
        email_service = EmailService()
        await email_service.send_therapist_registration_confirmation(
            to_email=therapist.email, first_name=therapist.first_name
        )

        logger.info(f"Therapist registration submitted: {therapist.email}")

        return {
            "success": True,
            "message": "Therapeuten-Registrierung eingereicht",
            "data": {
                "status": "pending_verification",
                "estimated_verification_time": "1-3 Werktage",
                "next_steps": [
                    "📧 Du erhältst eine Email sobald dein Account verifiziert ist",
                    "📋 Unsere Fachkräfte prüfen deine Lizenz",
                    "✅ Nach Freigabe kannst du dich einloggen",
                    "👥 Dann können dir Patienten Zugang gewähren",
                ],
                "contact_support": "Bei Fragen: support@mindbridge.app",
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Therapist registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Therapeuten-Registrierung fehlgeschlagen",
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_async_session),
    _rate_limit=Depends(auth_rate_limit),
) -> Dict[str, Any]:
    """
    User Login

    Login für Patienten und verifizierte Therapeuten.
    """
    try:
        user_service = UserService(db)

        # User finden
        user = await user_service.get_user_by_email(login_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Ungültige Anmeldedaten",
            )

        # Passwort prüfen
        if not verify_password(login_data.password, user.password_hash):
            # Login-Versuch loggen
            await user_service.log_failed_login(str(user.id), login_data.email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Ungültige Anmeldedaten",
            )

        # Account-Status prüfen
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Account ist deaktiviert"
            )

        # Therapeuten müssen verifiziert sein
        if user.role == "therapist" and not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Therapeuten-Account noch nicht verifiziert. Bitte warte auf die Freigabe.",
            )

        # Letzten Login aktualisieren
        await user_service.update_last_login(str(user.id))

        # Access Token erstellen
        access_token = create_access_token(
            data={"sub": str(user.id), "role": user.role}
        )

        logger.info(f"User logged in: {user.email} ({user.role})")

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "is_verified": user.is_verified,
                "last_login": user.last_login,
            },
            "message": f"Willkommen zurück, {user.first_name}!",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Anmeldung fehlgeschlagen",
        )


@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Get User Profile
    """
    try:
        user_service = UserService(db)

        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Benutzer nicht gefunden"
            )

        # Profil-Statistiken holen
        profile_stats = await user_service.get_profile_statistics(user_id)

        profile_data = {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "is_verified": user.is_verified,
            "timezone": user.timezone,
            "created_at": user.created_at,
            "last_login": user.last_login,
            "statistics": profile_stats,
        }

        # Therapeuten-spezifische Daten
        if user.role == "therapist":
            profile_data.update(
                {
                    "license_number": user.license_number,
                    "specializations": user.specializations,
                    "practice_address": user.practice_address,
                    "phone_number": user.phone_number,
                    "bio": user.bio,
                    "verification_status": (
                        "verified" if user.is_verified else "pending"
                    ),
                }
            )

        return profile_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profil konnte nicht geladen werden",
        )


@router.put("/profile", response_model=UserProfileResponse)
async def update_profile(
    profile_data: UserProfileUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
    _rate_limit=Depends(general_rate_limit),
) -> Dict[str, Any]:
    """
    Update User Profile
    """
    try:
        user_service = UserService(db)

        # User finden
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Benutzer nicht gefunden"
            )

        # Profil aktualisieren
        updated_user = await user_service.update_user_profile(
            user_id=user_id, profile_data=profile_data
        )

        logger.info(f"Profile updated: {user.email}")

        # Aktualisiertes Profil zurückgeben
        return await get_profile(user_id, db)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profil konnte nicht aktualisiert werden",
        )


@router.post("/change-password", response_model=SuccessResponse)
async def change_password(
    password_data: PasswordChange,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
    _rate_limit=Depends(auth_rate_limit),
) -> Dict[str, Any]:
    """
    Change Password
    """
    try:
        user_service = UserService(db)

        # User finden
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Benutzer nicht gefunden"
            )

        # Aktuelles Passwort prüfen
        if not verify_password(password_data.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Aktuelles Passwort ist falsch",
            )

        # Neues Passwort setzen
        await user_service.update_password(user_id, password_data.new_password)

        logger.info(f"Password changed: {user.email}")

        return {
            "success": True,
            "message": "Passwort erfolgreich geändert",
            "data": {
                "changed_at": datetime.utcnow(),
                "security_tip": "Verwende ein starkes, einzigartiges Passwort",
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to change password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Passwort konnte nicht geändert werden",
        )


@router.post("/delete-account", response_model=SuccessResponse)
async def delete_account(
    confirmation: str = Query(..., description="Muss 'ACCOUNT_LÖSCHEN' sein"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Delete User Account

    Vollständige Löschung des Accounts und aller Daten.
    """
    try:
        if confirmation != "ACCOUNT_LÖSCHEN":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bestätigung erforderlich: 'ACCOUNT_LÖSCHEN'",
            )

        user_service = UserService(db)

        # User finden
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Benutzer nicht gefunden"
            )

        # Account und alle Daten löschen
        deletion_summary = await user_service.delete_user_account(user_id)

        logger.warning(f"Account deleted: {user.email}")

        return {
            "success": True,
            "message": "Account erfolgreich gelöscht",
            "data": {
                "deleted_at": datetime.utcnow(),
                "deletion_summary": deletion_summary,
                "note": "Alle deine Daten wurden vollständig und unwiderruflich gelöscht",
                "gdpr_compliance": "Löschung erfolgte DSGVO-konform",
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Account-Löschung fehlgeschlagen",
        )


@router.get("/therapists/search")
async def search_therapists(
    location: Optional[str] = Query(None, description="Stadt oder PLZ"),
    specialization: Optional[str] = Query(None, description="Spezialisierung"),
    radius: int = Query(50, ge=5, le=200, description="Suchradius in km"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Search Therapists

    Patienten können nach verifizierten Therapeuten suchen.
    """
    try:
        user_service = UserService(db)

        # Nur Patienten dürfen Therapeuten suchen
        user = await user_service.get_user_by_id(user_id)
        if user.role != "patient":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nur Patienten können nach Therapeuten suchen",
            )

        # Therapeuten suchen
        therapists = await user_service.search_verified_therapists(
            location=location, specialization=specialization, radius=radius
        )

        return {
            "success": True,
            "data": {
                "therapists": therapists,
                "search_params": {
                    "location": location,
                    "specialization": specialization,
                    "radius": radius,
                },
                "total_found": len(therapists),
                "note": "Alle angezeigten Therapeuten sind von MindBridge verifiziert",
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Therapist search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Therapeuten-Suche fehlgeschlagen",
        )


@router.get("/account/export")
async def export_account_data(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Export Account Data (GDPR)

    Vollständiger Daten-Export für DSGVO-Compliance.
    """
    try:
        user_service = UserService(db)

        # Alle Benutzerdaten exportieren
        export_data = await user_service.export_user_data(user_id)

        logger.info(f"Data export requested: {user_id}")

        return {
            "success": True,
            "data": export_data,
            "export_info": {
                "generated_at": datetime.utcnow(),
                "data_format": "JSON",
                "gdpr_compliant": True,
                "includes": [
                    "Profildaten",
                    "Stimmungseinträge",
                    "Traumtagebuch",
                    "Therapie-Notizen",
                    "Geteilte Daten",
                    "Account-Aktivitäten",
                ],
            },
        }

    except Exception as e:
        logger.error(f"Data export failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Daten-Export fehlgeschlagen",
        )


@router.get("/statistics/platform")
async def get_platform_statistics(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Platform Statistics

    Anonyme Plattform-Statistiken (ohne persönliche Daten).
    """
    try:
        user_service = UserService(db)

        # Anonyme Plattform-Stats
        platform_stats = await user_service.get_platform_statistics()

        return {
            "success": True,
            "data": platform_stats,
            "note": "Alle Statistiken sind vollständig anonymisiert",
        }

    except Exception as e:
        logger.error(f"Platform statistics failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Plattform-Statistiken konnten nicht geladen werden",
        )
