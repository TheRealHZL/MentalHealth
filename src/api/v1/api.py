"""
API Router - Version 1

Zentrale Routing-Konfiguration für alle v1 API-Endpoints.
"""

from fastapi import APIRouter

from src.api.v1.endpoints import (
    users,
    mood,
    dreams,
    thoughts,  # therapy notes
    sharing,
    analytics,
    ai_training,  # AI training endpoints
    encryption  # Client-side encryption endpoints
)

# Create main v1 router
api_router = APIRouter()

# Include all endpoint routers with their prefixes
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Not found"},
        429: {"description": "Too many requests"}
    }
)

api_router.include_router(
    mood.router,
    prefix="/mood",
    tags=["mood-tracking"],
    dependencies=[],  # Add global dependencies if needed
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"}
    }
)

api_router.include_router(
    dreams.router,
    prefix="/dreams",
    tags=["dream-journal"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"}
    }
)

api_router.include_router(
    thoughts.router,
    prefix="/therapy",
    tags=["therapy-notes"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"}
    }
)

api_router.include_router(
    sharing.router,
    prefix="/sharing",
    tags=["data-sharing"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"}
    }
)

api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["analytics"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"}
    }
)

api_router.include_router(
    ai_training.router,
    prefix="/ai-training",
    tags=["ai-training"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - Admin/Therapist access required"},
        404: {"description": "Not found"},
        429: {"description": "Too many requests"}
    }
)

api_router.include_router(
    encryption.router,
    # prefix already set in encryption.py as "/encryption"
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Not found"}
    }
)

# Health check endpoint
@api_router.get("/health", tags=["health"])
async def health_check():
    """API Health Check"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "api": "MindBridge AI Platform",
        "features": [
            "mood-tracking",
            "dream-journal", 
            "therapy-notes",
            "ai-analysis",
            "secure-sharing",
            "ai-training"
        ]
    }

# API Info endpoint
@api_router.get("/info", tags=["info"])
async def api_info():
    """API Information"""
    return {
        "api_name": "MindBridge AI API",
        "version": "1.0.0",
        "description": "AI-powered mental health platform with privacy-first approach",
        "features": {
            "mood_tracking": {
                "description": "Comprehensive mood and wellness tracking",
                "ai_powered": True,
                "endpoints": ["/mood"]
            },
            "dream_journal": {
                "description": "Dream analysis and interpretation",
                "ai_powered": True,
                "endpoints": ["/dreams"]
            },
            "therapy_tools": {
                "description": "Structured therapy worksheets and self-reflection",
                "ai_powered": True,
                "endpoints": ["/therapy"]
            },
            "secure_sharing": {
                "description": "GDPR-compliant data sharing with therapists",
                "ai_powered": False,
                "endpoints": ["/sharing"]
            },
            "analytics": {
                "description": "AI-powered insights and pattern recognition",
                "ai_powered": True,
                "endpoints": ["/analytics"]
            },
            "ai_training": {
                "description": "AI model training and dataset management",
                "ai_powered": True,
                "endpoints": ["/ai-training"],
                "access_level": "admin_therapist_only",
                "features": [
                    "Upload training data in JSON format",
                    "Train custom AI models",
                    "Model evaluation and testing",
                    "Model deployment management",
                    "Performance monitoring"
                ]
            }
        },
        "authentication": "JWT Bearer Token",
        "rate_limiting": "Enabled",
        "privacy": {
            "gdpr_compliant": True,
            "data_encryption": True,
            "patient_controlled": True
        },
        "ai_training_info": {
            "supported_formats": ["JSON", "CSV", "JSONL"],
            "supported_model_types": [
                "mood_classifier",
                "dream_interpreter", 
                "sentiment_analyzer",
                "risk_assessor",
                "recommendation_engine"
            ],
            "training_data_examples": {
                "mood_analysis": {
                    "input": {
                        "mood_score": 7,
                        "activities": ["work", "exercise"],
                        "notes": "Good day with productive work"
                    },
                    "output": {
                        "analysis": "Positive mood with healthy activities",
                        "recommendations": ["Continue exercise routine"],
                        "mood_category": "good"
                    }
                },
                "dream_analysis": {
                    "input": {
                        "description": "Flying over mountains",
                        "symbols": ["flying", "mountains"],
                        "emotions": ["freedom", "joy"]
                    },
                    "output": {
                        "interpretation": "Desire for freedom and transcendence",
                        "symbol_meanings": {
                            "flying": "freedom, escape",
                            "mountains": "challenges, goals"
                        }
                    }
                }
            },
            "upload_limits": {
                "max_samples_per_batch": 10000,
                "max_file_size_mb": 100,
                "supported_file_types": ["json", "csv", "jsonl"]
            }
        }
    }
