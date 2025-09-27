"""
Sharing Models

Datenbank-Modelle für sicheres Datenteilen zwischen Patienten und Therapeuten.
Patient-First Ansatz mit vollständiger Kontrolle.
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from datetime import datetime, timedelta

from src.core.database import Base

# =============================================================================
# Share Key Models
# =============================================================================

class SharePermission(enum.Enum):
    """Share permission levels"""
    READ_ONLY = "read_only"
    READ_COMMENT = "read_comment"  # Can add comments (future feature)
    COLLABORATIVE = "collaborative"  # Can suggest entries (future feature)

class ShareKeyStatus(enum.Enum):
    """Share key status enumeration"""
    PENDING = "pending"  # Created but not accepted
    ACTIVE = "active"    # Accepted and active
    EXPIRED = "expired"  # Time expired
    REVOKED = "revoked"  # Manually revoked
    SESSION_LIMIT_REACHED = "session_limit_reached"

class ShareKey(Base):
    """Share keys for patient-therapist data sharing"""
    
    __tablename__ = "share_keys"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    share_key = Column(String(255), unique=True, nullable=False, index=True)  # The actual key
    
    # Participants
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    therapist_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # Null until accepted
    therapist_email = Column(String(255), nullable=False, index=True)  # Email for unregistered therapists
    
    # Permissions and access control
    permission_level = Column(String(20), nullable=False, default=SharePermission.READ_ONLY.value)
    include_mood_entries = Column(Boolean, default=True, nullable=False)
    include_dream_entries = Column(Boolean, default=False, nullable=False)
    include_therapy_notes = Column(Boolean, default=True, nullable=False)
    
    # Time and session limits
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=True)  # Optional expiration
    max_sessions = Column(Integer, nullable=True)  # Optional session limit
    
    # Status tracking
    is_active = Column(Boolean, default=True, nullable=False)
    is_accepted = Column(Boolean, default=False, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    
    # Access tracking
    access_count = Column(Integer, default=0, nullable=False)
    last_accessed = Column(DateTime, nullable=True)
    
    # Revocation
    revoked_at = Column(DateTime, nullable=True)
    revocation_reason = Column(String(100), nullable=True)  # "patient_request", "expired", "security"
    
    # Patient notes and therapist message
    notes = Column(Text, nullable=True)  # Patient's notes about sharing
    therapist_message = Column(Text, nullable=True)  # Therapist's acceptance message
    
    # Data filtering (for future granular control)
    date_range_start = Column(DateTime, nullable=True)  # Only share data after this date
    date_range_end = Column(DateTime, nullable=True)    # Only share data before this date
    exclude_tags = Column(ARRAY(String), nullable=True)  # Exclude entries with these tags
    
    # Emergency and safety
    emergency_contact = Column(Boolean, default=False)  # Is this therapist an emergency contact?
    crisis_access = Column(Boolean, default=False)      # Can access during crisis situations?
    
    # Metadata
    ip_address_created = Column(String(45), nullable=True)  # IP when key was created
    user_agent_created = Column(Text, nullable=True)        # User agent when created
    
    # Relationships
    patient = relationship("User", foreign_keys=[patient_id], back_populates="patient_share_keys")
    therapist = relationship("User", foreign_keys=[therapist_id], back_populates="therapist_share_keys")
    access_logs = relationship("ShareKeyAccessLog", back_populates="share_key", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ShareKey(id={self.id}, patient_id={self.patient_id}, therapist_email={self.therapist_email}, active={self.is_active})>"
    
    @property
    def status(self) -> ShareKeyStatus:
        """Get current status of share key"""
        if not self.is_active:
            if self.revoked_at:
                return ShareKeyStatus.REVOKED
            else:
                return ShareKeyStatus.EXPIRED
        
        if not self.is_accepted:
            return ShareKeyStatus.PENDING
        
        # Check expiration
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return ShareKeyStatus.EXPIRED
        
        # Check session limit
        if self.max_sessions and self.access_count >= self.max_sessions:
            return ShareKeyStatus.SESSION_LIMIT_REACHED
        
        return ShareKeyStatus.ACTIVE
    
    @property
    def is_valid(self) -> bool:
        """Check if share key is currently valid for access"""
        return self.status == ShareKeyStatus.ACTIVE
    
    @property
    def days_until_expiry(self) -> int:
        """Get days until expiry (or -1 if no expiry)"""
        if not self.expires_at:
            return -1
        
        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.days)
    
    @property
    def remaining_sessions(self) -> int:
        """Get remaining sessions (or -1 if unlimited)"""
        if not self.max_sessions:
            return -1
        
        return max(0, self.max_sessions - self.access_count)
    
    def can_access_data_type(self, data_type: str) -> bool:
        """Check if key allows access to specific data type"""
        type_mapping = {
            "mood": self.include_mood_entries,
            "dreams": self.include_dream_entries,
            "therapy_notes": self.include_therapy_notes
        }
        return type_mapping.get(data_type, False)
    
    def revoke(self, reason: str = "patient_request"):
        """Revoke the share key"""
        self.is_active = False
        self.revoked_at = datetime.utcnow()
        self.revocation_reason = reason
    
    def extend_expiry(self, days: int):
        """Extend expiry by specified days"""
        if self.expires_at:
            self.expires_at += timedelta(days=days)
        else:
            self.expires_at = datetime.utcnow() + timedelta(days=days)
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert to dictionary"""
        base_dict = {
            "id": str(self.id),
            "therapist_email": self.therapist_email,
            "permission_level": self.permission_level,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_accepted": self.is_accepted,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "data_permissions": {
                "mood_entries": self.include_mood_entries,
                "dream_entries": self.include_dream_entries,
                "therapy_notes": self.include_therapy_notes
            },
            "limits": {
                "max_sessions": self.max_sessions,
                "remaining_sessions": self.remaining_sessions,
                "days_until_expiry": self.days_until_expiry
            }
        }
        
        if include_sensitive:
            base_dict.update({
                "share_key": self.share_key,
                "notes": self.notes,
                "therapist_message": self.therapist_message
            })
        
        return base_dict

