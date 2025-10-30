"""
Rate Limiting Configuration

Implements API rate limiting to prevent:
- Brute force password attacks
- Account enumeration
- DoS attacks
- API abuse

Uses slowapi for rate limiting with Redis backend for distributed rate limiting.
"""

import json
from typing import Optional
from fastapi import Request, Response
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from src.core.config import settings


# ============================================================================
# Rate Limiter Initialization
# ============================================================================

def get_client_identifier(request: Request) -> str:
    """
    Get unique identifier for rate limiting

    Priority:
    1. Authenticated user ID (from JWT)
    2. X-Forwarded-For header (behind proxy)
    3. Remote address (direct connection)

    This ensures rate limits are per-user when authenticated,
    and per-IP when unauthenticated.
    """
    # Try to get user ID from request state (set by JWT middleware)
    if hasattr(request.state, "user_id") and request.state.user_id:
        return f"user:{request.state.user_id}"

    # Try X-Forwarded-For header (if behind reverse proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Get first IP (client IP before proxies)
        client_ip = forwarded_for.split(",")[0].strip()
        return f"ip:{client_ip}"

    # Fallback to remote address
    return f"ip:{get_remote_address(request)}"


# Initialize rate limiter
limiter = Limiter(
    key_func=get_client_identifier,
    default_limits=[],  # No default limits - apply per endpoint
    storage_uri=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",  # Distributed rate limiting
    strategy="fixed-window",  # Fixed time window (simple and efficient)
    headers_enabled=True,  # Return rate limit info in headers
)


