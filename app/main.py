"""
MindBridge AI Platform - Main Application

Enterprise-Ready FastAPI application with modular architecture.
Automatically loads and registers modules from app/modules/
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.core.config import get_settings
from app.core.database import close_database, init_database
from app.core.module_loader import init_modules
from app.core.rate_limiting import limiter, rate_limit_exceeded_handler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events

    Startup:
    - Initialize database
    - Load and register modules
    - Initialize AI Engine
    - Create necessary directories

    Shutdown:
    - Close database connections
    - Cleanup resources
    """

    # ========================================================================
    # STARTUP
    # ========================================================================
    logger.info("🚀 Starting MindBridge AI Platform...")

    try:
        # Initialize database
        logger.info("📦 Initializing database...")
        await init_database()
        logger.info("✅ Database initialized")

        # Load and register modules
        logger.info("🔌 Loading modules...")
        module_loader = init_modules(app)
        app.state.module_loader = module_loader
        logger.info(f"✅ Loaded {len(module_loader.modules)} modules")

        # Initialize AI Engine (if available)
        try:
            from app.ai.engine import AIEngine

            ai_engine = AIEngine()
            await ai_engine.initialize()
            app.state.ai_engine = ai_engine
            logger.info("✅ AI Engine initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️  AI Engine initialization failed: {e}")
            logger.warning("⚠️  AI features will be disabled. Train models first.")
            # Create engine but don't initialize to allow training endpoints
            from app.ai.engine import AIEngine
            app.state.ai_engine = AIEngine()
            app.state.ai_engine.is_initialized = False

        # Create necessary directories
        directories = [
            "data/uploads",
            "data/licenses",
            "data/exports",
            "data/models",
            "data/static",
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
        logger.info("✅ Directories created")

        logger.info("🎉 MindBridge AI Platform started successfully!")
        logger.info(f"📊 Environment: {settings.ENVIRONMENT}")
        logger.info(f"🌐 Host: {settings.HOST}:{settings.PORT}")

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}", exc_info=True)
        raise

    yield

    # ========================================================================
    # SHUTDOWN
    # ========================================================================
    logger.info("🛑 Shutting down MindBridge AI Platform...")

    try:
        # Close database connections
        await close_database()
        logger.info("✅ Database connections closed")

        # Cleanup AI Engine
        if hasattr(app.state, "ai_engine") and app.state.ai_engine:
            if app.state.ai_engine.is_initialized:
                await app.state.ai_engine.cleanup()
                logger.info("✅ AI Engine cleaned up")

        logger.info("👋 MindBridge AI Platform shut down gracefully")

    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")


def create_application() -> FastAPI:
    """
    Create and configure FastAPI application

    Returns:
        Configured FastAPI application instance
    """

    # Create FastAPI app with lifespan
    app = FastAPI(
        title="MindBridge AI Platform",
        description="""
        🧠 **AI-powered Mental Health Platform**

        **Enterprise-Ready Modular Architecture**

        ## Features

        - **Modular Design**: Plug-and-play module system
        - **AI-Powered**: In-house PyTorch models (no external APIs)
        - **Privacy-First**: GDPR compliant, patient-controlled data
        - **Scalable**: Designed for enterprise deployment
        - **Extensible**: Easy to add new modules

        ## Available Modules

        Modules are automatically loaded from `/app/modules/`.
        Check `/api/v1/modules` endpoint for active modules.

        ## Documentation

        - [API Docs](/docs)
        - [Module Guide](/docs/MODULE_GUIDE.md)
        - [Installation Guide](/docs/INSTALLATION.md)
        """,
        version="2.0.0",
        contact={
            "name": "MindBridge Support",
            "email": "support@mindbridge.app",
            "url": "https://mindbridge.app/support",
        },
        license_info={
            "name": "Proprietary",
            "url": "https://mindbridge.app/license"
        },
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ========================================================================
    # MIDDLEWARE
    # ========================================================================

    # CORS Middleware
    allowed_origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS != "*" else ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # GZip Compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Rate Limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    # ========================================================================
    # HEALTH CHECK & MODULE INFO
    # ========================================================================

    @app.get("/health", tags=["health"])
    async def health_check():
        """
        Health check endpoint

        Returns:
            Health status and system info
        """
        return {
            "status": "healthy",
            "version": "2.0.0",
            "environment": settings.ENVIRONMENT,
            "api": "MindBridge AI Platform",
            "architecture": "modular",
        }

    @app.get("/ping", tags=["health"])
    async def ping():
        """
        Docker healthcheck endpoint

        Simple ping endpoint for container health checks.
        Returns minimal response for fast health verification.
        """
        return {"status": "ok"}

    @app.get("/api/v1/modules", tags=["system"])
    async def list_modules(request: Request):
        """
        List all loaded modules

        Returns:
            List of loaded modules with metadata
        """
        if hasattr(request.app.state, "module_loader"):
            module_loader = request.app.state.module_loader
            return {
                "modules": module_loader.get_modules_info(),
                "total": len(module_loader.modules),
                "loaded": module_loader.loaded_count,
                "failed": module_loader.failed_count,
            }
        return {"modules": [], "total": 0, "loaded": 0, "failed": 0}

    # ========================================================================
    # ERROR HANDLERS
    # ========================================================================

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler"""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred" if settings.ENVIRONMENT == "production" else str(exc),
            },
        )

    logger.info("✅ FastAPI application created successfully")

    return app


# Create application instance
app = create_application()


# ============================================================================
# DEVELOPMENT SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning",
    )