class ShareKeyAccessLog(Base):
    """Log of therapist access to patient data"""
    
    __tablename__ = "share_key_access_logs"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    share_key_id = Column(UUID(as_uuid=True), ForeignKey("share_keys.id"), nullable=False)
    
    # Access details
    accessed_at = Column(DateTime, server_default=func.now(), nullable=False)
    accessed_resource = Column(String(100), nullable=False)  # "mood_entries", "therapy_notes", etc.
    resource_count = Column(Integer, default=1, nullable=False)  # Number of items accessed
    
    # Access metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(255), nullable=True)  # Therapist's session ID
    
    # Data access details
    data_filters = Column(JSON, nullable=True)  # What filters were applied
    data_range = Column(JSON, nullable=True)    # Date range accessed
    
    # Actions performed
    action_type = Column(String(50), nullable=False, default="view")  # "view", "export", "comment"
    action_details = Column(JSON, nullable=True)  # Additional action metadata
    
    # Duration and engagement
    session_duration_seconds = Column(Integer, nullable=True)  # How long was data viewed
    items_viewed = Column(JSON, nullable=True)  # Which specific items were viewed
    
    # Relationship
    share_key = relationship("ShareKey", back_populates="access_logs")
    
    def __repr__(self):
        return f"<ShareKeyAccessLog(id={self.id}, share_key_id={self.share_key_id}, resource={self.accessed_resource}, accessed_at={self.accessed_at})>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "accessed_at": self.accessed_at.isoformat(),
            "accessed_resource": self.accessed_resource,
            "resource_count": self.resource_count,
            "action_type": self.action_type,
            "session_duration_seconds": self.session_duration_seconds,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent[:100] if self.user_agent else None  # Truncate for privacy
        }

# =============================================================================
# Therapist Access Models
# =============================================================================

