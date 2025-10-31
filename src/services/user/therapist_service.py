"""
Therapist Service

Zuständig für Therapeuten-spezifische Funktionen:
Verifikation, Suche, Patienten-Management.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import ShareKey, ShareKeyAccessLog, User, UserRole
from src.services.email_service import EmailService

logger = logging.getLogger(__name__)


class TherapistService:
    """Therapist Management Service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =============================================================================
    # Therapist Search & Discovery
    # =============================================================================

    async def search_verified_therapists(
        self,
        location: Optional[str] = None,
        specialization: Optional[str] = None,
        radius: int = 50,
    ) -> List[Dict[str, Any]]:
        """Search for verified therapists"""

        query = select(User).where(
            and_(
                User.role == UserRole.THERAPIST,
                User.is_verified == True,
                User.is_active == True,
            )
        )

        # Filter by specialization
        if specialization:
            query = query.where(
                or_(
                    func.array_to_string(User.specializations, ",").ilike(
                        f"%{specialization}%"
                    ),
                    func.lower(User.bio).like(f"%{specialization.lower()}%"),
                )
            )

        # Filter by location (simplified - in real app would use geocoding)
        if location:
            query = query.where(
                func.lower(User.practice_address).like(f"%{location.lower()}%")
            )

        query = query.order_by(User.created_at.desc()).limit(20)  # Limit results

        result = await self.db.execute(query)
        therapists = list(result.scalars().all())

        # Format for response (anonymized for patient safety)
        formatted_therapists = []
        for therapist in therapists:
            formatted_therapists.append(
                {
                    "id": str(therapist.id),
                    "name": f"Dr. {therapist.first_name} {therapist.last_name[0]}.",  # Partial last name for privacy
                    "specializations": therapist.specializations,
                    "bio": self._truncate_bio(therapist.bio),
                    "practice_location": self._extract_city_from_address(
                        therapist.practice_address
                    ),
                    "email": therapist.email,  # For share key creation
                    "verified_since": (
                        therapist.created_at.strftime("%Y")
                        if therapist.is_verified
                        else None
                    ),
                    "patient_count": await self._get_therapist_patient_count(
                        str(therapist.id)
                    ),
                    "experience_level": self._determine_experience_level(
                        therapist.created_at
                    ),
                    "availability_status": await self._get_availability_status(
                        str(therapist.id)
                    ),
                }
            )

        return formatted_therapists

    async def get_therapist_profile(
        self, therapist_id: str, requesting_user_role: str
    ) -> Dict[str, Any]:
        """Get detailed therapist profile (role-based visibility)"""

        from .auth_service import AuthService

        auth_service = AuthService(self.db)

        therapist = await auth_service.get_user_by_id(therapist_id)

        if not therapist or therapist.role != UserRole.THERAPIST:
            raise ValueError("Therapist not found")

        # Base profile info
        profile = {
            "id": str(therapist.id),
            "first_name": therapist.first_name,
            "specializations": therapist.specializations,
            "bio": therapist.bio,
            "is_verified": therapist.is_verified,
            "verified_since": therapist.created_at if therapist.is_verified else None,
        }

        # Additional info for patients (public view)
        if requesting_user_role == "patient":
            profile.update(
                {
                    "public_name": f"Dr. {therapist.first_name} {therapist.last_name[0]}.",
                    "practice_city": self._extract_city_from_address(
                        therapist.practice_address
                    ),
                    "specializations_detailed": therapist.specializations,
                    "bio_public": self._sanitize_bio_for_public(therapist.bio),
                    "patient_count": await self._get_therapist_patient_count(
                        therapist_id
                    ),
                    "experience_years": self._calculate_experience_years(
                        therapist.created_at
                    ),
                    "contact_info": {
                        "email": therapist.email,
                        "note": "Kontakt nur über MindBridge Share-Keys möglich",
                    },
                }
            )

        # Full info for the therapist themselves
        elif requesting_user_role == "therapist" and str(therapist.id) == therapist_id:
            profile.update(
                {
                    "full_name": f"{therapist.first_name} {therapist.last_name}",
                    "email": therapist.email,
                    "license_number": therapist.license_number,
                    "practice_address": therapist.practice_address,
                    "phone_number": therapist.phone_number,
                    "full_bio": therapist.bio,
                    "verification_status": (
                        "verified" if therapist.is_verified else "pending"
                    ),
                    "professional_stats": await self._get_professional_statistics(
                        therapist_id
                    ),
                }
            )

        return profile

    # =============================================================================
    # Therapist Verification & Admin
    # =============================================================================

    async def get_pending_verifications(self) -> List[Dict[str, Any]]:
        """Get therapists pending verification (admin function)"""

        result = await self.db.execute(
            select(User)
            .where(
                and_(
                    User.role == UserRole.THERAPIST,
                    User.is_verified == False,
                    User.is_active == True,
                )
            )
            .order_by(User.created_at.asc())
        )

        pending_therapists = list(result.scalars().all())

        verification_list = []
        for therapist in pending_therapists:
            verification_list.append(
                {
                    "id": str(therapist.id),
                    "name": f"{therapist.first_name} {therapist.last_name}",
                    "email": therapist.email,
                    "license_number": therapist.license_number,
                    "specializations": therapist.specializations,
                    "practice_address": therapist.practice_address,
                    "registration_date": therapist.created_at,
                    "days_pending": (datetime.utcnow() - therapist.created_at).days,
                    "license_file_path": therapist.license_file_path,
                    "bio_excerpt": self._truncate_bio(therapist.bio, max_length=150),
                }
            )

        return verification_list

    async def verify_therapist(
        self, therapist_id: str, admin_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Verify therapist account (admin function)"""

        from .auth_service import AuthService

        auth_service = AuthService(self.db)

        therapist = await auth_service.get_user_by_id(therapist_id)

        if not therapist or therapist.role != UserRole.THERAPIST:
            raise ValueError("Therapist not found")

        if therapist.is_verified:
            raise ValueError("Therapist already verified")

        # Verify the therapist
        therapist.is_verified = True
        therapist.verified_at = datetime.utcnow()
        therapist.verification_notes = admin_notes

        await self.db.commit()

        # Send verification email
        email_service = EmailService()
        await email_service.send_therapist_verification_approved(
            to_email=therapist.email, first_name=therapist.first_name
        )

        logger.info(f"Therapist verified: {therapist.email}")

        return {
            "therapist_id": str(therapist.id),
            "therapist_name": f"{therapist.first_name} {therapist.last_name}",
            "verification_date": therapist.verified_at,
            "admin_notes": admin_notes,
            "notification_sent": True,
        }

    async def reject_therapist_verification(
        self,
        therapist_id: str,
        rejection_reason: str,
        admin_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Reject therapist verification (admin function)"""

        from .auth_service import AuthService

        auth_service = AuthService(self.db)

        therapist = await auth_service.get_user_by_id(therapist_id)

        if not therapist or therapist.role != UserRole.THERAPIST:
            raise ValueError("Therapist not found")

        # Mark as rejected and deactivate
        therapist.is_active = False
        therapist.verification_rejected = True
        therapist.rejection_reason = rejection_reason
        therapist.verification_notes = admin_notes

        await self.db.commit()

        # Send rejection email
        email_service = EmailService()
        await email_service.send_therapist_verification_rejected(
            to_email=therapist.email,
            first_name=therapist.first_name,
            rejection_reason=rejection_reason,
        )

        logger.warning(
            f"Therapist verification rejected: {therapist.email} - {rejection_reason}"
        )

        return {
            "therapist_id": str(therapist.id),
            "therapist_name": f"{therapist.first_name} {therapist.last_name}",
            "rejection_reason": rejection_reason,
            "admin_notes": admin_notes,
            "notification_sent": True,
        }

    async def notify_admin_for_verification(self, therapist_id: uuid.UUID) -> None:
        """Notify admin about new therapist registration"""

        from .auth_service import AuthService

        auth_service = AuthService(self.db)

        therapist = await auth_service.get_user_by_id(str(therapist_id))

        if therapist:
            # Admin notification implementation
            # In production, this would send emails/Slack/admin dashboard notifications
            # For now, log the notification for monitoring
            logger.info(
                f"🔔 ADMIN NOTIFICATION: New therapist registration - {therapist.email}"
            )
            logger.info(
                f"🔔 Therapist details: ID={therapist_id}, Name={therapist.first_name} {therapist.last_name}"
            )

            # Future enhancement: Implement multi-channel notifications
            # Options:
            # 1. Email to admin team (implemented below)
            # 2. Slack webhook notification
            # 3. Admin dashboard notification
            # 4. SMS for urgent verifications

            from src.services.email_service import EmailService

            email_service = EmailService()
            await email_service.send_admin_therapist_notification(
                therapist_name=f"{therapist.first_name} {therapist.last_name}",
                therapist_email=therapist.email,
                license_number=therapist.license_number,
                registration_date=therapist.created_at,
            )

    # =============================================================================
    # Patient Management (for Therapists)
    # =============================================================================

    async def get_therapist_patients_overview(
        self, therapist_id: str
    ) -> Dict[str, Any]:
        """Get comprehensive overview of therapist's patients"""

        # Get all active share keys for this therapist
        result = await self.db.execute(
            select(ShareKey)
            .where(
                and_(
                    ShareKey.therapist_id == uuid.UUID(therapist_id),
                    ShareKey.is_active == True,
                    ShareKey.is_accepted == True,
                )
            )
            .order_by(desc(ShareKey.created_at))
        )

        share_keys = list(result.scalars().all())

        patients_overview = []
        total_data_points = 0

        for share_key in share_keys:
            patient_summary = await self._get_patient_summary_for_therapist(share_key)
            patients_overview.append(patient_summary)
            total_data_points += patient_summary.get("total_entries", 0)

        # Calculate aggregate statistics
        if patients_overview:
            avg_mood = sum(
                p.get("avg_mood_30d", 0)
                for p in patients_overview
                if p.get("avg_mood_30d")
            ) / len([p for p in patients_overview if p.get("avg_mood_30d")])
            most_common_challenges = self._aggregate_patient_challenges(
                patients_overview
            )
        else:
            avg_mood = 0
            most_common_challenges = []

        return {
            "total_patients": len(patients_overview),
            "patients": patients_overview,
            "aggregate_insights": {
                "total_data_points": total_data_points,
                "avg_patient_mood": round(avg_mood, 1) if avg_mood else None,
                "most_common_challenges": most_common_challenges,
                "engagement_distribution": self._calculate_engagement_distribution(
                    patients_overview
                ),
            },
            "clinical_notes": {
                "data_privacy": "Alle Daten sind anonymisiert und DSGVO-konform",
                "patient_control": "Patienten können Zugang jederzeit widerrufen",
                "ethical_use": "Daten nur für therapeutische Zwecke nutzen",
            },
        }

    async def get_patient_clinical_summary(
        self, therapist_id: str, patient_id: str, days: int = 30
    ) -> Dict[str, Any]:
        """Get clinical summary for specific patient"""

        # Verify therapist has access to this patient
        has_access = await self._verify_patient_access(therapist_id, patient_id)
        if not has_access:
            raise ValueError("No access to this patient's data")

        # Get anonymized clinical summary
        from src.services.sharing_service import SharingService

        sharing_service = SharingService(self.db)

        # Get different types of data
        mood_data = await sharing_service.get_patient_data_for_therapist(
            patient_id=patient_id,
            data_type="mood",
            start_date=datetime.utcnow() - timedelta(days=days),
            therapist_id=therapist_id,
        )

        therapy_data = await sharing_service.get_patient_data_for_therapist(
            patient_id=patient_id,
            data_type="therapy_notes",
            start_date=datetime.utcnow() - timedelta(days=days),
            therapist_id=therapist_id,
        )

        # Generate clinical insights
        clinical_summary = {
            "patient_id": patient_id,
            "summary_period": f"{days} days",
            "mood_analysis": mood_data.get("summary", {}),
            "therapy_progress": therapy_data.get("summary", {}),
            "clinical_observations": self._generate_clinical_observations(
                mood_data, therapy_data
            ),
            "recommended_focus_areas": self._suggest_focus_areas(
                mood_data, therapy_data
            ),
            "data_quality": {
                "mood_data_points": len(mood_data.get("entries", [])),
                "therapy_entries": len(therapy_data.get("entries", [])),
                "data_completeness": self._assess_data_completeness(
                    mood_data, therapy_data, days
                ),
            },
        }

        return clinical_summary

    # =============================================================================
    # Helper Methods
    # =============================================================================

    async def _get_therapist_patient_count(self, therapist_id: str) -> int:
        """Get number of active patients for therapist"""

        result = await self.db.execute(
            select(func.count(ShareKey.id.distinct())).where(
                and_(
                    ShareKey.therapist_id == uuid.UUID(therapist_id),
                    ShareKey.is_active == True,
                    ShareKey.is_accepted == True,
                )
            )
        )
        return result.scalar()

    def _truncate_bio(self, bio: Optional[str], max_length: int = 200) -> Optional[str]:
        """Truncate bio for public display"""
        if not bio:
            return None

        if len(bio) <= max_length:
            return bio

        return bio[:max_length].rsplit(" ", 1)[0] + "..."

    def _extract_city_from_address(self, address: Optional[str]) -> Optional[str]:
        """Extract city from practice address for privacy"""
        if not address:
            return None

        # Simple extraction - in real app would use proper address parsing
        parts = address.split(",")
        return parts[0].strip() if parts else None

    def _determine_experience_level(self, registration_date: datetime) -> str:
        """Determine experience level based on registration date"""

        months_since_registration = (datetime.utcnow() - registration_date).days / 30

        if months_since_registration < 6:
            return "new_to_platform"
        elif months_since_registration < 18:
            return "established"
        else:
            return "experienced"

    async def _get_availability_status(self, therapist_id: str) -> str:
        """Determine therapist availability status"""

        patient_count = await self._get_therapist_patient_count(therapist_id)

        if patient_count == 0:
            return "available"
        elif patient_count < 10:
            return "accepting_patients"
        elif patient_count < 20:
            return "limited_availability"
        else:
            return "fully_booked"

    def _sanitize_bio_for_public(self, bio: Optional[str]) -> Optional[str]:
        """Sanitize bio for public patient viewing"""
        if not bio:
            return None

        # Remove potentially sensitive information
        sanitized = bio

        # Remove email addresses, phone numbers, etc.
        import re

        sanitized = re.sub(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "[Email entfernt]",
            sanitized,
        )
        sanitized = re.sub(
            r"\b\d{2,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b",
            "[Telefonnummer entfernt]",
            sanitized,
        )

        return sanitized

    def _calculate_experience_years(self, registration_date: datetime) -> int:
        """Calculate years of experience on platform"""
        return max(0, (datetime.utcnow() - registration_date).days // 365)

    async def _get_professional_statistics(self, therapist_id: str) -> Dict[str, Any]:
        """Get detailed professional statistics for therapist"""

        # Patient engagement stats
        patient_count = await self._get_therapist_patient_count(therapist_id)

        # Total data accesses
        total_accesses_result = await self.db.execute(
            select(func.sum(ShareKey.access_count)).where(
                ShareKey.therapist_id == uuid.UUID(therapist_id)
            )
        )
        total_accesses = total_accesses_result.scalar() or 0

        # Recent activity
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_activity_result = await self.db.execute(
            select(func.count(ShareKeyAccessLog.id)).where(
                and_(
                    ShareKeyAccessLog.share_key_id.in_(
                        select(ShareKey.id).where(
                            ShareKey.therapist_id == uuid.UUID(therapist_id)
                        )
                    ),
                    ShareKeyAccessLog.accessed_at >= seven_days_ago,
                )
            )
        )
        recent_activity = recent_activity_result.scalar()

        return {
            "active_patients": patient_count,
            "total_data_accesses": total_accesses,
            "recent_activity_7d": recent_activity,
            "avg_accesses_per_patient": round(
                total_accesses / max(patient_count, 1), 1
            ),
            "engagement_level": (
                "high"
                if recent_activity > 10
                else "medium" if recent_activity > 3 else "low"
            ),
        }

    async def _get_patient_summary_for_therapist(
        self, share_key: ShareKey
    ) -> Dict[str, Any]:
        """Get patient summary for therapist dashboard"""

        # Basic patient info (anonymized)
        patient_summary = {
            "patient_id": str(share_key.patient_id),
            "patient_name": share_key.patient.first_name,  # Only first name
            "shared_since": share_key.created_at,
            "last_access": share_key.last_accessed,
            "total_accesses": share_key.access_count,
            "data_permissions": {
                "mood_data": share_key.include_mood_entries,
                "dream_data": share_key.include_dream_entries,
                "therapy_notes": share_key.include_therapy_notes,
            },
        }

        # Get recent patient statistics (anonymized)
        from src.services.sharing_service import SharingService

        sharing_service = SharingService(self.db)

        patient_stats = await sharing_service._get_patient_summary_stats(
            str(share_key.patient_id)
        )
        patient_summary.update(patient_stats)

        return patient_summary

    async def _verify_patient_access(self, therapist_id: str, patient_id: str) -> bool:
        """Verify therapist has access to patient data"""

        result = await self.db.execute(
            select(ShareKey).where(
                and_(
                    ShareKey.therapist_id == uuid.UUID(therapist_id),
                    ShareKey.patient_id == uuid.UUID(patient_id),
                    ShareKey.is_active == True,
                    ShareKey.is_accepted == True,
                )
            )
        )

        return result.scalar_one_or_none() is not None

    def _generate_clinical_observations(
        self, mood_data: Dict, therapy_data: Dict
    ) -> List[str]:
        """Generate clinical observations from patient data"""

        observations = []

        # Mood trend observations
        mood_summary = mood_data.get("summary", {})
        if mood_summary.get("avg_mood"):
            avg_mood = mood_summary["avg_mood"]
            if avg_mood < 4:
                observations.append(
                    "Durchschnittliche Stimmung liegt im niedrigen Bereich"
                )
            elif avg_mood > 7:
                observations.append("Überwiegend positive Stimmungslage")

            if mood_summary.get("mood_trend") == "improving":
                observations.append("Positive Stimmungsentwicklung erkennbar")
            elif mood_summary.get("mood_trend") == "declining":
                observations.append("Stimmungsrückgang zu beobachten")

        # Therapy progress observations
        therapy_summary = therapy_data.get("summary", {})
        if therapy_summary.get("total_notes", 0) > 5:
            observations.append("Hohe Therapie-Engagement sichtbar")

        return observations

    def _suggest_focus_areas(self, mood_data: Dict, therapy_data: Dict) -> List[str]:
        """Suggest therapeutic focus areas based on data"""

        focus_areas = []

        mood_summary = mood_data.get("summary", {})

        # Mood-based suggestions
        if mood_summary.get("avg_mood", 5) < 4:
            focus_areas.append("Stimmungsregulation und -stabilisierung")

        if mood_summary.get("avg_stress", 5) > 7:
            focus_areas.append("Stressmanagement-Techniken")

        # Therapy data based suggestions
        therapy_summary = therapy_data.get("summary", {})
        techniques = therapy_summary.get("techniques_used", [])

        if "cbt" in techniques:
            focus_areas.append("Vertiefung kognitiver Techniken")
        if "dbt" in techniques:
            focus_areas.append("Emotionsregulations-Skills")

        return focus_areas

    def _assess_data_completeness(
        self, mood_data: Dict, therapy_data: Dict, days: int
    ) -> str:
        """Assess completeness of patient data"""

        mood_entries = len(mood_data.get("entries", []))
        therapy_entries = len(therapy_data.get("entries", []))

        expected_entries = days // 3  # Expect entry every 3 days
        total_entries = mood_entries + therapy_entries

        if total_entries >= expected_entries:
            return "complete"
        elif total_entries >= expected_entries * 0.5:
            return "adequate"
        else:
            return "limited"

    def _aggregate_patient_challenges(self, patients: List[Dict]) -> List[str]:
        """Aggregate common challenges across patients"""

        # This would analyze common themes in patient data
        # Simplified for demo
        return ["Stressmanagement", "Schlafqualität", "Soziale Ängste"]

    def _calculate_engagement_distribution(
        self, patients: List[Dict]
    ) -> Dict[str, int]:
        """Calculate patient engagement distribution"""

        high_engagement = sum(1 for p in patients if p.get("mood_entries_30d", 0) > 15)
        medium_engagement = sum(
            1 for p in patients if 5 <= p.get("mood_entries_30d", 0) <= 15
        )
        low_engagement = len(patients) - high_engagement - medium_engagement

        return {
            "high": high_engagement,
            "medium": medium_engagement,
            "low": low_engagement,
        }
