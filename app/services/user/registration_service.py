"""
User Registration Service

Zuständig für Patient- und Therapeuten-Registrierung.
"""

import hashlib
import logging
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models import User, UserRole

logger = logging.getLogger(__name__)


class RegistrationService:
    """User Registration Service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_patient(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        date_of_birth: Optional[date] = None,
        timezone: str = "Europe/Berlin",
    ) -> User:
        """Create new patient account - immediately active"""

        password_hash = hash_password(password)

        patient = User(
            email=email.lower(),
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            role=UserRole.PATIENT.value,  # FIX: Use .value to get string
            date_of_birth=date_of_birth,
            timezone=timezone,
            is_active=True,
            is_verified=True,  # Patients are immediately verified
            email_verified=True,
            registration_completed=True,
        )

        self.db.add(patient)
        await self.db.commit()
        await self.db.refresh(patient)

        logger.info(f"Patient created: {email}")
        return patient

    async def create_therapist(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        license_number: str,
        specializations: List[str],
        practice_address: Optional[str] = None,
        phone_number: Optional[str] = None,
        bio: Optional[str] = None,
        license_filename: Optional[str] = None,
    ) -> User:
        """Create new therapist account - requires verification"""

        password_hash = hash_password(password)

        therapist = User(
            email=email.lower(),
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            role=UserRole.THERAPIST.value,  # FIX: Use .value to get string
            timezone="Europe/Berlin",
            is_active=True,
            is_verified=False,  # Therapists need manual verification
            email_verified=True,
            registration_completed=True,
            license_number=license_number,
            specializations=specializations,
            practice_address=practice_address,
            phone_number=phone_number,
            bio=bio,
            license_file_path=license_filename,
        )

        self.db.add(therapist)
        await self.db.commit()
        await self.db.refresh(therapist)

        logger.info(f"Therapist created (pending verification): {email}")
        return therapist

    async def save_license_file(self, email: str, filename: str, content: bytes) -> str:
        """Save therapist license file securely"""

        # Create secure filename
        email_hash = hashlib.md5(email.encode()).hexdigest()[:8]
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_extension = Path(filename).suffix

        secure_filename = f"license_{email_hash}_{timestamp}{file_extension}"

        # Create licenses directory if it doesn't exist
        licenses_dir = Path("data/licenses")
        licenses_dir.mkdir(parents=True, exist_ok=True)

        # Save file
        file_path = licenses_dir / secure_filename
        with open(file_path, "wb") as f:
            f.write(content)

        logger.info(f"License file saved: {secure_filename}")
        return str(file_path)

    async def validate_license_number(self, license_number: str) -> bool:
        """Validate therapist license number format"""

        # Simple validation - in real app would check against professional registry
        return (
            license_number
            and len(license_number) >= 6
            and any(char.isdigit() for char in license_number)
        )

    async def check_email_available(self, email: str) -> bool:
        """Check if email is available for registration"""

        from app.services.user.auth_service import AuthService

        auth_service = AuthService(self.db)

        existing_user = await auth_service.get_user_by_email(email)
        return existing_user is None

    async def get_registration_statistics(self) -> Dict[str, Any]:
        """Get registration statistics for admin dashboard"""

        from sqlalchemy import and_, func

        # Total registrations
        total_users_result = await self.db.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar()

        # Registrations by role
        patients_result = await self.db.execute(
            select(func.count(User.id)).where(User.role == UserRole.PATIENT.value)
        )
        patients_count = patients_result.scalar()

        therapists_result = await self.db.execute(
            select(func.count(User.id)).where(User.role == UserRole.THERAPIST.value)
        )
        therapists_count = therapists_result.scalar()

        # Pending therapist verifications
        pending_therapists_result = await self.db.execute(
            select(func.count(User.id)).where(
                and_(User.role == UserRole.THERAPIST.value, User.is_verified == False)
            )
        )
        pending_therapists = pending_therapists_result.scalar()

        # Recent registrations (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_registrations_result = await self.db.execute(
            select(func.count(User.id)).where(User.created_at >= seven_days_ago)
        )
        recent_registrations = recent_registrations_result.scalar()

        return {
            "total_users": total_users,
            "patients": patients_count,
            "therapists": therapists_count,
            "pending_therapist_verifications": pending_therapists,
            "recent_registrations_7d": recent_registrations,
            "patient_to_therapist_ratio": round(
                patients_count / max(therapists_count, 1), 1
            ),
        }

    async def generate_welcome_data(self, user: User) -> Dict[str, Any]:
        """Generate welcome data for new user"""

        if user.role == UserRole.PATIENT.value:
            return {
                "welcome_message": f"Willkommen bei MindBridge, {user.first_name}!",
                "getting_started": [
                    {
                        "step": 1,
                        "title": "Erstes Mood-Tracking",
                        "description": "Beginne mit der Erfassung deiner täglichen Stimmung",
                        "action": "create_mood_entry",
                    },
                    {
                        "step": 2,
                        "title": "Traumtagebuch starten",
                        "description": "Dokumentiere deine Träume für tiefere Selbsterkenntnis",
                        "action": "create_dream_entry",
                    },
                    {
                        "step": 3,
                        "title": "Selbstreflexion",
                        "description": "Nutze unsere strukturierten Reflexions-Tools",
                        "action": "try_self_reflection",
                    },
                    {
                        "step": 4,
                        "title": "Optional: Therapeut einladen",
                        "description": "Später kannst du einem Therapeuten Zugang gewähren",
                        "action": "explore_sharing",
                    },
                ],
                "helpful_tips": [
                    "💡 Sei ehrlich zu dir selbst bei den Einträgen",
                    "📅 Versuche regelmäßige Einträge zu machen",
                    "🔒 Deine Daten sind vollständig privat und verschlüsselt",
                    "🎯 Kleine, regelmäßige Schritte sind besser als perfekte Einträge",
                ],
            }

        elif user.role == UserRole.THERAPIST.value:
            return {
                "welcome_message": f"Willkommen bei MindBridge, Dr. {user.last_name}!",
                "verification_status": {
                    "status": "pending",
                    "message": "Ihr Account wird von unserem Team verifiziert",
                    "estimated_time": "1-3 Werktage",
                    "next_steps": [
                        "📧 Sie erhalten eine Email bei Freigabe",
                        "📋 Unsere Fachkräfte prüfen Ihre Lizenz",
                        "✅ Nach Freigabe können Sie sich einloggen",
                        "👥 Dann können Ihnen Patienten Zugang gewähren",
                    ],
                },
                "platform_info": {
                    "patient_first_approach": "Patienten haben vollständige Kontrolle über ihre Daten",
                    "sharing_model": "Patienten entscheiden, was und wann geteilt wird",
                    "privacy_focus": "DSGVO-konforme, sichere Datenübertragung",
                    "support": "Bei Fragen: support@mindbridge.app",
                },
            }

        return {}
