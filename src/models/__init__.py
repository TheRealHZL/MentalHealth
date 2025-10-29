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

# Chat Models
from .chat import (
    ChatSession,
    ChatMessage,
    ChatAnalysis,
    ChatTemplate,
    ConversationFlow
)

# Training Models
from .training import (
    TrainingDataset,
    TrainingJob,
    ModelVersion,
    PredictionLog,
    ModelEvaluation,
    TrainingDataSample,
    AIModelDeployment
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
    "SharingStatistics",
    
    # Chat models
    "ChatSession",
    "ChatMessage",
    "ChatAnalysis",
    "ChatTemplate",
    "ConversationFlow",
    
    # Training models
    "TrainingDataset",
    "TrainingJob",
    "ModelVersion",
    "PredictionLog",
    "ModelEvaluation",
    "TrainingDataSample",
    "AIModelDeployment"
]

# Model categories for easy access
USER_MODELS = [User, LoginAttempt, UserSession, UserNotification, UserActivityLog]
CONTENT_MODELS = [MoodEntry, DreamEntry, TherapyNote]
SHARING_MODELS = [ShareKey, ShareKeyAccessLog, TherapistNoteAccess, DataSharingAudit, PatientSharingPreferences, SharingStatistics]
CHAT_MODELS = [ChatSession, ChatMessage, ChatAnalysis, ChatTemplate, ConversationFlow]
TRAINING_MODELS = [TrainingDataset, TrainingJob, ModelVersion, PredictionLog, ModelEvaluation, TrainingDataSample, AIModelDeployment]

# All models for migration and initialization
ALL_MODELS = USER_MODELS + CONTENT_MODELS + SHARING_MODELS + CHAT_MODELS + TRAINING_MODELS
