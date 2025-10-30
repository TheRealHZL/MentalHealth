"""
Authentication Endpoints for MindBridge

Registrierung und Login für:
- Patienten (mit und ohne Therapeut)
- Therapeuten
- Selbsthilfe-Nutzer ohne professionelle Betreuung
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from src.core.database import get_async_session
from src.core.security import (
    create_access_token, create_refresh_token, verify_token,
    get_password_hash, verify_password, get_current_user_id,
    validate_email, validate_password_strength
)
from src.core.rate_limiting import (
    limiter,
    AUTH_LOGIN_LIMIT,
    AUTH_REGISTER_PATIENT_LIMIT,
    AUTH_REGISTER_THERAPIST_LIMIT,
    AUTH_REFRESH_TOKEN_LIMIT
)
from src.schemas.ai import (
    UserRegistration, UserLogin, UserProfile, UserUpdate,
    TokenResponse, RefreshTokenRequest, SuccessResponse, ErrorResponse
)
from src.models import User, UserRole
from src.services.user_service import UserService, EmailService

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

@router.post("/register", response_model=SuccessResponse)
@limiter.limit(AUTH_REGISTER_PATIENT_LIMIT)  # 5 registrations per hour
async def register_user(
    request: Request,
    user_data: UserRegistration,
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    User Registration
    
    Registriert neue Nutzer:
    - Patienten (mit oder ohne Therapeut)
    - Selbsthilfe-Nutzer
    - Therapeuten (mit Lizenznummer)
    """
    try:
        # Email-Validierung
        if not validate_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ungültiges E-Mail-Format"
            )
        
        # Password-Stärke prüfen
        is_strong, error_msg = validate_password_strength(user_data.password)
        if not is_strong:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Passwort zu schwach: {error_msg}"
            )
        
        # Prüfen ob Email bereits existiert
        user_service = UserService(db)
        existing_user = await user_service.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="E-Mail-Adresse bereits registriert"
            )
        
        # Username prüfen
        existing_username = await user_service.get_user_by_username(user_data.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Benutzername bereits vergeben"
            )
        
        # Therapeuten-spezifische Validierung
        if user_data.role == UserRole.THERAPIST:
            if not user_data.license_number:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Lizenznummer ist für Therapeuten erforderlich"
                )
            
            # Prüfen ob Lizenznummer bereits verwendet wird
            existing_license = await user_service.get_user_by_license(user_data.license_number)
            if existing_license:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Lizenznummer bereits registriert"
                )
        
        # Passwort hashen
        hashed_password = get_password_hash(user_data.password)
        
        # User erstellen
        new_user = await user_service.create_user(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=user_data.role,
            date_of_birth=user_data.date_of_birth,
            license_number=user_data.license_number,
            specialization=user_data.specialization,
            institution=user_data.institution,
            privacy_level=user_data.privacy_level
        )
        
        # Welcome Email senden (für alle Nutzertypen)
        email_service = EmailService()
        
        if user_data.role == UserRole.PATIENT:
            # Spezielle Willkommens-Email für Patienten
            await email_service.send_patient_welcome_email(
                email=new_user.email,
                first_name=new_user.first_name,
                has_therapist=False  # Kann später geändert werden
            )
        elif user_data.role == UserRole.THERAPIST:
            # Therapeuten-Willkommens-Email
            await email_service.send_therapist_welcome_email(
                email=new_user.email,
                first_name=new_user.first_name,
                license_number=new_user.license_number
            )
        
        logger.info(f"New user registered: {new_user.email} ({new_user.role.value})")
        
        return {
            "success": True,
            "message": "Registrierung erfolgreich! Bitte bestätigen Sie Ihre E-Mail-Adresse.",
            "data": {
                "user_id": str(new_user.id),
                "email": new_user.email,
                "role": new_user.role.value,
                "requires_email_verification": True,
                "welcome_message": _get_welcome_message(new_user.role)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registrierung fehlgeschlagen"
        )

@router.post("/login", response_model=TokenResponse)
@limiter.limit(AUTH_LOGIN_LIMIT)  # 10 login attempts per minute
async def login_user(
    request: Request,
    login_data: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    User Login
    
    Anmeldung für alle Nutzertypen.
    """
    try:
        user_service = UserService(db)
        
        # User finden
        user = await user_service.get_user_by_email(login_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Ungültige Anmeldedaten"
            )
        
        # Passwort prüfen
        if not verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Ungültige Anmeldedaten"
            )
        
        # Account-Status prüfen
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account ist deaktiviert"
            )
        
        # Tokens erstellen
        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))

        # Login-Zeit aktualisieren
        await user_service.update_last_login(user.id)

        # Session erstellen (optional für Tracking)
        ip_address = request.client.host
        user_agent = request.headers.get("user-agent", "")
        await user_service.create_session(
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent
        )

        # Set secure httpOnly cookies for tokens (XSS Protection!)
        # Access token - short lived
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,  # JavaScript can't access (XSS protection!)
            secure=request.url.scheme == "https",  # Only over HTTPS in production
            samesite="strict",  # CSRF protection
            max_age=30 * 60,  # 30 minutes
            path="/"
        )

        # Refresh token - longer lived, more secure
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,  # JavaScript can't access
            secure=request.url.scheme == "https",  # Only HTTPS
            samesite="strict",  # Strict CSRF protection
            max_age=7 * 24 * 60 * 60,  # 7 days
            path="/api/v1/auth"  # Only sent to auth endpoints
        )

        logger.info(f"✅ User logged in: {user.email} (Tokens in httpOnly cookies)")

        # Return user info (tokens are in cookies now!)
        return {
            "success": True,
            "message": "Login successful",
            "user_id": str(user.id),
            "role": user.role,
            "token_type": "cookie",  # Indicate tokens are in cookies
            "expires_in": 30 * 60  # Access token expiry
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Anmeldung fehlgeschlagen"
        )

@router.post("/refresh", response_model=TokenResponse)
@limiter.limit(AUTH_REFRESH_TOKEN_LIMIT)  # 20 token refreshes per hour
async def refresh_token(
    request: Request,
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Refresh Access Token
    """
    try:
        # Refresh Token validieren
        user_id = verify_token(refresh_data.refresh_token, "refresh")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Ungültiger Refresh Token"
            )
        
        # User existiert noch?
        user_service = UserService(db)
        user = await user_service.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User nicht gefunden oder deaktiviert"
            )
        
        # Neue Tokens erstellen
        new_access_token = create_access_token(subject=user_id)
        new_refresh_token = create_refresh_token(subject=user_id)
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": 30 * 60,
            "user_id": user_id,
            "role": user.role
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token-Erneuerung fehlgeschlagen"
        )

