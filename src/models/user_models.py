"""
User Models

Benutzer-bezogene Datenbank-Modelle für Patient und Therapeut.
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from src.core.database import Base

class UserRole(enum.Enum):
    """User role enumeration"""
    PATIENT = "patient"
    THERAPIST = "therapist"
    ADMIN = "admin"

class User(Base):
    """User model for patients, therapists, and admins"""
    
    __tablename__ = "users"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Basic info
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False, default=UserRole.PATIENT.value)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    registration_completed = Column(Boolean, default=False, nullable=False)
    
    # Personal details
    date_of_birth = Column(DateTime, nullable=True)
    timezone = Column(String(50), default="Europe/Berlin")
    profile_picture_url = Column(String(500), nullable=True)
    
    # Preferences & Settings
    notification_preferences = Column(JSON, nullable=True)
    privacy_settings = Column(JSON, nullable=True)
    
    # Therapist-specific fields
    license_number = Column(String(100), nullable=True)  # Only for therapists
    specializations = Column(ARRAY(String), nullable=True)  # Therapist specializations
    practice_address = Column(Text, nullable=True)  # Practice location
    phone_number = Column(String(20), nullable=True)  # Practice phone
    bio = Column(Text, nullable=True)  # Therapist bio
    license_file_path = Column(String(500), nullable=True)  # License document path
    
    # Verification fields (for therapists)
    verified_at = Column(DateTime, nullable=True)
    verification_notes = Column(Text, nullable=True)
    verification_rejected = Column(Boolean, default=False)
    rejection_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    mood_entries = relationship("MoodEntry", back_populates="user", cascade="all, delete-orphan")
    dream_entries = relationship("DreamEntry", back_populates="user", cascade="all, delete-orphan")
    therapy_notes = relationship("TherapyNote", back_populates="user", cascade="all, delete-orphan")
    
    # Share keys as patient
    patient_share_keys = relationship(
        "ShareKey", 
        foreign_keys="ShareKey.patient_id",
        back_populates="patient",
        cascade="all, delete-orphan"
    )
    
    # Share keys as therapist
    therapist_share_keys = relationship(
        "ShareKey",
        foreign_keys="ShareKey.therapist_id", 
        back_populates="therapist"
    )
    
    login_attempts = relationship("LoginAttempt", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
    
    @property
    def full_name(self) -> str:
        """Get full name"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_patient(self) -> bool:
        """Check if user is a patient"""
        return self.role == UserRole.PATIENT.value
    
    @property
    def is_therapist(self) -> bool:
        """Check if user is a therapist"""
        return self.role == UserRole.THERAPIST.value
    
    @property
    def is_admin(self) -> bool:
        """Check if user is an admin"""
        return self.role == UserRole.ADMIN.value
    
    def can_access_patient_data(self) -> bool:
        """Check if user can access patient data"""
        return self.is_therapist and self.is_verified
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert to dictionary"""
        base_dict = {
            "id": str(self.id),
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "role": self.role,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }
        
        if include_sensitive:
            base_dict.update({
                "email_verified": self.email_verified,
                "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
                "timezone": self.timezone,
                "notification_preferences": self.notification_preferences,
                "privacy_settings": self.privacy_settings
            })
            
            if self.is_therapist:
                base_dict.update({
                    "license_number": self.license_number,
                    "specializations": self.specializations,
                    "practice_address": self.practice_address,
                    "phone_number": self.phone_number,
                    "bio": self.bio,
                    "verified_at": self.verified_at.isoformat() if self.verified_at else None
                })
        
        return base_dict

class LoginAttempt(Base):
    """Login attempt tracking for security"""
    
    __tablename__ = "login_attempts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # Nullable for failed email attempts
    email = Column(String(255), nullable=False, index=True)
    
    successful = Column(Boolean, nullable=False)
    attempted_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Optional tracking data
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    failure_reason = Column(String(100), nullable=True)  # "invalid_password", "account_locked", etc.
    
    # Relationship
    user = relationship("User", back_populates="login_attempts")
    
    def __repr__(self):
        return f"<LoginAttempt(email={self.email}, successful={self.successful}, attempted_at={self.attempted_at})>"

class UserSession(Base):
    """User session tracking (optional, for enhanced security)"""
    
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True, nullable=True, index=True)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, server_default=func.now(), nullable=False)
    
    is_active = Column(Boolean, default=True, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    revocation_reason = Column(String(100), nullable=True)  # "logout", "security", "expired"
    
    # Device/Location tracking
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    device_info = Column(JSON, nullable=True)
    location_info = Column(JSON, nullable=True)
    
    # Relationship
    user = relationship("User")
    
    def __repr__(self):
        return f"<UserSession(user_id={self.user_id}, active={self.is_active}, expires_at={self.expires_at})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired"""
        from datetime import datetime
        return datetime.utcnow() > self.expires_at
    
    def revoke(self, reason: str = "manual"):
        """Revoke the session"""
        from datetime import datetime
        self.is_active = False
        self.revoked_at = datetime.utcnow()
        self.revocation_reason = reason

class UserNotification(Base):
    """User notifications system"""
    
    __tablename__ = "user_notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    notification_type = Column(String(50), nullable=False)  # "welcome", "share_key_accepted", "therapist_verified"
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=True)  # Optional expiration
    
    # Optional action data
    action_url = Column(String(500), nullable=True)
    action_data = Column(JSON, nullable=True)
    
    # Priority and styling
    priority = Column(String(20), default="normal")  # "low", "normal", "high", "urgent"
    icon = Column(String(50), nullable=True)
    color = Column(String(20), nullable=True)
    
    # Relationship
    user = relationship("User")
    
    def __repr__(self):
        return f"<UserNotification(user_id={self.user_id}, type={self.notification_type}, read={self.is_read})>"
    
    def mark_as_read(self):
        """Mark notification as read"""
        from datetime import datetime
        self.is_read = True
        self.read_at = datetime.utcnow()
    
    @property
    def is_expired(self) -> bool:
        """Check if notification is expired"""
        if not self.expires_at:
            return False
        from datetime import datetime
        return datetime.utcnow() > self.expires_at

class UserActivityLog(Base):
    """User activity logging for analytics and security"""
    
    __tablename__ = "user_activity_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    activity_type = Column(String(50), nullable=False)  # "login", "mood_entry", "share_key_created"
    activity_description = Column(String(200), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Optional metadata
    metadata = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Relationship
    user = relationship("User")
    
    def __repr__(self):
        return f"<UserActivityLog(user_id={self.user_id}, type={self.activity_type}, created_at={self.created_at})>"

# Index definitions for better performance
from sqlalchemy import Index

# Create indexes for common queries
Index('idx_users_email_active', User.email, User.is_active)
Index('idx_users_role_verified', User.role, User.is_verified)
Index('idx_login_attempts_email_time', LoginAttempt.email, LoginAttempt.attempted_at)
Index('idx_user_sessions_token', UserSession.session_token)
Index('idx_user_sessions_user_active', UserSession.user_id, UserSession.is_active)
Index('idx_notifications_user_unread', UserNotification.user_id, UserNotification.is_read)
Index('idx_activity_logs_user_type', UserActivityLog.user_id, UserActivityLog.activity_type)
