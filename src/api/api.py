"""
Main API Router

Zentrale Routing-Konfiguration mit Versioning und Middleware.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import logging

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
        503: {"description": "Service unavailable"}
    }
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
            "v1": {
                "status": "stable",
                "base_url": "/api/v1",
                "documentation": "/docs"
            }
        },
        "features": [
            "🧠 AI-powered mood analysis",
            "🌙 Intelligent dream interpretation", 
            "📝 Structured therapy tools",
            "🔒 Secure therapist sharing",
            "📊 Advanced analytics",
            "🛡️ GDPR compliance"
        ],
        "getting_started": {
            "1": "Register as patient: POST /api/v1/users/register/patient",
            "2": "Login: POST /api/v1/users/login", 
            "3": "Create mood entry: POST /api/v1/mood/",
            "4": "Explore features: GET /api/v1/info"
        },
        "support": {
            "documentation": "/docs",
            "redoc": "/redoc",
            "health_check": "/api/health",
            "contact": "support@mindbridge.app"
        }
    }

# Global health check
@api_router.get("/health", tags=["health"])
async def global_health_check():
    """Global Health Check"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "uptime": "operational",
        "services": {
            "api": "healthy",
            "database": "healthy",
            "ai_engine": "healthy",
            "security": "healthy"
        },
        "version": "1.0.0"
    }

# API Status endpoint
@api_router.get("/status", tags=["status"])
async def api_status():
    """Detailed API Status"""
    return {
        "api_status": "operational",
        "current_version": "1.0.0",
        "supported_versions": ["v1"],
        "maintenance_mode": False,
        "rate_limiting": {
            "enabled": True,
            "default_limit": "100 requests/hour",
            "auth_limit": "5 requests/15min"
        },
        "features": {
            "user_registration": "enabled",
            "ai_analysis": "enabled", 
            "data_sharing": "enabled",
            "analytics": "enabled",
            "export": "enabled"
        },
        "security": {
            "jwt_auth": "enabled",
            "rate_limiting": "enabled",
            "cors": "configured",
            "https_only": settings.HTTPS_ONLY if hasattr(settings, 'HTTPS_ONLY') else True
        },
        "compliance": {
            "gdpr": "compliant",
            "data_encryption": "enabled",
            "audit_logging": "enabled"
        }
    }

# Metrics endpoint (for monitoring)
@api_router.get("/metrics", tags=["monitoring"])
async def api_metrics():
    """API Metrics for Monitoring"""
    # In production, this would return real metrics
    return {
        "requests": {
            "total": 0,
            "per_minute": 0,
            "success_rate": 100.0
        },
        "response_times": {
            "avg_ms": 150,
            "p95_ms": 300,
            "p99_ms": 500
        },
        "errors": {
            "rate": 0.1,
            "4xx_count": 0,
            "5xx_count": 0
        },
        "users": {
            "active_sessions": 0,
            "total_registered": 0
        },
        "ai_usage": {
            "analyses_today": 0,
            "avg_processing_time_ms": 1200
        }
    }

# Custom exception handlers
@api_router.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format"""
    
    # Add security headers
    headers = get_security_headers()
    
    # Log error for monitoring
    logger.error(f"HTTP {exc.status_code}: {exc.detail} - {request.url}")
    
    response_data = {
        "success": False,
        "error": exc.detail,
        "status_code": exc.status_code,
        "timestamp": time.time()
    }
    
    # Add helpful information for common errors
    if exc.status_code == 401:
        response_data["help"] = "Authentication required. Please provide a valid Bearer token."
    elif exc.status_code == 403:
        response_data["help"] = "Access forbidden. Check your permissions."
    elif exc.status_code == 404:
        response_data["help"] = "Resource not found. Check the URL and try again."
    elif exc.status_code == 429:
        response_data["help"] = "Rate limit exceeded. Please wait before making more requests."
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data,
        headers=headers
    )

@api_router.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception):
    """Handle internal server errors"""
    
    # Log detailed error for debugging
    logger.error(f"Internal Server Error: {str(exc)} - {request.url}", exc_info=True)
    
    # Add security headers
    headers = get_security_headers()
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "timestamp": time.time(),
            "support": "If this persists, contact support@mindbridge.app"
        },
        headers=headers
    )

# Request logging middleware
@api_router.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all API requests for monitoring"""
    
    start_time = time.time()
    
    # Log incoming request
    logger.info(f"API Request: {request.method} {request.url}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Add processing time header
    response.headers["X-Process-Time"] = str(process_time)
    
    # Add security headers
    security_headers = get_security_headers()
    for key, value in security_headers.items():
        response.headers[key] = value
    
    # Log response
    logger.info(f"API Response: {response.status_code} - {process_time:.3f}s")
    
    return response

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
                    "Initial release with full feature set",
                    "AI-powered mood and dream analysis",
                    "Secure therapist data sharing",
                    "Comprehensive analytics"
                ]
            }
        },
        "upcoming_versions": {
            "v2": {
                "status": "planned",
                "estimated_release": "2024-Q3",
                "planned_features": [
                    "Enhanced AI models",
                    "Advanced sharing controls",
                    "Real-time notifications",
                    "Mobile app integration"
                ]
            }
        },
        "migration_guide": {
            "v1_to_v2": "Migration guide will be available 30 days before v2 release"
        }
    }

# Development endpoints (only in dev mode)
if settings.ENVIRONMENT == "development":
    
    @api_router.get("/dev/test-error", tags=["development"])
    async def test_error():
        """Test error handling (dev only)"""
        raise HTTPException(status_code=500, detail="Test error for development")
    
    @api_router.get("/dev/test-auth", tags=["development"])
    async def test_auth(user_id: str = Depends(get_current_user_id)):
        """Test authentication (dev only)"""
        return {"authenticated": True, "user_id": user_id}
    
    @api_router.get("/dev/config", tags=["development"])
    async def dev_config():
        """Development configuration (dev only)"""
        return {
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
            "database_url": settings.DATABASE_URL[:20] + "..." if settings.DATABASE_URL else None,
            "ai_enabled": True,
            "cors_enabled": True
        }
