"""
Models Package

Zentrale Imports für alle Datenbank-Modelle.
"""

# Chat Models
from .chat import (ChatAnalysis, ChatMessage, ChatSession, ChatTemplate,
                   ConversationFlow)
# Content Models
from .content_models import (  # Mood tracking; Dream journal; Therapy notes
    DreamEntry, DreamType, MoodEntry, MoodLevel, TherapyNote, TherapyNoteType,
    TherapyTechnique)
# Encrypted Models (Zero-Knowledge Architecture)
from .encrypted_models import (EncryptedChatMessage, EncryptedDreamEntry,
                               EncryptedMoodEntry, EncryptedTherapyNote,
                               UserEncryptionKey)
# Sharing Models
from .sharing_models import (  # Share keys; Access control; Preferences and settings
    DataSharingAudit, PatientSharingPreferences, ShareKey, ShareKeyAccessLog,
    ShareKeyStatus, SharePermission, SharingStatistics, TherapistNoteAccess)
# Training Models
from .training import (AIModelDeployment, ModelEvaluation, ModelVersion,
                       PredictionLog, TrainingDataSample, TrainingDataset,
                       TrainingJob)
# User Models
from .user_models import (LoginAttempt, User, UserActivityLog,
                          UserNotification, UserRole, UserSession)

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
    "AIModelDeployment",
    # Encrypted models
    "EncryptedMoodEntry",
    "EncryptedDreamEntry",
    "EncryptedTherapyNote",
    "EncryptedChatMessage",
    "UserEncryptionKey",
]

# Model categories for easy access
USER_MODELS = [User, LoginAttempt, UserSession, UserNotification, UserActivityLog]
CONTENT_MODELS = [MoodEntry, DreamEntry, TherapyNote]
SHARING_MODELS = [
    ShareKey,
    ShareKeyAccessLog,
    TherapistNoteAccess,
    DataSharingAudit,
    PatientSharingPreferences,
    SharingStatistics,
]
CHAT_MODELS = [ChatSession, ChatMessage, ChatAnalysis, ChatTemplate, ConversationFlow]
TRAINING_MODELS = [
    TrainingDataset,
    TrainingJob,
    ModelVersion,
    PredictionLog,
    ModelEvaluation,
    TrainingDataSample,
    AIModelDeployment,
]
ENCRYPTED_MODELS = [
    EncryptedMoodEntry,
    EncryptedDreamEntry,
    EncryptedTherapyNote,
    EncryptedChatMessage,
    UserEncryptionKey,
]

# All models for migration and initialization
ALL_MODELS = (
    USER_MODELS
    + CONTENT_MODELS
    + SHARING_MODELS
    + CHAT_MODELS
    + TRAINING_MODELS
    + ENCRYPTED_MODELS
)