@router.get("/profile", response_model=UserProfile)
async def get_user_profile(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Get User Profile
    
    Gibt das vollständige Benutzerprofil zurück.
    """
    try:
        user_service = UserService(db)
        user = await user_service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User nicht gefunden"
            )
        
        # Statistiken abrufen
        stats = await user_service.get_user_statistics(user_id)
        
        return {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "date_of_birth": user.date_of_birth,
            "is_active": user.is_active,
            "license_number": user.license_number,
            "specialization": user.specialization,
            "institution": user.institution,
            "total_mood_entries": stats.get("mood_entries", 0),
            "total_dream_entries": stats.get("dream_entries", 0),
            "total_therapy_notes": stats.get("therapy_notes", 0),
            "created_at": user.created_at,
            "last_login": user.last_login
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get profile failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profil konnte nicht geladen werden"
        )

@router.put("/profile", response_model=SuccessResponse)
async def update_user_profile(
    update_data: UserUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Update User Profile
    """
    try:
        user_service = UserService(db)
        
        # User existiert?
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User nicht gefunden"
            )
        
        # Profile aktualisieren
        updated_user = await user_service.update_user_profile(
            user_id=user_id,
            update_data=update_data.dict(exclude_unset=True)
        )
        
        return {
            "success": True,
            "message": "Profil erfolgreich aktualisiert",
            "data": {
                "user_id": str(updated_user.id),
                "updated_fields": list(update_data.dict(exclude_unset=True).keys())
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profil-Aktualisierung fehlgeschlagen"
        )

@router.post("/logout", response_model=SuccessResponse)
async def logout_user(
    response: Response,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    User Logout
    
    Beendet die Session und invalidiert Tokens.
    """
    try:
        user_service = UserService(db)
        
        # Session beenden
        await user_service.end_user_sessions(user_id)

        # Delete both httpOnly cookies (complete logout)
        response.delete_cookie(
            key="access_token",
            path="/"
        )
        response.delete_cookie(
            key="refresh_token",
            path="/api/v1/auth"
        )

        logger.info(f"✅ User logged out: {user_id} (Cookies cleared)")

        return {
            "success": True,
            "message": "Erfolgreich abgemeldet"
        }
        
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        # Logout sollte auch bei Fehlern erfolgreich sein
        return {
            "success": True,
            "message": "Abmeldung abgeschlossen"
        }

@router.get("/me/dashboard", response_model=Dict[str, Any])
async def get_user_dashboard(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    User Dashboard
    
    Gibt Dashboard-Daten für den eingeloggten Nutzer zurück.
    Funktioniert für alle Nutzertypen (mit/ohne Therapeut).
    """
    try:
        user_service = UserService(db)
        
        # User Info
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User nicht gefunden"
            )
        
        # Dashboard-Daten basierend auf Nutzertyp
        if user.role == UserRole.PATIENT:
            dashboard_data = await _get_patient_dashboard(user_id, user_service)
        elif user.role == UserRole.THERAPIST:
            dashboard_data = await _get_therapist_dashboard(user_id, user_service)
        else:
            dashboard_data = await _get_basic_dashboard(user_id, user_service)
        
        return {
            "success": True,
            "data": {
                "user_type": user.role.value,
                "welcome_message": _get_dashboard_welcome_message(user),
                **dashboard_data
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dashboard failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Dashboard konnte nicht geladen werden"
        )

# =============================================================================
# Helper Functions
# =============================================================================

def _get_welcome_message(role: UserRole) -> str:
    """Willkommensnachricht basierend auf Rolle"""
    if role == UserRole.PATIENT:
        return (
            "Willkommen bei MindBridge! 🌟\n\n"
            "Du kannst jetzt dein digitales Stimmungstagebuch führen, "
            "Träume dokumentieren und Therapie-Notizen erstellen. "
            "Unsere KI unterstützt dich dabei mit wertvollen Insights.\n\n"
            "💡 Tipp: Du kannst die Plattform auch ohne Therapeut nutzen - "
            "alle Tools stehen dir zur Selbsthilfe zur Verfügung!"
        )
    elif role == UserRole.THERAPIST:
        return (
            "Willkommen bei MindBridge für Therapeuten! 👩‍⚕️\n\n"
            "Sie können jetzt Patienten dabei unterstützen, ihre mentale Gesundheit "
            "zu verfolgen und zu verbessern. Mit Share-Keys erhalten Sie "
            "kontrollierten Zugang zu Patientendaten."
        )
    else:
        return "Willkommen bei MindBridge! Beginnen Sie Ihre Reise zu besserer mentaler Gesundheit."

def _get_dashboard_welcome_message(user: User) -> str:
    """Dashboard-Willkommensnachricht"""
    current_hour = datetime.now().hour
    
    if current_hour < 12:
        greeting = "Guten Morgen"
    elif current_hour < 18:
        greeting = "Guten Tag"
    else:
        greeting = "Guten Abend"
    
    if user.role == UserRole.PATIENT:
        return f"{greeting}, {user.first_name}! Wie geht es dir heute? 🌱"
    elif user.role == UserRole.THERAPIST:
        return f"{greeting}, {user.first_name}! Hier ist deine Patienten-Übersicht."
    else:
        return f"{greeting}, {user.first_name}!"

async def _get_patient_dashboard(user_id: str, user_service: UserService) -> Dict[str, Any]:
    """Dashboard für Patienten (mit oder ohne Therapeut)"""
    
    # Aktuelle Statistiken
    stats = await user_service.get_user_statistics(user_id)
    recent_mood = await user_service.get_recent_mood_trend(user_id, days=7)
    
    # Selbsthilfe-Tools und -Ressourcen
    suggestions = _get_self_help_suggestions(recent_mood)
    
    return {
        "current_mood_trend": recent_mood,
        "entries_this_week": stats.get("entries_this_week", 0),
        "total_entries": stats.get("total_entries", 0),
        "streak_days": stats.get("consecutive_days", 0),
        "self_help_suggestions": suggestions,
        "quick_actions": [
            "Stimmung eintragen",
            "Traum dokumentieren", 
            "Notiz schreiben",
            "KI-Chat starten"
        ],
        "achievements": await user_service.get_user_achievements(user_id),
        "has_therapist_access": await user_service.has_active_therapist_sharing(user_id)
    }

async def _get_therapist_dashboard(user_id: str, user_service: UserService) -> Dict[str, Any]:
    """Dashboard für Therapeuten"""
    
    # Patienten-Übersicht
    active_patients = await user_service.get_therapist_patients(user_id)
    
    return {
        "total_patients": len(active_patients),
        "active_share_keys": await user_service.count_active_share_keys(user_id),
        "recent_patient_activity": await user_service.get_recent_patient_activity(user_id),
        "patients_needing_attention": await user_service.get_patients_needing_attention(user_id),
        "quick_actions": [
            "Patienten-Übersicht",
            "Neue Share-Keys",
            "Fortschritte analysieren"
        ]
    }

async def _get_basic_dashboard(user_id: str, user_service: UserService) -> Dict[str, Any]:
    """Basis-Dashboard für andere Nutzertypen"""
    
    stats = await user_service.get_user_statistics(user_id)
    
    return {
        "total_entries": stats.get("total_entries", 0),
        "entries_this_week": stats.get("entries_this_week", 0),
        "quick_actions": [
            "Daten eintragen",
            "Verlauf ansehen"
        ]
    }

def _get_self_help_suggestions(mood_trend: Dict[str, Any]) -> List[str]:
    """Selbsthilfe-Vorschläge basierend auf Stimmungstrend"""
    
    current_mood = mood_trend.get("current_average", 5)
    trend = mood_trend.get("trend", "stable")
    
    suggestions = []
    
    if current_mood < 4:
        suggestions.extend([
            "🧘 Probiere eine 5-minütige Atemübung",
            "🚶 Ein kurzer Spaziergang kann helfen",
            "📱 Nutze unseren KI-Chat für Unterstützung"
        ])
    
    if trend == "declining":
        suggestions.extend([
            "📝 Schreibe deine Gedanken auf",
            "💪 Setze dir ein kleines, erreichbares Ziel",
            "🤝 Erreiche eine Vertrauensperson"
        ])
    elif trend == "improving":
        suggestions.extend([
            "🎉 Feiere deine Fortschritte!",
            "💡 Reflektiere, was gut läuft",
            "📈 Bleibe bei deinen gesunden Gewohnheiten"
        ])
    
    # Standard-Selbsthilfe-Tipps
    if not suggestions:
        suggestions = [
            "📊 Tracke deine Stimmung regelmäßig",
            "🌱 Entwickle eine Abendroutine",
            "🎯 Setze dir realistische Tagesziele"
        ]
    
    return suggestions[:3]  # Maximal 3 Vorschläge
