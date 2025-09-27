"""
Application Configuration

Zentrale FastAPI-App Konfiguration mit Middleware, CORS und Startup/Shutdown Events.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import time
import os

from src.core.config import get_settings
from src.core.database import init_database, close_database
from src.api import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    
    # Startup
    logger.info("🚀 Starting MindBridge AI Platform...")
    
    try:
        # Initialize database
        await init_database()
        logger.info("✅ Database initialized")
        
        # Initialize AI Engine (if available)
        try:
            # This would initialize your custom AI engine
            app.state.ai_engine = None  # Placeholder for AI engine
            logger.info("✅ AI Engine initialized")
        except Exception as e:
            logger.warning(f"⚠️ AI Engine initialization failed: {e}")
            app.state.ai_engine = None
        
        # Create necessary directories
        os.makedirs("data/uploads", exist_ok=True)
        os.makedirs("data/licenses", exist_ok=True)
        os.makedirs("data/exports", exist_ok=True)
        logger.info("✅ Directories created")
        
        logger.info("🎉 MindBridge AI Platform started successfully!")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down MindBridge AI Platform...")
    
    try:
        # Close database connections
        await close_database()
        logger.info("✅ Database connections closed")
        
        # Cleanup AI Engine
        if hasattr(app.state, 'ai_engine') and app.state.ai_engine:
            # Cleanup AI engine if needed
            pass
        
        logger.info("👋 MindBridge AI Platform shut down gracefully")
        
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")

def create_application() -> FastAPI:
    """Create and configure FastAPI application"""
    
    # Create FastAPI app with lifespan
    app = FastAPI(
        title="MindBridge AI Platform",
        description="""
        🧠 **AI-powered Mental Health Platform**
        
        MindBridge is a privacy-first mental health platform that empowers users with:
        
        - **AI-Enhanced Mood Tracking** - Intelligent insights into your emotional patterns
        - **Dream Journal & Analysis** - AI-powered dream interpretation and symbolism
        - **Structured Therapy Tools** - CBT/DBT worksheets and self-reflection guides
        - **Secure Data Sharing** - GDPR-compliant sharing with therapists (optional)
        - **Advanced Analytics** - Pattern recognition and personalized recommendations
        
        ## 🛡️ Privacy-First Design
        
        - **Patient Control**: You own your data and decide what to share
        - **GDPR Compliant**: Full data portability and right to deletion
        - **End-to-End Security**: Enterprise-grade encryption and security
        - **No Vendor Lock-in**: Export your data anytime
        
        ## 🎯 Self-Help Focused
        
        - **No Therapist Required**: All features work independently
        - **AI-Powered Insights**: Get intelligent feedback without human intervention
        - **Structured Tools**: Evidence-based therapy techniques (CBT, DBT, Mindfulness)
        - **Optional Collaboration**: Invite therapists when ready
        
        ## 🚀 Getting Started
        
        1. **Register** as a patient (no verification needed)
        2. **Create** your first mood entry or dream journal entry
        3. **Explore** AI-powered insights and patterns
        4. **Optional**: Invite a therapist to share specific data
        
        ## 🔗 Useful Links
        
        - [Privacy Policy](https://mindbridge.app/privacy)
        - [Terms of Service](https://mindbridge.app/terms)
        - [Support](mailto:support@mindbridge.app)
        """,
        version="1.0.0",
        contact={
            "name": "MindBridge Support",
            "email": "support@mindbridge.app",
            "url": "https://mindbridge.app/support"
        },
        license_info={
            "name": "Proprietary",
            "url": "https://mindbridge.app/license"
        },
        terms_of_service="https://mindbridge.app/terms",
        openapi_tags=[
            {
                "name": "users",
                "description": "User registration, authentication, and profile management"
            },
            {
                "name": "mood-tracking", 
                "description": "Mood entries with AI-powered analysis and insights"
            },
            {
                "name": "dream-journal",
                "description": "Dream logging with AI interpretation and symbol analysis"
            },
            {
                "name": "therapy-notes",
                "description": "Structured therapy tools, CBT worksheets, and self-reflection"
            },
            {
                "name": "data-sharing",
                "description": "Secure, GDPR-compliant data sharing with therapists"
            },
            {
                "name": "analytics",
                "description": "AI-powered insights, trends, and pattern recognition"
            },
            {
                "name": "health",
                "description": "System health and monitoring endpoints"
            }
        ],
        lifespan=lifespan,
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
        openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS if hasattr(settings, 'ALLOWED_HOSTS') else ["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Process-Time", "X-Request-ID"]
    )
    
    # Add trusted host middleware for production
    if settings.ENVIRONMENT == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS if hasattr(settings, 'ALLOWED_HOSTS') else ["mindbridge.app", "*.mindbridge.app"]
        )
    
    # Add GZip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Add custom middleware for request ID and timing
    @app.middleware("http")
    async def add_request_metadata(request: Request, call_next):
        """Add request ID and timing metadata"""
        
        # Generate unique request ID
        request_id = f"req_{int(time.time() * 1000)}"
        request.state.request_id = request_id
        
        # Add request start time
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Add response headers
        process_time = time.time() - start_time
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.3f}"
        
        return response
    
    # Mount static files (for uploaded content)
    if os.path.exists("data/static"):
        app.mount("/static", StaticFiles(directory="data/static"), name="static")
    
    # Include API router
    app.include_router(api_router, prefix="/api")
    
    # Root endpoint
    @app.get("/", tags=["root"])
    async def root():
        """Welcome to MindBridge AI Platform"""
        return {
            "message": "🧠 Welcome to MindBridge AI Platform",
            "tagline": "Privacy-first mental health with AI-powered insights",
            "version": "1.0.0",
            "status": "operational",
            "features": [
                "🎯 Self-help focused design",
                "🤖 AI-powered mood analysis", 
                "🌙 Intelligent dream interpretation",
                "📝 Structured therapy tools (CBT/DBT)",
                "🔒 Optional secure therapist sharing",
                "📊 Advanced pattern analytics",
                "🛡️ Complete GDPR compliance"
            ],
            "getting_started": {
                "patients": {
                    "1": "Register: POST /api/v1/users/register/patient",
                    "2": "Login: POST /api/v1/users/login",
                    "3": "Start tracking: POST /api/v1/mood/ or /api/v1/dreams/"
                },
                "therapists": {
                    "1": "Register: POST /api/v1/users/register/therapist",
                    "2": "Wait for verification (1-3 business days)",
                    "3": "Accept patient share keys: POST /api/v1/sharing/accept-share-key"
                }
            },
            "documentation": {
                "api_docs": "/docs",
                "redoc": "/redoc", 
                "health_check": "/api/health",
                "api_info": "/api/v1/info"
            },
            "support": {
                "email": "support@mindbridge.app",
                "privacy": "privacy@mindbridge.app",
                "security": "security@mindbridge.app"
            },
            "legal": {
                "privacy_policy": "https://mindbridge.app/privacy",
                "terms_of_service": "https://mindbridge.app/terms",
                "gdpr_rights": "https://mindbridge.app/gdpr"
            }
        }
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler for unhandled errors"""
        
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        logger.error(f"Unhandled exception [{request_id}]: {str(exc)}", exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Internal server error",
                "message": "An unexpected error occurred. Please try again later.",
                "request_id": request_id,
                "timestamp": time.time(),
                "support": {
                    "email": "support@mindbridge.app",
                    "message": "Please include the request_id when contacting support"
                }
            }
        )
    
    # Add custom headers to all responses
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        """Add security headers to all responses"""
        
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # HSTS for production
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # API metadata
        response.headers["X-API-Version"] = "1.0.0"
        response.headers["X-Platform"] = "MindBridge-AI"
        
        return response
    
    logger.info("🏗️ FastAPI application configured successfully")
    return app

# Create the application instance
app = create_application()

# Health check for load balancers
@app.get("/ping")
async def ping():
    """Simple ping endpoint for load balancers"""
    return {"status": "ok", "timestamp": time.time()}

# Robots.txt for web crawlers
@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots_txt():
    """Robots.txt for web crawlers"""
    return """User-agent: *
Disallow: /api/
Disallow: /docs/
Disallow: /redoc/
Allow: /

Sitemap: https://mindbridge.app/sitemap.xml
"""

if __name__ == "__main__":
    import uvicorn
    
    # Development server configuration
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False,
        log_level="info",
        access_log=True
    )
