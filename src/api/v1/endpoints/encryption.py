"""
Encryption API Endpoints

These endpoints help users set up and manage client-side encryption.
The server NEVER decrypts user data - all encryption happens in the browser.
"""

import base64
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.logging import get_logger
from src.core.security import get_current_user_id
from src.services.encryption_service import EncryptionService

logger = get_logger(__name__)

router = APIRouter(prefix="/encryption", tags=["encryption"])


# ========================================
# Request/Response Models
# ========================================


class EncryptionSetupRequest(BaseModel):
    """Request to set up encryption for a user"""

    iterations: Optional[int] = Field(
        default=600000,
        ge=100000,  # OWASP minimum
        le=1000000,  # Reasonable maximum
        description="Number of PBKDF2 iterations",
    )


class EncryptionParamsResponse(BaseModel):
    """Response with encryption parameters"""

    salt: str = Field(description="Base64-encoded salt for PBKDF2")
    iterations: int = Field(description="Number of PBKDF2 iterations")
    algorithm: str = Field(description="Key derivation algorithm")
    version: int = Field(description="Encryption version")
    has_recovery_key: bool = Field(description="Whether user has set up recovery key")
    estimated_derivation_time: float = Field(
        description="Estimated time to derive key (seconds)"
    )


class ValidatePayloadRequest(BaseModel):
    """Request to validate an encrypted payload"""

    ciphertext: str = Field(description="Base64-encoded ciphertext")
    nonce: str = Field(description="Base64-encoded nonce (12 bytes for AES-GCM)")
    version: int = Field(description="Encryption version", default=1)


class ValidatePayloadResponse(BaseModel):
    """Response from payload validation"""

    valid: bool = Field(description="Whether payload is valid")
    error: Optional[str] = Field(description="Error message if invalid", default=None)


class PasswordStrengthRequest(BaseModel):
    """Request to validate password strength"""

    password: str = Field(description="Password to validate")


class PasswordStrengthResponse(BaseModel):
    """Response from password strength validation"""

    valid: bool = Field(description="Whether password is strong enough")
    error: Optional[str] = Field(description="Error message if weak", default=None)
    strength_score: int = Field(description="Strength score (0-100)", ge=0, le=100)


class RecoveryKeyResponse(BaseModel):
    """Response with recovery key"""

    recovery_key: str = Field(
        description="Base64-encoded recovery key - SAVE THIS SECURELY!"
    )
    warning: str = Field(
        default="Store this recovery key in a secure location. You will need it to recover your account if you forget your password. This key will never be shown again!"
    )


# ========================================
# Endpoints
# ========================================


