"""
Main API Router

Zentrale Routing-Konfiguration mit Versioning und Middleware.
"""

import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from src.api.v1.api import api_router as v1_router
from src.core.config import get_settings
from src.core.security import get_security_headers

logger = logging.getLogger(__name__)
settings = get_settings()

# Create main API router
api_router = APIRouter()

# Include v1 router
api_router.include_router(
    v1_router,
    prefix="/v1",
    responses={
        500: {"description": "Internal server error"},
        503: {"description": "Service unavailable"},
    },
)


# Root endpoint
@api_router.get("/", tags=["root"])
async def root():
    """API Root - Welcome Message"""
    return {
        "message": "Welcome to MindBridge AI Platform",
        "description": "Privacy-first mental health platform with AI-powered insights",
        "version": "1.0.0",
        "api_versions": {
            "v1": {"status": "stable", "base_url": "/api/v1", "documentation": "/docs"}
        },
        "features": [
            "🧠 AI-powered mood analysis",
            "📊 Advanced analytics",
            "🔒 End-to-end encryption",
            "🎯 Personalized insights",
            "🌍 Multi-language support",
        ],
        "health_check": "/health",
        "status": "operational",
        "timestamp": time.time(),
    }


# Health check endpoint
@api_router.get("/health", tags=["monitoring"])
async def health_check(request: Request):
    """
    Health Check Endpoint

    Prüft den Status der API und ihrer Abhängigkeiten.
    """
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "services": {
            "api": "operational",
            "database": "unknown",
            "ai_service": "unknown",
        },
    }

    # Check database connection
    try:
        from sqlalchemy import text

        from src.core.database import async_engine

        # Try to execute a simple query to check database connectivity
        async with async_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        health_status["services"]["database"] = "operational"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["services"]["database"] = "degraded"
        health_status["status"] = "degraded"

    # Check AI service
    try:
        ai_engine = request.app.state.ai_engine
        if ai_engine and ai_engine.is_initialized:
            health_status["services"]["ai_service"] = "operational"
        elif ai_engine and not ai_engine.is_initialized:
            health_status["services"]["ai_service"] = "not_initialized"
            health_status["status"] = "degraded"
        else:
            health_status["services"]["ai_service"] = "unavailable"
            health_status["status"] = "degraded"
    except Exception as e:
        logger.error(f"AI service health check failed: {e}")
        health_status["services"]["ai_service"] = "error"
        health_status["status"] = "degraded"

    return health_status


# Metrics endpoint
@api_router.get("/metrics", tags=["monitoring"])
async def metrics():
    """
    API Metrics

    Gibt grundlegende Metriken über die API zurück.
    """
    return {
        "uptime": time.time(),
        "requests": {
            "total": 0,  # TODO: Implement actual metrics
            "success": 0,
            "errors": 0,
        },
        "performance": {
            "average_response_time": 0.0,
            "p95_response_time": 0.0,
            "p99_response_time": 0.0,
        },
        "resources": {"cpu_usage": 0.0, "memory_usage": 0.0, "active_connections": 0},
        "timestamp": time.time(),
    }


# Status endpoint
@api_router.get("/status", tags=["monitoring"])
async def status():
    """
    System Status

    Detaillierte Systeminformationen für Monitoring.
    """
    return {
        "system": "operational",
        "api_version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "debug_mode": settings.DEBUG,
        "components": {
            "authentication": "operational",
            "database": "operational",
            "ai_engine": "operational",
            "storage": "operational",
            "cache": "operational",
        },
        "maintenance": {"scheduled": False, "next_window": None, "message": None},
        "timestamp": time.time(),
    }


# API versioning info
@api_router.get("/versions", tags=["versioning"])
async def api_versions():
    """Available API Versions"""
    return {
        "current_version": "v1",
        "supported_versions": {
            "v1": {
                "status": "stable",
                "release_date": "2024-01-01",
                "deprecation_date": None,
                "base_url": "/api/v1",
                "changelog": [
                    "Initial release with core features",
                    "Mood tracking and analysis",
                    "AI-powered insights",
                    "User authentication",
                ],
            }
        },
        "latest_updates": [
            {
                "version": "v1.0.0",
                "date": "2024-01-01",
                "changes": [
                    "Core API endpoints",
                    "Authentication system",
                    "Basic mood tracking",
                ],
            }
        ],
        "deprecation_policy": {
            "notice_period": "6 months",
            "support_period": "12 months after deprecation",
            "migration_guide": "/docs/migration",
        },
    }


# Development endpoints (only in dev/staging)
if settings.ENVIRONMENT in ["development", "staging"]:

    @api_router.get("/dev/info", tags=["development"])
    async def dev_info():
        """Development Information (dev only)"""
        return {
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
            "database_configured": bool(settings.DATABASE_URL),
            "ai_configured": True,
            "security": {
                "jwt_configured": bool(settings.SECRET_KEY),
                "cors_enabled": True,
                "https_only": settings.ENVIRONMENT == "production",
            },
        }

    @api_router.get("/dev/test-error", tags=["development"])
    async def test_error():
        """Test error handling (dev only)"""
        raise HTTPException(status_code=500, detail="Test error for development")

    @api_router.get("/dev/config", tags=["development"])
    async def dev_config():
        """Development configuration (dev only)"""
        return {
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
            "database_url": (
                settings.DATABASE_URL[:20] + "..." if settings.DATABASE_URL else None
            ),
            "ai_enabled": True,
            "cors_enabled": True,
        }
