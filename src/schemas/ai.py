"""
AI & Core Schemas

Zentrale Import-Datei für alle Pydantic Schemas.
Diese Datei re-exportiert alle Schemas für einfachen Import.
"""

# User & Authentication
from src.schemas.user import (
    UserRole,
    UserRegistration,
    TherapistRegistration,
    TherapistVerification,
    UserLogin,
    PasswordChange,
    UserProfileUpdate,
    UserProfileResponse,
    TokenResponse
)

# Mood Entries
from src.schemas.mood import (
    MoodEntryCreate,
    MoodEntryUpdate,
    MoodEntryResponse
)

# Dream Entries
from src.schemas.dream import (
    DreamType,
    DreamEntryCreate,
    DreamEntryUpdate,
    DreamEntryResponse
)

# Therapy Notes
from src.schemas.therapy import (
    TherapyNoteType,
    TherapyTechnique,
    TherapyNoteCreate,
    TherapyNoteUpdate,
    TherapyNoteResponse
)

# AI Training
from src.schemas.ai_training import (
    TrainingJobStatus,
    ModelType,
    TrainingDataUpload,
    TrainingDatasetCreate,
    TrainingDatasetResponse,
    ModelTrainingRequest,
    ModelTrainingResponse,
    TrainingMetrics,
    ModelVersionResponse,
    ModelEvaluationRequest,
    ModelEvaluationResponse
)

# Sharing
from src.schemas.sharing import (
    SharePermission,
    ShareKeyCreate,
    TherapistAccessRequest,
    ShareKeyResponse,
    PatientOverview
)

# Analytics
from src.schemas.analytics import (
    AnalyticsRequest,
    MoodAnalyticsResponse,
    DreamAnalyticsResponse,
    TherapyProgressResponse
)

# Export
from src.schemas.export import (
    DataExportRequest,
    DataExportResponse
)

# Common Responses
from src.schemas.common import (
    SuccessResponse,
    ErrorResponse,
    PaginationParams,
    PaginatedResponse
)

# Re-export all für * imports
__all__ = [
    # User & Authentication
    'UserRole',
    'UserRegistration',
    'TherapistRegistration',
    'TherapistVerification',
    'UserLogin',
    'PasswordChange',
    'UserProfileUpdate',
    'UserProfileResponse',
    'TokenResponse',
    
    # Mood Entries
    'MoodEntryCreate',
    'MoodEntryUpdate',
    'MoodEntryResponse',
    
    # Dream Entries
    'DreamType',
    'DreamEntryCreate',
    'DreamEntryUpdate',
    'DreamEntryResponse',
    
    # Therapy Notes
    'TherapyNoteType',
    'TherapyTechnique',
    'TherapyNoteCreate',
    'TherapyNoteUpdate',
    'TherapyNoteResponse',
    
    # AI Training
    'TrainingJobStatus',
    'ModelType',
    'TrainingDataUpload',
    'TrainingDatasetCreate',
    'TrainingDatasetResponse',
    'ModelTrainingRequest',
    'ModelTrainingResponse',
    'TrainingMetrics',
    'ModelVersionResponse',
    'ModelEvaluationRequest',
    'ModelEvaluationResponse',
    
    # Sharing
    'SharePermission',
    'ShareKeyCreate',
    'TherapistAccessRequest',
    'ShareKeyResponse',
    'PatientOverview',
    
    # Analytics
    'AnalyticsRequest',
    'MoodAnalyticsResponse',
    'DreamAnalyticsResponse',
    'TherapyProgressResponse',
    
    # Export
    'DataExportRequest',
    'DataExportResponse',
    
    # Common
    'SuccessResponse',
    'ErrorResponse',
    'PaginationParams',
    'PaginatedResponse'
]