@router.post("/setup", response_model=EncryptionParamsResponse)
async def setup_encryption(
    request: EncryptionSetupRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Set up client-side encryption for the current user.

    This creates encryption parameters (salt, iterations) for key derivation.
    The actual master key is derived in the browser and NEVER sent to the server.

    **This should be called once during user registration.**
    """
    try:
        # Set up encryption for user
        encryption_key = await EncryptionService.setup_user_encryption(
            db=db, user_id=user_id, iterations=request.iterations
        )

        # Calculate estimated derivation time
        estimated_time = EncryptionService.estimate_key_derivation_time(
            encryption_key.key_iterations
        )

        return EncryptionParamsResponse(
            salt=base64.b64encode(encryption_key.key_salt).decode("utf-8"),
            iterations=encryption_key.key_iterations,
            algorithm=encryption_key.key_algorithm,
            version=encryption_key.current_key_version,
            has_recovery_key=encryption_key.has_recovery_key,
            estimated_derivation_time=estimated_time,
        )

    except Exception as e:
        logger.error(f"Failed to set up encryption for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set up encryption",
        )


@router.get("/params", response_model=EncryptionParamsResponse)
async def get_encryption_params(
    user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)
):
    """
    Get encryption parameters for the current user.

    Returns the salt and iterations needed for client-side key derivation.

    **This should be called on login to derive the master key in the browser.**
    """
    try:
        # Get encryption parameters
        params = await EncryptionService.get_user_encryption_params(db, user_id)

        if not params:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Encryption not set up for this user. Please complete registration.",
            )

        # Calculate estimated derivation time
        estimated_time = EncryptionService.estimate_key_derivation_time(
            params["iterations"]
        )

        return EncryptionParamsResponse(
            salt=params["salt"],
            iterations=params["iterations"],
            algorithm=params["algorithm"],
            version=params["version"],
            has_recovery_key=params["has_recovery_key"],
            estimated_derivation_time=estimated_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get encryption params for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve encryption parameters",
        )


@router.post("/validate-payload", response_model=ValidatePayloadResponse)
async def validate_encrypted_payload(
    request: ValidatePayloadRequest, user_id: str = Depends(get_current_user_id)
):
    """
    Validate that an encrypted payload has the correct structure.

    This checks:
    - Required fields are present
    - Ciphertext and nonce are valid base64
    - Nonce is correct length (12 bytes for AES-GCM)
    - Version is supported

    **Use this before saving encrypted data to catch errors early.**
    """
    payload = request.dict()
    valid, error = EncryptionService.validate_encrypted_payload(payload)

    return ValidatePayloadResponse(valid=valid, error=error)


@router.post("/validate-password", response_model=PasswordStrengthResponse)
async def validate_password_strength(request: PasswordStrengthRequest):
    """
    Validate password strength for encryption.

    Requirements:
    - At least 12 characters
    - Uppercase and lowercase letters
    - Numbers
    - Special characters

    **Use this during signup/password change to ensure strong passwords.**
    """
    valid, error = EncryptionService.validate_password_strength(request.password)

    # Calculate strength score (simple heuristic)
    score = 0
    if len(request.password) >= 12:
        score += 25
    if len(request.password) >= 16:
        score += 15
    if any(c.isupper() for c in request.password):
        score += 15
    if any(c.islower() for c in request.password):
        score += 15
    if any(c.isdigit() for c in request.password):
        score += 15
    if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in request.password):
        score += 15

    return PasswordStrengthResponse(
        valid=valid, error=error, strength_score=min(score, 100)
    )


@router.post("/generate-recovery-key", response_model=RecoveryKeyResponse)
async def generate_recovery_key(user_id: str = Depends(get_current_user_id)):
    """
    Generate a recovery key for account recovery.

    This generates a random 256-bit key that can be used to recover the account
    if the user forgets their password.

    **⚠️ IMPORTANT:**
    - This key is shown ONCE and never stored on the server
    - User MUST save it in a secure location (password manager, offline storage)
    - Without this key, forgotten passwords = lost data (Zero-Knowledge!)

    **Implementation Note:**
    The recovery key can be encrypted with a secondary password and stored
    in UserEncryptionKey.recovery_key_encrypted for actual recovery functionality.
    """
    recovery_key = EncryptionService.generate_recovery_key()

    return RecoveryKeyResponse(recovery_key=recovery_key)


@router.post("/rotate-key")
async def rotate_encryption_key(
    user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)
):
    """
    Rotate encryption key (generate new salt and version).

    **⚠️ WARNING:**
    After key rotation, ALL encrypted data must be re-encrypted with the new key!
    This is a complex operation and should only be done when necessary.

    **Not implemented in Phase 2 - placeholder for future.**
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Key rotation will be implemented in a future phase. "
        "This is a complex operation that requires re-encrypting all user data.",
    )


@router.get("/status")
async def get_encryption_status(
    user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)
):
    """
    Get encryption status for the current user.

    Returns whether encryption is set up and ready to use.
    """
    params = await EncryptionService.get_user_encryption_params(db, user_id)

    return {
        "encryption_enabled": params is not None,
        "ready": params is not None,
        "version": params.get("version") if params else None,
        "has_recovery_key": params.get("has_recovery_key") if params else False,
    }
