"""
AI & Core Schemas

Zentrale Import-Datei für alle Pydantic Schemas.
Diese Datei re-exportiert alle Schemas für einfachen Import.
"""

# AI Training
from src.schemas.ai_training import (ModelEvaluationRequest,
                                     ModelEvaluationResponse,
                                     ModelTrainingRequest,
                                     ModelTrainingResponse, ModelType,
                                     ModelVersionResponse,
                                     TrainingDatasetCreate,
                                     TrainingDatasetResponse,
                                     TrainingDataUpload, TrainingJobStatus,
                                     TrainingMetrics)
# Analytics
from src.schemas.analytics import (AnalyticsRequest, DreamAnalyticsResponse,
                                   MoodAnalyticsResponse,
                                   TherapyProgressResponse)
# Common Responses
from src.schemas.common import (ErrorResponse, PaginatedResponse,
                                PaginationParams, SuccessResponse)
# Dream Entries
from src.schemas.dream import (DreamEntryCreate, DreamEntryResponse,
                               DreamEntryUpdate, DreamType)
# Export
from src.schemas.export import DataExportRequest, DataExportResponse
# Mood Entries
from src.schemas.mood import (MoodEntryCreate, MoodEntryResponse,
                              MoodEntryUpdate)
# Sharing
from src.schemas.sharing import (PatientOverview, ShareKeyCreate,
                                 ShareKeyResponse, SharePermission,
                                 TherapistAccessRequest)
# Therapy Notes
from src.schemas.therapy import (TherapyNoteCreate, TherapyNoteResponse,
                                 TherapyNoteType, TherapyNoteUpdate,
                                 TherapyTechnique)
# User & Authentication
from src.schemas.user import (PasswordChange, TherapistRegistration,
                              TherapistVerification, TokenResponse, UserLogin,
                              UserProfileResponse, UserProfileUpdate,
                              UserRegistration, UserRole)

# Re-export all für * imports
__all__ = [
    # User & Authentication
    "UserRole",
    "UserRegistration",
    "TherapistRegistration",
    "TherapistVerification",
    "UserLogin",
    "PasswordChange",
    "UserProfileUpdate",
    "UserProfileResponse",
    "TokenResponse",
    # Mood Entries
    "MoodEntryCreate",
    "MoodEntryUpdate",
    "MoodEntryResponse",
    # Dream Entries
    "DreamType",
    "DreamEntryCreate",
    "DreamEntryUpdate",
    "DreamEntryResponse",
    # Therapy Notes
    "TherapyNoteType",
    "TherapyTechnique",
    "TherapyNoteCreate",
    "TherapyNoteUpdate",
    "TherapyNoteResponse",
    # AI Training
    "TrainingJobStatus",
    "ModelType",
    "TrainingDataUpload",
    "TrainingDatasetCreate",
    "TrainingDatasetResponse",
    "ModelTrainingRequest",
    "ModelTrainingResponse",
    "TrainingMetrics",
    "ModelVersionResponse",
    "ModelEvaluationRequest",
    "ModelEvaluationResponse",
    # Sharing
    "SharePermission",
    "ShareKeyCreate",
    "TherapistAccessRequest",
    "ShareKeyResponse",
    "PatientOverview",
    # Analytics
    "AnalyticsRequest",
    "MoodAnalyticsResponse",
    "DreamAnalyticsResponse",
    "TherapyProgressResponse",
    # Export
    "DataExportRequest",
    "DataExportResponse",
    # Common
    "SuccessResponse",
    "ErrorResponse",
    "PaginationParams",
    "PaginatedResponse",
]
