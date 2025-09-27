"""
Models Package

Zentrale Imports für alle Datenbank-Modelle.
"""

# User Models
from .user_models import (
    User,
    UserRole,
    LoginAttempt,
    UserSession,
    UserNotification,
    UserActivityLog
)

# Content Models
from .content_models import (
    # Mood tracking
    MoodEntry,
    MoodLevel,
    
    # Dream journal
    DreamEntry,
    DreamType,
    
    # Therapy notes
    TherapyNote,
    TherapyNoteType,
    TherapyTechnique
)

# Sharing Models
from .sharing_models import (
    # Share keys
    ShareKey,
    SharePermission,
    ShareKeyStatus,
    ShareKeyAccessLog,
    
    # Access control
    TherapistNoteAccess,
    DataSharingAudit,
    
    # Preferences and settings
    PatientSharingPreferences,
    SharingStatistics
)

# Export all models for easy importing
__all__ = [
    # User models
    "User",
    "UserRole", 
    "LoginAttempt",
    "UserSession",
    "UserNotification",
    "UserActivityLog",
    
    # Content models
    "MoodEntry",
    "MoodLevel",
    "DreamEntry", 
    "DreamType",
    "TherapyNote",
    "TherapyNoteType",
    "TherapyTechnique",
    
    # Sharing models
    "ShareKey",
    "SharePermission",
    "ShareKeyStatus", 
    "ShareKeyAccessLog",
    "TherapistNoteAccess",
    "DataSharingAudit",
    "PatientSharingPreferences",
    "SharingStatistics"
]

# Model categories for easy access
USER_MODELS = [User, LoginAttempt, UserSession, UserNotification, UserActivityLog]
CONTENT_MODELS = [MoodEntry, DreamEntry, TherapyNote]
SHARING_MODELS = [ShareKey, ShareKeyAccessLog, TherapistNoteAccess, DataSharingAudit, PatientSharingPreferences, SharingStatistics]

# All models for migration and initialization
ALL_MODELS = USER_MODELS + CONTENT_MODELS + SHARING_MODELS
