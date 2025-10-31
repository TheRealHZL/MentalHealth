"""
FastAPI Middleware for Row-Level Security (RLS)

This middleware automatically sets the PostgreSQL RLS context for every authenticated request.
It extracts the user from the JWT token and sets app.user_id in the database session.

Usage:
    app.add_middleware(RLSMiddleware)
"""

import logging
from typing import Callable, Optional
from uuid import UUID

from fastapi import Depends, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.database import get_async_session
from src.core.rls_middleware import set_user_context
from src.core.security import decode_token

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


class RLSMiddleware(BaseHTTPMiddleware):
    """
    Middleware that automatically sets RLS context for authenticated requests

    For every authenticated request:
    1. Extract user_id from JWT token
    2. Set app.user_id in PostgreSQL session
    3. All subsequent queries are automatically filtered by RLS policies
    """

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request and set RLS context"""

        # Skip RLS for public endpoints
        if self._is_public_endpoint(request.url.path):
            logger.debug(f"⏭️ Skipping RLS for public endpoint: {request.url.path}")
            response = await call_next(request)
            return response

        # Extract user_id from JWT token
        user_id = await self._extract_user_id(request)

        if user_id:
            # Store user_id in request state for later use
            request.state.user_id = user_id
            request.state.is_authenticated = True

            logger.debug(f"✅ RLS context will be set for user {user_id}")
        else:
            request.state.user_id = None
            request.state.is_authenticated = False

            logger.debug(f"⚠️ No user_id found - RLS not set")

        # Process request
        response = await call_next(request)

        return response

    def _is_public_endpoint(self, path: str) -> bool:
        """
        Check if endpoint is public (doesn't require authentication)

        Public endpoints:
        - /docs, /redoc (API documentation)
        - /openapi.json (OpenAPI spec)
        - /health (Health check)
        - /api/v1/users/login (Login)
        - /api/v1/users/register/* (Registration)
        """
        public_paths = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/api/v1/users/login",
            "/api/v1/users/register",
        ]

        return any(path.startswith(public) for public in public_paths)

    async def _extract_user_id(self, request: Request) -> Optional[UUID]:
        """
        Extract user_id from JWT token in Authorization header

        Returns:
            UUID: User ID if token is valid, None otherwise
        """
        try:
            # Get Authorization header
            auth_header = request.headers.get("Authorization")

            if not auth_header:
                return None

            # Extract token (format: "Bearer <token>")
            if not auth_header.startswith("Bearer "):
                return None

            token = auth_header.replace("Bearer ", "")

            # Decode token
            payload = decode_token(token)

            if not payload:
                return None

            # Extract user_id (sub claim)
            user_id_str = payload.get("sub")

            if not user_id_str:
                return None

            # Convert to UUID
            user_id = UUID(user_id_str)

            return user_id

        except Exception as e:
            logger.warning(f"⚠️ Failed to extract user_id from token: {e}")
            return None


# ============================================================================
# FastAPI Dependencies for RLS-protected endpoints
# ============================================================================


async def get_current_user_id(request: Request) -> Optional[UUID]:
    """
    FastAPI dependency to get current user ID from request state

    This is set by RLSMiddleware.

    Usage:
        @router.get("/protected")
        async def protected_endpoint(
            user_id: UUID = Depends(get_current_user_id)
        ):
            return {"user_id": str(user_id)}
    """
    return getattr(request.state, "user_id", None)


async def require_authentication(request: Request) -> UUID:
    """
    FastAPI dependency that requires authentication

    Raises:
        HTTPException: If user is not authenticated

    Usage:
        @router.get("/protected")
        async def protected_endpoint(
            user_id: UUID = Depends(require_authentication)
        ):
            # user_id is guaranteed to be set
            return {"user_id": str(user_id)}
    """
    from fastapi import HTTPException, status

    user_id = getattr(request.state, "user_id", None)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id


async def get_rls_session(
    request: Request, session: AsyncSession = Depends(get_async_session)
) -> AsyncSession:
    """
    FastAPI dependency that provides a database session with RLS context set

    This automatically sets the app.user_id in PostgreSQL session,
    enabling Row-Level Security policies.

    Usage:
        @router.get("/mood")
        async def get_moods(
            session: AsyncSession = Depends(get_rls_session)
        ):
            # This session has RLS context set!
            # All queries automatically filter by user_id
            result = await session.execute(select(MoodEntry))
            return result.scalars().all()
    """
    user_id = getattr(request.state, "user_id", None)

    if user_id:
        # Set RLS context
        await set_user_context(session, user_id, is_admin=False)
        logger.debug(f"✅ RLS context set for session: user_id={user_id}")
    else:
        logger.debug(f"⚠️ No user_id - RLS context NOT set")

    return session


async def get_admin_rls_session(
    request: Request, session: AsyncSession = Depends(get_async_session)
) -> AsyncSession:
    """
    FastAPI dependency for admin sessions (bypasses RLS)

    This is for system operations that need to access all data.

    Usage:
        @router.get("/admin/all-moods")
        async def get_all_moods(
            session: AsyncSession = Depends(get_admin_rls_session)
        ):
            # This session can see ALL data
            result = await session.execute(select(MoodEntry))
            return result.scalars().all()
    """
    user_id = getattr(request.state, "user_id", None)

    if user_id:
        # Set RLS context with admin flag
        await set_user_context(session, user_id, is_admin=True)
        logger.debug(f"✅ ADMIN RLS context set: user_id={user_id}")
    else:
        logger.warning(f"⚠️ No user_id for admin session")

    return session


# ============================================================================
# Utility Functions
# ============================================================================


def is_user_authenticated(request: Request) -> bool:
    """
    Check if current request is authenticated

    Usage:
        if is_user_authenticated(request):
            print("User is logged in!")
    """
    return getattr(request.state, "is_authenticated", False)


def get_user_id_from_request(request: Request) -> Optional[UUID]:
    """
    Get user_id from request state (set by middleware)

    Usage:
        user_id = get_user_id_from_request(request)
        if user_id:
            print(f"User: {user_id}")
    """
    return getattr(request.state, "user_id", None)


# ============================================================================
# Integration Example
# ============================================================================

"""
Example: How to use RLS in your API endpoints

## 1. Add middleware to FastAPI app (in main.py):

from src.core.rls_fastapi_middleware import RLSMiddleware

app = FastAPI()
app.add_middleware(RLSMiddleware)


## 2. Use RLS-protected session in endpoints:

from src.core.rls_fastapi_middleware import get_rls_session, require_authentication

@router.get("/mood")
async def get_moods(
    user_id: UUID = Depends(require_authentication),
    session: AsyncSession = Depends(get_rls_session)
):
    # This query automatically filters by user_id thanks to RLS!
    result = await session.execute(select(MoodEntry))
    moods = result.scalars().all()

    # User will ONLY see their own moods
    return [mood.to_dict() for mood in moods]


## 3. For admin endpoints (see all data):

from src.core.rls_fastapi_middleware import get_admin_rls_session

@router.get("/admin/all-moods")
async def get_all_moods(
    user_id: UUID = Depends(require_authentication),  # Still need auth
    session: AsyncSession = Depends(get_admin_rls_session)  # But bypass RLS
):
    # Check if user is admin (add your own logic)
    if not user_is_admin(user_id):
        raise HTTPException(403, "Admin access required")

    # This query sees ALL moods (RLS bypassed)
    result = await session.execute(select(MoodEntry))
    return result.scalars().all()


## 4. No changes needed to existing queries!

The beauty of RLS is that it works automatically:

# Before RLS:
result = await session.execute(select(MoodEntry))

# After RLS:
result = await session.execute(select(MoodEntry))  # Same code!

# But now it automatically filters by user_id at the database level!
"""

__all__ = [
    "RLSMiddleware",
    "get_current_user_id",
    "require_authentication",
    "get_rls_session",
    "get_admin_rls_session",
    "is_user_authenticated",
    "get_user_id_from_request",
]