class TherapistNoteAccess(Base):
    """Track which therapy notes therapists can access"""
    
    __tablename__ = "therapist_note_access"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # References
    share_key_id = Column(UUID(as_uuid=True), ForeignKey("share_keys.id"), nullable=False)
    therapy_note_id = Column(UUID(as_uuid=True), ForeignKey("therapy_notes.id"), nullable=False)
    
    # Access permissions
    can_view = Column(Boolean, default=True, nullable=False)
    can_comment = Column(Boolean, default=False, nullable=False)  # Future feature
    
    # Grant details
    granted_at = Column(DateTime, server_default=func.now(), nullable=False)
    granted_by_patient = Column(Boolean, default=True, nullable=False)  # Patient explicitly granted access
    
    # Revocation
    revoked_at = Column(DateTime, nullable=True)
    revocation_reason = Column(String(100), nullable=True)
    
    # Relationships
    share_key = relationship("ShareKey")
    
    def __repr__(self):
        return f"<TherapistNoteAccess(share_key_id={self.share_key_id}, therapy_note_id={self.therapy_note_id}, can_view={self.can_view})>"

class DataSharingAudit(Base):
    """Audit trail for all data sharing activities"""
    
    __tablename__ = "data_sharing_audit"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Event details
    event_type = Column(String(50), nullable=False)  # "share_key_created", "data_accessed", "key_revoked"
    event_description = Column(Text, nullable=False)
    occurred_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Participants
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    therapist_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    admin_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # For admin actions
    
    # Related objects
    share_key_id = Column(UUID(as_uuid=True), ForeignKey("share_keys.id"), nullable=True)
    
    # Event metadata
    event_data = Column(JSON, nullable=True)  # Additional event details
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Compliance and legal
    gdpr_relevant = Column(Boolean, default=False)  # Is this event GDPR relevant?
    retention_period_days = Column(Integer, nullable=True)  # How long to keep this log
    
    # Relationships
    patient = relationship("User", foreign_keys=[patient_id])
    therapist = relationship("User", foreign_keys=[therapist_id])
    admin_user = relationship("User", foreign_keys=[admin_user_id])
    share_key = relationship("ShareKey")
    
    def __repr__(self):
        return f"<DataSharingAudit(id={self.id}, event_type={self.event_type}, occurred_at={self.occurred_at})>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "event_type": self.event_type,
            "event_description": self.event_description,
            "occurred_at": self.occurred_at.isoformat(),
            "patient_id": str(self.patient_id) if self.patient_id else None,
            "therapist_id": str(self.therapist_id) if self.therapist_id else None,
            "share_key_id": str(self.share_key_id) if self.share_key_id else None,
            "event_data": self.event_data
        }

# =============================================================================
# Sharing Preferences Models
# =============================================================================

