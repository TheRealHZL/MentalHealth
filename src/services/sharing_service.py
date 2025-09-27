"""
Sharing Service - Secure Data Sharing

Business Logic für sicheres Teilen von Patientendaten mit Therapeuten.
Patient-First Ansatz mit vollständiger Kontrolle.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc, or_
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timedelta, date
import uuid
import secrets
import logging

from src.models import (
    ShareKey, SharePermission, ShareKeyAccessLog, TherapyNoteAccess,
    User, UserRole, MoodEntry, DreamEntry, TherapyNote
)
from src.schemas.ai import PaginationParams

logger = logging.getLogger(__name__)

class SharingService:
    """Secure Data Sharing Service"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # =============================================================================
    # Share Key Management
    # =============================================================================
    
    async def create_share_key(
        self,
        patient_id: str,
        therapist_email: str,
        permission_level: SharePermission = SharePermission.READ_ONLY,
        include_mood_entries: bool = True,
        include_dream_entries: bool = False,
        include_therapy_notes: bool = True,
        expires_at: Optional[datetime] = None,
        max_sessions: Optional[int] = None,
        notes: Optional[str] = None
    ) -> ShareKey:
        """Create secure share key for therapist access"""
        
        # Generate secure share key
        share_key_value = secrets.token_urlsafe(32)
        
        # Default expiration: 90 days
        if not expires_at:
            expires_at = datetime.utcnow() + timedelta(days=90)
        
        share_key = ShareKey(
            share_key=share_key_value,
            patient_id=uuid.UUID(patient_id),
            therapist_email=therapist_email.lower(),
            permission_level=permission_level,
            include_mood_entries=include_mood_entries,
            include_dream_entries=include_dream_entries,
            include_therapy_notes=include_therapy_notes,
            expires_at=expires_at,
            max_sessions=max_sessions,
            notes=notes,
            is_active=True,
            is_accepted=False,
            access_count=0
        )
        
        self.db.add(share_key)
        await self.db.commit()
        await self.db.refresh(share_key)
        
        logger.info(f"Share key created: {patient_id} -> {therapist_email}")
        return share_key
    
    async def accept_share_key(
        self,
        share_key: str,
        therapist_id: str,
        therapist_email: str,
        message: Optional[str] = None
    ) -> ShareKey:
        """Therapist accepts a share key"""
        
        # Find and validate share key
        result = await self.db.execute(
            select(ShareKey).where(
                and_(
                    ShareKey.share_key == share_key,
                    ShareKey.therapist_email == therapist_email.lower(),
                    ShareKey.is_active == True,
                    ShareKey.is_accepted == False,
                    or_(
                        ShareKey.expires_at.is_(None),
                        ShareKey.expires_at > datetime.utcnow()
                    )
                )
            )
        )
        
        share_key_obj = result.scalar_one_or_none()
        
        if not share_key_obj:
            raise ValueError("Ungültiger oder abgelaufener Share-Key")
        
        # Accept the key
        share_key_obj.therapist_id = uuid.UUID(therapist_id)
        share_key_obj.is_accepted = True
        
        await self.db.commit()
        await self.db.refresh(share_key_obj)
        
        # Log the acceptance
        await self._log_access(
            share_key_obj.id,
            "share_key_accepted",
            f"Therapeut hat Zugang akzeptiert. Nachricht: {message or 'Keine'}"
        )
        
        logger.info(f"Share key accepted: {therapist_id} accepted key from {share_key_obj.patient_id}")
        return share_key_obj
    
    async def revoke_share_key(
        self,
        share_key_id: str,
        patient_id: str
    ) -> Optional[ShareKey]:
        """Patient revokes a share key"""
        
        result = await self.db.execute(
            select(ShareKey).where(
                and_(
                    ShareKey.id == uuid.UUID(share_key_id),
                    ShareKey.patient_id == uuid.UUID(patient_id),
                    ShareKey.is_active == True
                )
            )
        )
        
        share_key = result.scalar_one_or_none()
        
        if not share_key:
            return None
        
        # Revoke the key
        share_key.is_active = False
        
        await self.db.commit()
        
        # Log the revocation
        await self._log_access(
            share_key.id,
            "share_key_revoked",
            "Patient hat Zugang widerrufen"
        )
        
        logger.info(f"Share key revoked: {patient_id} revoked {share_key_id}")
        return share_key
    
    async def emergency_revoke_all_share_keys(self, patient_id: str) -> int:
        """Emergency revoke all active share keys for patient"""
        
        result = await self.db.execute(
            select(ShareKey).where(
                and_(
                    ShareKey.patient_id == uuid.UUID(patient_id),
                    ShareKey.is_active == True
                )
            )
        )
        
        active_keys = list(result.scalars().all())
        
        # Revoke all keys
        for share_key in active_keys:
            share_key.is_active = False
            
            # Log emergency revocation
            await self._log_access(
                share_key.id,
                "emergency_revoke",
                "NOTFALL: Patient hat alle Zugriffe widerrufen"
            )
        
        await self.db.commit()
        
        logger.warning(f"EMERGENCY REVOKE: Patient {patient_id} revoked {len(active_keys)} keys")
        return len(active_keys)
    
    # =============================================================================
    # Data Access & Verification
    # =============================================================================
    
    async def verify_therapist_access(
        self,
        therapist_id: str,
        patient_id: str,
        data_type: str
    ) -> bool:
        """Verify if therapist has access to specific patient data type"""
        
        result = await self.db.execute(
            select(ShareKey).where(
                and_(
                    ShareKey.therapist_id == uuid.UUID(therapist_id),
                    ShareKey.patient_id == uuid.UUID(patient_id),
                    ShareKey.is_active == True,
                    ShareKey.is_accepted == True,
                    or_(
                        ShareKey.expires_at.is_(None),
                        ShareKey.expires_at > datetime.utcnow()
                    )
                )
            )
        )
        
        share_key = result.scalar_one_or_none()
        
        if not share_key:
            return False
        
        # Check specific data type permissions
        if data_type == "mood" and not share_key.include_mood_entries:
            return False
        elif data_type == "dreams" and not share_key.include_dream_entries:
            return False
        elif data_type == "therapy_notes" and not share_key.include_therapy_notes:
            return False
        
        # Check session limits
        if share_key.max_sessions and share_key.access_count >= share_key.max_sessions:
            return False
        
        return True
    
    async def get_patient_data_for_therapist(
        self,
        patient_id: str,
        data_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        therapist_id: str = None
    ) -> Dict[str, Any]:
        """Get anonymized patient data for therapist"""
        
        # Increment access count
        if therapist_id:
            await self._increment_access_count(therapist_id, patient_id, data_type)
        
        if data_type == "mood":
            return await self._get_mood_data_anonymized(patient_id, start_date, end_date)
        elif data_type == "dreams":
            return await self._get_dream_data_anonymized(patient_id, start_date, end_date)
        elif data_type == "therapy_notes":
            return await self._get_therapy_notes_anonymized(patient_id, start_date, end_date)
        else:
            raise ValueError(f"Unbekannter Datentyp: {data_type}")
    
    async def _get_mood_data_anonymized(
        self,
        patient_id: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Dict[str, Any]:
        """Get anonymized mood data"""
        
        query = select(MoodEntry).where(MoodEntry.user_id == uuid.UUID(patient_id))
        
        if start_date:
            query = query.where(MoodEntry.created_at >= start_date)
        if end_date:
            query = query.where(MoodEntry.created_at <= end_date)
        
        query = query.order_by(desc(MoodEntry.entry_date)).limit(100)  # Limit for privacy
        
        result = await self.db.execute(query)
        entries = list(result.scalars().all())
        
        # Anonymize data
        anonymized_entries = []
        for entry in entries:
            anonymized_entries.append({
                "date": entry.entry_date.isoformat(),
                "mood_score": entry.mood_score,
                "stress_level": entry.stress_level,
                "energy_level": entry.energy_level,
                "sleep_quality": entry.sleep_quality,
                "sleep_hours": entry.sleep_hours,
                "exercise_minutes": entry.exercise_minutes,
                "activities": entry.activities,
                "symptoms": entry.symptoms[:3] if entry.symptoms else [],  # Limit symptoms
                "triggers": entry.triggers[:3] if entry.triggers else [],  # Limit triggers
                "notes": entry.notes[:200] + "..." if entry.notes and len(entry.notes) > 200 else entry.notes,  # Truncate notes
                # Persönliche Daten werden entfernt: location, medication_notes
            })
        
        # Calculate summary statistics
        if entries:
            mood_scores = [e.mood_score for e in entries]
            stress_levels = [e.stress_level for e in entries]
            
            summary = {
                "total_entries": len(entries),
                "avg_mood": round(sum(mood_scores) / len(mood_scores), 1),
                "avg_stress": round(sum(stress_levels) / len(stress_levels), 1),
                "mood_trend": self._calculate_trend(mood_scores),
                "date_range": {
                    "start": entries[-1].entry_date.isoformat(),
                    "end": entries[0].entry_date.isoformat()
                }
            }
        else:
            summary = {"total_entries": 0}
        
        return {
            "data_type": "mood_entries",
            "entries": anonymized_entries,
            "summary": summary,
            "privacy_note": "Daten sind anonymisiert. Persönliche Details wurden entfernt."
        }
    
    async def _get_dream_data_anonymized(
        self,
        patient_id: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Dict[str, Any]:
        """Get anonymized dream data"""
        
        query = select(DreamEntry).where(DreamEntry.user_id == uuid.UUID(patient_id))
        
        if start_date:
            query = query.where(DreamEntry.created_at >= start_date)
        if end_date:
            query = query.where(DreamEntry.created_at <= end_date)
        
        query = query.order_by(desc(DreamEntry.dream_date)).limit(50)
        
        result = await self.db.execute(query)
        entries = list(result.scalars().all())
        
        # Anonymize dream data
        anonymized_entries = []
        for entry in entries:
            # Remove specific people names, keep general categories
            people_anonymized = ["Person A", "Person B", "Familie", "Freund"] if entry.people_in_dream else []
            
            anonymized_entries.append({
                "date": entry.dream_date.isoformat(),
                "dream_type": entry.dream_type.value,
                "mood_after_waking": entry.mood_after_waking,
                "sleep_quality": entry.sleep_quality,
                "became_lucid": entry.became_lucid,
                "description": entry.description[:300] + "..." if len(entry.description) > 300 else entry.description,
                "symbols": entry.symbols[:5] if entry.symbols else [],  # Limit symbols
                "emotions_felt": entry.emotions_felt[:5] if entry.emotions_felt else [],
                "people_categories": people_anonymized[:3],  # Anonymized people
                "location_types": entry.locations[:3] if entry.locations else [],
                # Entfernt: personal_interpretation, life_connection (zu persönlich)
            })
        
        return {
            "data_type": "dream_entries",
            "entries": anonymized_entries,
            "summary": {
                "total_dreams": len(entries),
                "dream_types": self._get_dream_type_distribution(entries),
                "avg_mood_after": round(sum(e.mood_after_waking for e in entries) / len(entries), 1) if entries else 0
            },
            "privacy_note": "Traumdaten anonymisiert. Persönliche Interpretationen entfernt."
        }
    
    async def _get_therapy_notes_anonymized(
        self,
        patient_id: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Dict[str, Any]:
        """Get anonymized therapy notes"""
        
        query = select(TherapyNote).where(
            and_(
                TherapyNote.user_id == uuid.UUID(patient_id),
                TherapyNote.share_with_therapist == True  # Only shared notes
            )
        )
        
        if start_date:
            query = query.where(TherapyNote.created_at >= start_date)
        if end_date:
            query = query.where(TherapyNote.created_at <= end_date)
        
        query = query.order_by(desc(TherapyNote.note_date)).limit(50)
        
        result = await self.db.execute(query)
        entries = list(result.scalars().all())
        
        # Anonymize therapy notes
        anonymized_entries = []
        for entry in entries:
            anonymized_entries.append({
                "date": entry.note_date.isoformat(),
                "note_type": entry.note_type.value,
                "title": entry.title,
                "content_summary": entry.content[:200] + "..." if len(entry.content) > 200 else entry.content,
                "techniques_used": entry.techniques_used,
                "goals_discussed": entry.goals_discussed[:3] if entry.goals_discussed else [],
                "challenges_faced": entry.challenges_faced[:3] if entry.challenges_faced else [],
                "mood_before": entry.mood_before_session,
                "mood_after": entry.mood_after_session,
                "key_emotions": entry.key_emotions[:3] if entry.key_emotions else [],
                "progress_made": entry.progress_made[:300] + "..." if entry.progress_made and len(entry.progress_made) > 300 else entry.progress_made,
                # Entfernt: Sehr persönliche Details wie key_insights
            })
        
        return {
            "data_type": "therapy_notes",
            "entries": anonymized_entries,
            "summary": {
                "total_notes": len(entries),
                "note_types": self._get_note_type_distribution(entries),
                "techniques_used": self._get_technique_distribution(entries),
                "mood_improvement": self._calculate_mood_improvement(entries)
            },
            "privacy_note": "Nur zur Therapie freigegebene Notizen. Sehr persönliche Details entfernt."
        }
    
    # =============================================================================
    # Patient & Therapist Overviews
    # =============================================================================
    
    async def get_patient_share_keys(
        self,
        patient_id: str,
        pagination: PaginationParams,
        status_filter: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get patient's share keys with status"""
        
        query = select(ShareKey).where(ShareKey.patient_id == uuid.UUID(patient_id))
        count_query = select(func.count(ShareKey.id)).where(ShareKey.patient_id == uuid.UUID(patient_id))
        
        # Apply status filter
        if status_filter == "active":
            filter_condition = and_(
                ShareKey.is_active == True,
                ShareKey.is_accepted == True,
                or_(
                    ShareKey.expires_at.is_(None),
                    ShareKey.expires_at > datetime.utcnow()
                )
            )
            query = query.where(filter_condition)
            count_query = count_query.where(filter_condition)
        elif status_filter == "inactive":
            query = query.where(ShareKey.is_active == False)
            count_query = count_query.where(ShareKey.is_active == False)
        elif status_filter == "expired":
            query = query.where(
                and_(
                    ShareKey.is_active == True,
                    ShareKey.expires_at <= datetime.utcnow()
                )
            )
            count_query = count_query.where(
                and_(
                    ShareKey.is_active == True,
                    ShareKey.expires_at <= datetime.utcnow()
                )
            )
        
        # Pagination
        offset = (pagination.page - 1) * pagination.page_size
        query = query.order_by(desc(ShareKey.created_at)).offset(offset).limit(pagination.page_size)
        
        # Execute queries
        entries_result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        
        share_keys = list(entries_result.scalars().all())
        total_count = count_result.scalar()
        
        # Format for response
        formatted_keys = []
        for key in share_keys:
            status = self._get_share_key_status(key)
            
            formatted_keys.append({
                "id": str(key.id),
                "therapist_email": key.therapist_email,
                "permission_level": key.permission_level.value,
                "status": status,
                "created_at": key.created_at,
                "expires_at": key.expires_at,
                "last_accessed": key.last_accessed,
                "access_count": key.access_count,
                "includes": {
                    "mood_entries": key.include_mood_entries,
                    "dream_entries": key.include_dream_entries,
                    "therapy_notes": key.include_therapy_notes
                }
            })
        
        return formatted_keys, total_count
    
    async def get_therapist_patients(self, therapist_id: str) -> List[Dict[str, Any]]:
        """Get therapist's patients overview"""
        
        result = await self.db.execute(
            select(ShareKey).where(
                and_(
                    ShareKey.therapist_id == uuid.UUID(therapist_id),
                    ShareKey.is_active == True,
                    ShareKey.is_accepted == True
                )
            ).order_by(desc(ShareKey.created_at))
        )
        
        share_keys = list(result.scalars().all())
        
        patients = []
        for key in share_keys:
            # Get basic patient stats (anonymized)
            patient_stats = await self._get_patient_summary_stats(str(key.patient_id))
            
            patients.append({
                "patient_id": str(key.patient_id),
                "patient_name": key.patient.first_name,  # Only first name
                "permission_level": key.permission_level.value,
                "shared_since": key.created_at,
                "last_accessed": key.last_accessed,
                "access_count": key.access_count,
                "data_access": {
                    "mood_entries": key.include_mood_entries,
                    "dream_entries": key.include_dream_entries,
                    "therapy_notes": key.include_therapy_notes
                },
                "summary_stats": patient_stats,
                "expires_at": key.expires_at
            })
        
        return patients
    
    # =============================================================================
    # Access Logging & Statistics
    # =============================================================================
    
    async def _log_access(
        self,
        share_key_id: uuid.UUID,
        accessed_resource: str,
        details: str = "",
        resource_count: int = 1
    ) -> None:
        """Log therapist access to patient data"""
        
        access_log = ShareKeyAccessLog(
            share_key_id=share_key_id,
            accessed_resource=accessed_resource,
            resource_count=resource_count
        )
        
        self.db.add(access_log)
        await self.db.commit()
    
    async def _increment_access_count(
        self,
        therapist_id: str,
        patient_id: str,
        data_type: str
    ) -> None:
        """Increment access count and update last accessed"""
        
        result = await self.db.execute(
            select(ShareKey).where(
                and_(
                    ShareKey.therapist_id == uuid.UUID(therapist_id),
                    ShareKey.patient_id == uuid.UUID(patient_id),
                    ShareKey.is_active == True
                )
            )
        )
        
        share_key = result.scalar_one_or_none()
        
        if share_key:
            share_key.access_count += 1
            share_key.last_accessed = datetime.utcnow()
            
            # Log the specific access
            await self._log_access(
                share_key.id,
                data_type,
                f"Therapeut hat {data_type} Daten abgerufen"
            )
            
            await self.db.commit()
    
    async def get_access_logs(
        self,
        share_key_id: str,
        pagination: PaginationParams
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get access logs for a share key"""
        
        query = select(ShareKeyAccessLog).where(
            ShareKeyAccessLog.share_key_id == uuid.UUID(share_key_id)
        )
        count_query = select(func.count(ShareKeyAccessLog.id)).where(
            ShareKeyAccessLog.share_key_id == uuid.UUID(share_key_id)
        )
        
        # Pagination
        offset = (pagination.page - 1) * pagination.page_size
        query = query.order_by(desc(ShareKeyAccessLog.accessed_at)).offset(offset).limit(pagination.page_size)
        
        # Execute queries
        logs_result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        
        logs = list(logs_result.scalars().all())
        total_count = count_result.scalar()
        
        # Format logs
        formatted_logs = []
        for log in logs:
            formatted_logs.append({
                "accessed_at": log.accessed_at,
                "resource": log.accessed_resource,
                "resource_count": log.resource_count,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent[:100] if log.user_agent else None  # Truncate
            })
        
        return formatted_logs, total_count
    
    # =============================================================================
    # Helper Methods
    # =============================================================================
    
    def _get_share_key_status(self, share_key: ShareKey) -> str:
        """Determine share key status"""
        
        if not share_key.is_active:
            return "revoked"
        elif not share_key.is_accepted:
            return "pending"
        elif share_key.expires_at and share_key.expires_at <= datetime.utcnow():
            return "expired"
        elif share_key.max_sessions and share_key.access_count >= share_key.max_sessions:
            return "session_limit_reached"
        else:
            return "active"
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend from list of values"""
        
        if len(values) < 2:
            return "insufficient_data"
        
        # Simple trend: compare first and last third
        third = len(values) // 3
        if third == 0:
            return "stable"
        
        first_third_avg = sum(values[:third]) / third
        last_third_avg = sum(values[-third:]) / third
        
        change = last_third_avg - first_third_avg
        
        if change > 0.5:
            return "improving"
        elif change < -0.5:
            return "declining"
        else:
            return "stable"
    
    async def get_share_key_by_id(self, share_key_id: str, patient_id: str) -> Optional[ShareKey]:
        """Get share key by ID for patient"""
        
        result = await self.db.execute(
            select(ShareKey).where(
                and_(
                    ShareKey.id == uuid.UUID(share_key_id),
                    ShareKey.patient_id == uuid.UUID(patient_id)
                )
            )
        )
        
        return result.scalar_one_or_none()
    
    async def notify_patient_of_acceptance(
        self,
        share_key_id: uuid.UUID,
        therapist_name: str,
        message: Optional[str]
    ) -> None:
        """Notify patient that therapist accepted share key"""
        
        # Log the notification
        await self._log_access(
            share_key_id,
            "therapist_accepted",
            f"Therapeut {therapist_name} hat Zugang akzeptiert. Nachricht: {message or 'Keine'}"
        )
        
        # TODO: Implement actual notification (email, in-app, etc.)
        logger.info(f"Patient notification: Therapist {therapist_name} accepted share key {share_key_id}")
    
    async def notify_therapist_of_revocation(
        self,
        share_key_id: str,
        patient_name: str
    ) -> None:
        """Notify therapist that patient revoked access"""
        
        # TODO: Implement actual notification (email, in-app, etc.)
        logger.info(f"Therapist notification: Patient {patient_name} revoked share key {share_key_id}")
    
    async def _get_patient_summary_stats(self, patient_id: str) -> Dict[str, Any]:
        """Get anonymized patient summary statistics"""
        
        # Get recent mood data (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        mood_result = await self.db.execute(
            select(MoodEntry.mood_score).where(
                and_(
                    MoodEntry.user_id == uuid.UUID(patient_id),
                    MoodEntry.created_at >= thirty_days_ago
                )
            )
        )
        
        mood_scores = [row[0] for row in mood_result.all()]
        
        if mood_scores:
            return {
                "avg_mood_30d": round(sum(mood_scores) / len(mood_scores), 1),
                "mood_entries_30d": len(mood_scores),
                "mood_trend": self._calculate_trend(mood_scores),
                "last_entry": "recent"  # Anonymized
            }
        else:
            return {
                "avg_mood_30d": None,
                "mood_entries_30d": 0,
                "mood_trend": "no_data",
                "last_entry": None
            }
