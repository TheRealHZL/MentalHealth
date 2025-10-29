"""
Security Module

JWT, Password Hashing, and Authentication utilities.
"""

from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets
import logging

from src.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Password hashing context - with proper bcrypt configuration
# bcrypt has a 72 byte limit, we handle this by truncating passwords
pwd_context = CryptContext(
    schemes=["bcrypt"], bcrypt__truncate_error=False,
    deprecated="auto",
)

# =============================================================================
# Password Security
# =============================================================================

def hash_password(password: str) -> str:
    """
    Hash password using bcrypt
    
    bcrypt has a 72-byte limit. We truncate passwords to 72 bytes,
    but we do it carefully to avoid cutting in the middle of a multi-byte UTF-8 character.
    """
    # Encode to bytes
    password_bytes = password.encode('utf-8')
    
    # If longer than 72 bytes, truncate carefully
    if len(password_bytes) > 72:
        # Truncate to 72 bytes
        truncated = password_bytes[:72]
        
        # Decode back, ignoring errors to handle partial multi-byte chars
        # Then re-encode to get valid UTF-8
        password = truncated.decode('utf-8', errors='ignore')
    
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify password against hash
    
    Apply the same truncation logic as hash_password for consistency
    """
    try:
        # Apply same truncation as during hashing
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            truncated = password_bytes[:72]
            password = truncated.decode('utf-8', errors='ignore')
        
        return pwd_context.verify(password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False

# =============================================================================
# JWT Token Management
# =============================================================================

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})

    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create refresh token with longer expiration"""
    
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)  # 7 days for refresh tokens
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "refresh"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate JWT token"""
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.error(f"Token decode error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected token error: {e}")
        return None


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """Verify token and check type"""
    
    payload = decode_token(token)
    
    if not payload:
        return None
    
    # Check token type for refresh tokens
    if token_type == "refresh" and payload.get("type") != "refresh":
        logger.warning("Invalid token type")
        return None
    
    return payload

# =============================================================================
# Security Headers
# =============================================================================

def get_security_headers() -> Dict[str, str]:
    """Get security headers for responses"""
    
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains" if settings.ENVIRONMENT == "production" else "",
        "Content-Security-Policy": "default-src 'self'" if settings.ENVIRONMENT == "production" else "",
        "Referrer-Policy": "strict-origin-when-cross-origin"
    }

# =============================================================================
# Token Generation
# =============================================================================

def generate_verification_token() -> str:
    """Generate secure verification token"""
    return secrets.token_urlsafe(32)


def generate_share_key() -> str:
    """Generate secure share key for data sharing"""
    return secrets.token_urlsafe(48)


def generate_reset_token() -> str:
    """Generate password reset token"""
    return secrets.token_urlsafe(32)

# =============================================================================
# Rate Limiting (Simple implementation)
# =============================================================================

from collections import defaultdict
from datetime import datetime
from typing import Tuple

# In-memory rate limit store (use Redis in production)
_rate_limit_store: Dict[str, list] = defaultdict(list)


def check_rate_limit(identifier: str, limit: int = 5, window_minutes: int = 15) -> Tuple[bool, int]:
    """
    Check if identifier has exceeded rate limit
    
    Returns: (is_allowed, remaining_attempts)
    """
    
    now = datetime.utcnow()
    window_start = now - timedelta(minutes=window_minutes)
    
    # Clean old attempts
    _rate_limit_store[identifier] = [
        attempt for attempt in _rate_limit_store[identifier]
        if attempt > window_start
    ]
    
    current_attempts = len(_rate_limit_store[identifier])
    
    if current_attempts >= limit:
        return False, 0
    
    # Add current attempt
    _rate_limit_store[identifier].append(now)
    
    remaining = limit - (current_attempts + 1)
    return True, remaining


def create_rate_limit_dependency(limit: int = 30, window_minutes: int = 60):
    """Create a rate limit dependency for FastAPI"""
    
    from fastapi import Request, HTTPException, status
    
    async def rate_limit_checker(request: Request):
        """Check rate limit for request"""
        
        # Use IP address as identifier
        client_ip = request.client.host if request.client else "unknown"
        
        is_allowed, remaining = check_rate_limit(
            f"{client_ip}:{request.url.path}",
            limit=limit,
            window_minutes=window_minutes
        )
        
        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {window_minutes} minutes."
            )
        
        return remaining
    
    return rate_limit_checker

# =============================================================================
# Authentication Dependencies
# =============================================================================

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security_scheme = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> str:
    """Get current user ID from JWT token"""
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


async def get_current_user_with_role(
    required_role: str,
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> str:
    """Get current user ID and verify role"""
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    user_role = payload.get("role")
    
    if not user_id or not user_role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user_role != required_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required role: {required_role}"
        )
    
    return user_id


async def require_patient_or_therapist(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> str:
    """Require user to be either patient or therapist"""
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    user_role = payload.get("role")
    
    if not user_id or not user_role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user_role not in ["patient", "therapist"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Patients and therapists only."
        )
    
    return user_id


async def get_current_user_role(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> tuple[str, str]:
    """Get current user ID and role from JWT token"""
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    user_role = payload.get("role")
    
    if not user_id or not user_role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id, user_role


async def get_current_user_id_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[str]:
    """Get current user ID from JWT token (optional - returns None if no token)"""
    
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        return None
    
    return payload.get("sub")
