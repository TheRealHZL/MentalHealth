"""
User Profile Service

Zuständig für Profil-Updates, Passwort-Änderung und Benutzer-Statistiken.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import hash_password
from src.models import (DreamEntry, MoodEntry, ShareKey, ShareKeyAccessLog,
                        TherapyNote, User, UserRole)
from src.schemas.ai import UserProfileUpdate

logger = logging.getLogger(__name__)


class ProfileService:
    """User Profile Service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def update_user_profile(
        self, user_id: str, profile_data: UserProfileUpdate
    ) -> User:
        """Update user profile"""

        from src.services.user.auth_service import AuthService

        auth_service = AuthService(self.db)

        user = await auth_service.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        # Update fields
        update_dict = profile_data.dict(exclude_unset=True)

        for field, value in update_dict.items():
            if hasattr(user, field) and value is not None:
                setattr(user, field, value)

        await self.db.commit()
        await self.db.refresh(user)

        logger.info(f"Profile updated: {user.email}")
        return user

    async def update_password(self, user_id: str, new_password: str) -> None:
        """Update user password"""

        from src.services.user.auth_service import AuthService

        auth_service = AuthService(self.db)

        user = await auth_service.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        user.password_hash = hash_password(new_password)
        await self.db.commit()

        logger.info(f"Password updated: {user.email}")

    async def get_profile_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get user profile statistics"""

        from src.services.user.auth_service import AuthService

        auth_service = AuthService(self.db)

        user = await auth_service.get_user_by_id(user_id)
        if not user:
            return {}

        if user.role == UserRole.PATIENT:
            return await self._get_patient_statistics(user_id)
        elif user.role == UserRole.THERAPIST:
            return await self._get_therapist_statistics(user_id)
        else:
            return {}

    async def _get_patient_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get patient-specific statistics"""

        # Mood entries count
        mood_result = await self.db.execute(
            select(func.count(MoodEntry.id)).where(
                MoodEntry.user_id == uuid.UUID(user_id)
            )
        )
        mood_count = mood_result.scalar()

        # Dream entries count
        dream_result = await self.db.execute(
            select(func.count(DreamEntry.id)).where(
                DreamEntry.user_id == uuid.UUID(user_id)
            )
        )
        dream_count = dream_result.scalar()

        # Therapy notes count
        therapy_result = await self.db.execute(
            select(func.count(TherapyNote.id)).where(
                TherapyNote.user_id == uuid.UUID(user_id)
            )
        )
        therapy_count = therapy_result.scalar()

        # Share keys count
        share_result = await self.db.execute(
            select(func.count(ShareKey.id)).where(
                ShareKey.patient_id == uuid.UUID(user_id)
            )
        )
        share_count = share_result.scalar()

        # Recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        recent_mood_result = await self.db.execute(
            select(func.count(MoodEntry.id)).where(
                and_(
                    MoodEntry.user_id == uuid.UUID(user_id),
                    MoodEntry.created_at >= thirty_days_ago,
                )
            )
        )
        recent_mood_count = recent_mood_result.scalar()

        # Get user for days calculation
        from src.services.user.auth_service import AuthService

        auth_service = AuthService(self.db)
        user = await auth_service.get_user_by_id(user_id)
        days_registered = (datetime.utcnow() - user.created_at).days

        return {
            "role": "patient",
            "total_mood_entries": mood_count,
            "total_dream_entries": dream_count,
            "total_therapy_notes": therapy_count,
            "total_share_keys": share_count,
            "recent_activity": {
                "mood_entries_30d": recent_mood_count,
                "active_days": min(days_registered, 30),
            },
            "usage_insights": {
                "avg_entries_per_week": round(
                    (mood_count / max(days_registered / 7, 1)), 1
                ),
                "most_used_feature": self._determine_most_used_feature(
                    mood_count, dream_count, therapy_count
                ),
                "consistency_score": self._calculate_consistency_score(
                    recent_mood_count, days_registered
                ),
            },
            "milestones": self._get_patient_milestones(
                mood_count, dream_count, therapy_count, days_registered
            ),
        }

    async def _get_therapist_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get therapist-specific statistics"""

        # Active patients
        active_patients_result = await self.db.execute(
            select(func.count(ShareKey.id.distinct())).where(
                and_(
                    ShareKey.therapist_id == uuid.UUID(user_id),
                    ShareKey.is_active == True,
                    ShareKey.is_accepted == True,
                )
            )
        )
        active_patients = active_patients_result.scalar()

        # Total accesses
        total_accesses_result = await self.db.execute(
            select(func.sum(ShareKey.access_count)).where(
                ShareKey.therapist_id == uuid.UUID(user_id)
            )
        )
        total_accesses = total_accesses_result.scalar() or 0

        # Recent activity
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_accesses_result = await self.db.execute(
            select(func.count(ShareKeyAccessLog.id)).where(
                and_(
                    ShareKeyAccessLog.share_key_id.in_(
                        select(ShareKey.id).where(
                            ShareKey.therapist_id == uuid.UUID(user_id)
                        )
                    ),
                    ShareKeyAccessLog.accessed_at >= seven_days_ago,
                )
            )
        )
        recent_accesses = recent_accesses_result.scalar()

        from src.services.user.auth_service import AuthService

        auth_service = AuthService(self.db)
        user = await auth_service.get_user_by_id(user_id)
        days_since_verification = (
            (datetime.utcnow() - user.created_at).days if user.is_verified else 0
        )

        return {
            "role": "therapist",
            "active_patients": active_patients,
            "total_data_accesses": total_accesses,
            "recent_activity": {
                "accesses_7d": recent_accesses,
                "avg_accesses_per_patient": round(
                    total_accesses / max(active_patients, 1), 1
                ),
            },
            "professional_info": {
                "license_number": user.license_number,
                "specializations": user.specializations,
                "verification_date": user.created_at if user.is_verified else None,
                "days_since_verification": days_since_verification,
            },
            "practice_metrics": {
                "patient_engagement": (
                    "high"
                    if recent_accesses > 5
                    else "medium" if recent_accesses > 0 else "low"
                ),
                "data_utilization": round(
                    (total_accesses / max(active_patients * 30, 1)) * 100, 1
                ),  # % of available data accessed
            },
        }

    def _determine_most_used_feature(
        self, mood_count: int, dream_count: int, therapy_count: int
    ) -> str:
        """Determine user's most used feature"""

        if mood_count >= dream_count and mood_count >= therapy_count:
            return "mood_tracking"
        elif dream_count >= therapy_count:
            return "dream_journal"
        else:
            return "therapy_notes"

    def _calculate_consistency_score(
        self, recent_entries: int, days_registered: int
    ) -> int:
        """Calculate user consistency score (0-100)"""

        if days_registered < 7:
            return 100 if recent_entries > 0 else 0

        # Aim for 3-4 entries per week
        target_entries = min(days_registered // 2, 12)  # Cap at 12 for 30-day period
        consistency = min(100, int((recent_entries / max(target_entries, 1)) * 100))

        return consistency

    def _get_patient_milestones(
        self,
        mood_count: int,
        dream_count: int,
        therapy_count: int,
        days_registered: int,
    ) -> List[str]:
        """Get patient achievement milestones"""

        milestones = []

        if mood_count >= 1:
            milestones.append("🎯 Erstes Mood-Tracking")
        if mood_count >= 7:
            milestones.append("📈 Eine Woche getrackt")
        if mood_count >= 30:
            milestones.append("🏆 Ein Monat konsequent")
        if dream_count >= 1:
            milestones.append("🌙 Erstes Traumtagebuch")
        if dream_count >= 10:
            milestones.append("💭 Traum-Explorer")
        if therapy_count >= 1:
            milestones.append("📝 Erste Reflexion")
        if therapy_count >= 5:
            milestones.append("🧠 Selbstreflexions-Profi")
        if days_registered >= 30:
            milestones.append("⭐ Einen Monat dabei")
        if days_registered >= 90:
            milestones.append("🎉 Langzeit-Nutzer")

        return milestones

    async def update_user_preferences(
        self, user_id: str, preferences: Dict[str, Any]
    ) -> None:
        """Update user preferences"""

        from src.services.user.auth_service import AuthService

        auth_service = AuthService(self.db)

        user = await auth_service.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        # Update specific preference fields
        if "timezone" in preferences:
            user.timezone = preferences["timezone"]

        if "notification_preferences" in preferences:
            user.notification_preferences = preferences["notification_preferences"]

        if "privacy_settings" in preferences:
            user.privacy_settings = preferences["privacy_settings"]

        await self.db.commit()
        logger.info(f"User preferences updated: {user.email}")

    async def get_profile_completion_status(self, user_id: str) -> Dict[str, Any]:
        """Get profile completion status and suggestions"""

        from src.services.user.auth_service import AuthService

        auth_service = AuthService(self.db)

        user = await auth_service.get_user_by_id(user_id)
        if not user:
            return {}

        completion_items = []
        completed_count = 0
        total_items = 0

        # Basic profile items
        basic_items = [
            ("email", "Email bestätigt", user.email_verified),
            ("name", "Name ausgefüllt", bool(user.first_name and user.last_name)),
            ("timezone", "Zeitzone gesetzt", bool(user.timezone)),
        ]

        if user.role == UserRole.PATIENT:
            patient_items = [
                (
                    "first_entry",
                    "Erster Mood-Eintrag",
                    await self._has_mood_entries(user_id),
                ),
                (
                    "profile_picture",
                    "Profilbild hochgeladen",
                    bool(user.profile_picture_url),
                ),
            ]
            basic_items.extend(patient_items)

        elif user.role == UserRole.THERAPIST:
            therapist_items = [
                ("license_verified", "Lizenz verifiziert", user.is_verified),
                (
                    "bio_complete",
                    "Bio ausgefüllt",
                    bool(user.bio and len(user.bio) > 50),
                ),
                (
                    "specializations",
                    "Spezialisierungen angegeben",
                    bool(user.specializations),
                ),
                ("practice_address", "Praxis-Adresse", bool(user.practice_address)),
            ]
            basic_items.extend(therapist_items)

        for item_key, item_name, is_completed in basic_items:
            completion_items.append(
                {"key": item_key, "name": item_name, "completed": is_completed}
            )

            total_items += 1
            if is_completed:
                completed_count += 1

        completion_percentage = (
            round((completed_count / total_items) * 100) if total_items > 0 else 0
        )

        return {
            "completion_percentage": completion_percentage,
            "completed_items": completed_count,
            "total_items": total_items,
            "items": completion_items,
            "next_suggestions": self._get_completion_suggestions(
                completion_items, user.role
            ),
        }

    def _get_completion_suggestions(
        self, items: List[Dict], role: UserRole
    ) -> List[str]:
        """Get suggestions for profile completion"""

        suggestions = []
        incomplete_items = [item for item in items if not item["completed"]]

        for item in incomplete_items[:3]:  # Top 3 suggestions
            if item["key"] == "first_entry":
                suggestions.append("📊 Erstelle deinen ersten Stimmungseintrag")
            elif item["key"] == "bio_complete":
                suggestions.append("📝 Vervollständige deine Therapeuten-Bio")
            elif item["key"] == "specializations":
                suggestions.append("🎯 Füge deine Spezialisierungen hinzu")
            elif item["key"] == "profile_picture":
                suggestions.append("📸 Lade ein Profilbild hoch")
            elif item["key"] == "practice_address":
                suggestions.append("📍 Trage deine Praxis-Adresse ein")

        return suggestions

    async def _has_mood_entries(self, user_id: str) -> bool:
        """Check if user has any mood entries"""

        result = await self.db.execute(
            select(func.count(MoodEntry.id)).where(
                MoodEntry.user_id == uuid.UUID(user_id)
            )
        )
        count = result.scalar()
        return count > 0