class PatientSharingPreferences(Base):
    """Patient preferences for data sharing"""
    
    __tablename__ = "patient_sharing_preferences"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    
    # Default sharing preferences
    default_mood_sharing = Column(Boolean, default=True)
    default_dream_sharing = Column(Boolean, default=False)
    default_therapy_sharing = Column(Boolean, default=True)
    
    # Default time limits
    default_expiry_days = Column(Integer, default=90)  # 90 days default
    default_max_sessions = Column(Integer, nullable=True)  # No limit by default
    
    # Auto-approval settings
    auto_approve_verified_therapists = Column(Boolean, default=False)
    auto_approve_emergency_access = Column(Boolean, default=True)
    
    # Notification preferences
    notify_on_access = Column(Boolean, default=True)
    notify_on_key_accepted = Column(Boolean, default=True)
    notify_daily_access_summary = Column(Boolean, default=False)
    
    # Privacy settings
    allow_anonymous_stats = Column(Boolean, default=True)  # For platform analytics
    allow_research_participation = Column(Boolean, default=False)  # For research studies
    
    # Emergency settings
    emergency_sharing_enabled = Column(Boolean, default=False)
    emergency_contact_therapist_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    crisis_auto_share_duration_hours = Column(Integer, default=24)  # 24 hours default
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    patient = relationship("User", foreign_keys=[patient_id])
    emergency_contact_therapist = relationship("User", foreign_keys=[emergency_contact_therapist_id])
    
    def __repr__(self):
        return f"<PatientSharingPreferences(patient_id={self.patient_id}, mood={self.default_mood_sharing}, dreams={self.default_dream_sharing})>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "patient_id": str(self.patient_id),
            "default_sharing": {
                "mood_entries": self.default_mood_sharing,
                "dream_entries": self.default_dream_sharing,
                "therapy_notes": self.default_therapy_sharing
            },
            "default_limits": {
                "expiry_days": self.default_expiry_days,
                "max_sessions": self.default_max_sessions
            },
            "auto_approval": {
                "verified_therapists": self.auto_approve_verified_therapists,
                "emergency_access": self.auto_approve_emergency_access
            },
            "notifications": {
                "on_access": self.notify_on_access,
                "on_key_accepted": self.notify_on_key_accepted,
                "daily_summary": self.notify_daily_access_summary
            },
            "emergency": {
                "enabled": self.emergency_sharing_enabled,
                "contact_therapist_id": str(self.emergency_contact_therapist_id) if self.emergency_contact_therapist_id else None,
                "auto_share_duration_hours": self.crisis_auto_share_duration_hours
            }
        }

# =============================================================================
# Sharing Statistics Models
# =============================================================================

class SharingStatistics(Base):
    """Anonymized sharing statistics for platform analytics"""
    
    __tablename__ = "sharing_statistics"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Date for aggregation
    date = Column(DateTime, nullable=False, index=True)
    
    # Anonymized counts
    total_active_share_keys = Column(Integer, default=0)
    new_share_keys_created = Column(Integer, default=0)
    share_keys_accepted = Column(Integer, default=0)
    share_keys_revoked = Column(Integer, default=0)
    share_keys_expired = Column(Integer, default=0)
    
    # Data access stats
    total_data_accesses = Column(Integer, default=0)
    mood_data_accesses = Column(Integer, default=0)
    dream_data_accesses = Column(Integer, default=0)
    therapy_data_accesses = Column(Integer, default=0)
    
    # Engagement metrics
    avg_session_duration_seconds = Column(Integer, nullable=True)
    unique_therapists_accessing = Column(Integer, default=0)
    unique_patients_sharing = Column(Integer, default=0)
    
    # Privacy metrics
    total_revocations = Column(Integer, default=0)
    emergency_accesses = Column(Integer, default=0)
    
    # Generated timestamp
    generated_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<SharingStatistics(date={self.date}, active_keys={self.total_active_share_keys})>"

# =============================================================================
# Indexes for Performance
# =============================================================================

from sqlalchemy import Index

# Share keys indexes
Index('idx_share_keys_patient_active', ShareKey.patient_id, ShareKey.is_active)
Index('idx_share_keys_therapist_active', ShareKey.therapist_id, ShareKey.is_active)
Index('idx_share_keys_email_active', ShareKey.therapist_email, ShareKey.is_active)
Index('idx_share_keys_key_lookup', ShareKey.share_key)
Index('idx_share_keys_expiry', ShareKey.expires_at, ShareKey.is_active)

# Access logs indexes
Index('idx_access_logs_share_key_time', ShareKeyAccessLog.share_key_id, ShareKeyAccessLog.accessed_at)
Index('idx_access_logs_resource_time', ShareKeyAccessLog.accessed_resource, ShareKeyAccessLog.accessed_at)

# Audit trail indexes
Index('idx_audit_patient_event', DataSharingAudit.patient_id, DataSharingAudit.event_type)
Index('idx_audit_therapist_event', DataSharingAudit.therapist_id, DataSharingAudit.event_type)
Index('idx_audit_time_event', DataSharingAudit.occurred_at, DataSharingAudit.event_type)

# Statistics indexes
Index('idx_sharing_stats_date', SharingStatistics.date)
