"""
Main API Router for MindBridge v1

Sammelt alle API-Endpunkte und konfiguriert Routing.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import Dict, Any

from src.core.security import get_current_user_id, require_admin
from src.api.v1.endpoints import auth, mood, dreams, thoughts, feedback, ai, analytics, admin, ai_training

# Create main API router
api_router = APIRouter()

# Security
security = HTTPBearer()

# Health check endpoint (no auth required)
@api_router.get("/health", tags=["health"])
async def health_check() -> Dict[str, Any]:
    """
    API Health Check
    """
    return {
        "status": "healthy",
        "version": "2.0.0",
        "api": "mindbridge",
        "custom_ai": True,
        "endpoints": {
            "auth": "/auth",
            "mood": "/mood", 
            "dreams": "/dreams",
            "thoughts": "/thoughts",
            "feedback": "/feedback",
            "ai": "/ai",
            "analytics": "/analytics"
        }
    }

# Include all endpoint routers
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"]
)

api_router.include_router(
    mood.router,
    prefix="/mood",
    tags=["mood-tracking"],
    dependencies=[Depends(get_current_user_id)]
)

api_router.include_router(
    dreams.router,
    prefix="/dreams", 
    tags=["dream-journal"],
    dependencies=[Depends(get_current_user_id)]
)

api_router.include_router(
    thoughts.router,
    prefix="/thoughts",
    tags=["thought-records"],
    dependencies=[Depends(get_current_user_id)]
)

api_router.include_router(
    feedback.router,
    prefix="/feedback",
    tags=["feedback"],
    dependencies=[Depends(get_current_user_id)]
)

api_router.include_router(
    ai.router,
    prefix="/ai",
    tags=["artificial-intelligence"]
)

api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["analytics"],
    dependencies=[Depends(get_current_user_id)]
)

api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)]
)

api_router.include_router(
    ai_training.router,
    prefix="/ai/training",
    tags=["ai-training"]
)

# Global error handler for the API
@api_router.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Global HTTP exception handler"""
    return {
        "error": True,
        "message": exc.detail,
        "status_code": exc.status_code
    }