# ============================================================================
# Rate Limit Exceeded Handler
# ============================================================================

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors

    Returns 429 Too Many Requests with retry-after header
    """
    return Response(
        content=json.dumps({
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please try again later.",
            "detail": str(exc.detail),
            "retry_after_seconds": getattr(exc, "retry_after", 60)
        }),
        status_code=429,
        media_type="application/json",
        headers={
            "Retry-After": str(getattr(exc, "retry_after", 60)),
            "X-RateLimit-Limit": str(getattr(exc, "limit", "unknown")),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(getattr(exc, "reset", "unknown"))
        }
    )


# ============================================================================
# Rate Limit Decorators for Different Endpoint Types
# ============================================================================

# Authentication Endpoints (Strict limits to prevent brute force)
AUTH_LOGIN_LIMIT = "10/minute"  # 10 login attempts per minute
AUTH_REGISTER_PATIENT_LIMIT = "5/hour"  # 5 patient registrations per hour
AUTH_REGISTER_THERAPIST_LIMIT = "3/hour"  # 3 therapist registrations per hour (more restricted)
AUTH_PASSWORD_RESET_LIMIT = "3/hour"  # 3 password reset requests per hour
AUTH_REFRESH_TOKEN_LIMIT = "20/hour"  # 20 token refreshes per hour

# AI Endpoints (Moderate limits to prevent API abuse)
AI_CHAT_LIMIT = "20/minute"  # 20 AI chat messages per minute
AI_MOOD_ANALYSIS_LIMIT = "30/minute"  # 30 mood analyses per minute
AI_DREAM_INTERPRETATION_LIMIT = "15/minute"  # 15 dream interpretations per minute

# CRUD Endpoints (Generous limits for normal usage)
CRUD_CREATE_LIMIT = "60/minute"  # 60 create operations per minute
CRUD_READ_LIMIT = "100/minute"  # 100 read operations per minute
CRUD_UPDATE_LIMIT = "60/minute"  # 60 update operations per minute
CRUD_DELETE_LIMIT = "30/minute"  # 30 delete operations per minute

# Analytics Endpoints (Moderate limits)
ANALYTICS_LIMIT = "30/minute"  # 30 analytics requests per minute

# General API Limit (Catch-all)
GENERAL_API_LIMIT = "100/minute"  # 100 requests per minute


# ============================================================================
# Rate Limit Documentation
# ============================================================================

RATE_LIMIT_INFO = {
    "authentication": {
        "login": {
            "limit": AUTH_LOGIN_LIMIT,
            "reason": "Prevent brute force password attacks"
        },
        "register_patient": {
            "limit": AUTH_REGISTER_PATIENT_LIMIT,
            "reason": "Prevent mass account creation"
        },
        "register_therapist": {
            "limit": AUTH_REGISTER_THERAPIST_LIMIT,
            "reason": "Prevent unauthorized therapist account creation"
        },
        "password_reset": {
            "limit": AUTH_PASSWORD_RESET_LIMIT,
            "reason": "Prevent account enumeration"
        },
        "refresh_token": {
            "limit": AUTH_REFRESH_TOKEN_LIMIT,
            "reason": "Prevent token refresh abuse"
        }
    },
    "ai": {
        "chat": {
            "limit": AI_CHAT_LIMIT,
            "reason": "Prevent AI API abuse and excessive costs"
        },
        "mood_analysis": {
            "limit": AI_MOOD_ANALYSIS_LIMIT,
            "reason": "Prevent AI API abuse"
        },
        "dream_interpretation": {
            "limit": AI_DREAM_INTERPRETATION_LIMIT,
            "reason": "Prevent AI API abuse (complex analysis)"
        }
    },
    "crud": {
        "create": {
            "limit": CRUD_CREATE_LIMIT,
            "reason": "Prevent spam data creation"
        },
        "read": {
            "limit": CRUD_READ_LIMIT,
            "reason": "Prevent data scraping"
        },
        "update": {
            "limit": CRUD_UPDATE_LIMIT,
            "reason": "Prevent spam updates"
        },
        "delete": {
            "limit": CRUD_DELETE_LIMIT,
            "reason": "Prevent mass data deletion"
        }
    },
    "analytics": {
        "general": {
            "limit": ANALYTICS_LIMIT,
            "reason": "Prevent analytics API abuse"
        }
    },
    "general": {
        "api": {
            "limit": GENERAL_API_LIMIT,
            "reason": "General API rate limit"
        }
    }
}


def get_rate_limit_info() -> dict:
    """
    Get rate limit information for documentation

    Returns:
        dict: Rate limit configuration details
    """
    return RATE_LIMIT_INFO


# ============================================================================
# Rate Limit Exemptions
# ============================================================================

EXEMPT_PATHS = [
    "/docs",
    "/redoc",
    "/openapi.json",
    "/health",
    "/api/v1/health",
    "/.well-known",
]


def is_exempt_from_rate_limiting(request: Request) -> bool:
    """
    Check if request path is exempt from rate limiting

    Args:
        request: FastAPI request object

    Returns:
        bool: True if exempt, False otherwise
    """
    path = request.url.path

    # Check exact matches
    if path in EXEMPT_PATHS:
        return True

    # Check prefix matches
    for exempt_path in EXEMPT_PATHS:
        if path.startswith(exempt_path):
            return True

    return False


# ============================================================================
# Monitoring & Metrics
# ============================================================================

class RateLimitMonitor:
    """
    Monitor rate limit violations for security analysis
    """

    def __init__(self):
        self.violations = []

    def record_violation(
        self,
        client_id: str,
        endpoint: str,
        limit: str,
        timestamp: str
    ):
        """
        Record a rate limit violation

        Args:
            client_id: Client identifier (user ID or IP)
            endpoint: API endpoint that was rate limited
            limit: Rate limit that was exceeded
            timestamp: When the violation occurred
        """
        self.violations.append({
            "client_id": client_id,
            "endpoint": endpoint,
            "limit": limit,
            "timestamp": timestamp
        })

        # Keep only last 1000 violations in memory
        if len(self.violations) > 1000:
            self.violations = self.violations[-1000:]

    def get_violations(self, client_id: Optional[str] = None) -> list:
        """
        Get rate limit violations

        Args:
            client_id: Optional filter by client ID

        Returns:
            list: List of violation records
        """
        if client_id:
            return [v for v in self.violations if v["client_id"] == client_id]
        return self.violations

    def get_top_violators(self, limit: int = 10) -> list:
        """
        Get top rate limit violators

        Args:
            limit: Number of top violators to return

        Returns:
            list: Top violators with violation counts
        """
        from collections import Counter

        violator_counts = Counter(v["client_id"] for v in self.violations)
        return violator_counts.most_common(limit)


# Initialize global monitor
rate_limit_monitor = RateLimitMonitor()


# ============================================================================
# Export
# ============================================================================

__all__ = [
    "limiter",
    "rate_limit_exceeded_handler",
    "get_client_identifier",
    "get_rate_limit_info",
    "is_exempt_from_rate_limiting",
    "rate_limit_monitor",
    # Rate limit constants
    "AUTH_LOGIN_LIMIT",
    "AUTH_REGISTER_PATIENT_LIMIT",
    "AUTH_REGISTER_THERAPIST_LIMIT",
    "AUTH_PASSWORD_RESET_LIMIT",
    "AUTH_REFRESH_TOKEN_LIMIT",
    "AI_CHAT_LIMIT",
    "AI_MOOD_ANALYSIS_LIMIT",
    "AI_DREAM_INTERPRETATION_LIMIT",
    "CRUD_CREATE_LIMIT",
    "CRUD_READ_LIMIT",
    "CRUD_UPDATE_LIMIT",
    "CRUD_DELETE_LIMIT",
    "ANALYTICS_LIMIT",
    "GENERAL_API_LIMIT",
]
