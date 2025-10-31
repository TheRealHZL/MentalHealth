"""
Encryption Service - Server-Side Utilities

IMPORTANT: This service does NOT perform encryption/decryption of user data!
User data is encrypted CLIENT-SIDE in the browser.

This service provides:
- Validation of encrypted payloads
- Key derivation parameter management
- Encryption setup assistance
- Testing endpoints for client-side encryption

The server NEVER sees plaintext user data!
"""

import base64
import hashlib
import os
import secrets
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import logging
from src.models.encrypted_models import UserEncryptionKey

logger = logging.getLogger(__name__)


class EncryptionService:
    """
    Server-side encryption utilities for Zero-Knowledge architecture.

    This service helps users set up encryption but NEVER decrypts user data.
    """

    # Security parameters
    DEFAULT_PBKDF2_ITERATIONS = 600000  # OWASP recommended minimum
    SALT_LENGTH = 32  # 256 bits
    MIN_PASSWORD_LENGTH = 12  # Minimum password length for security

    # Supported encryption versions
    SUPPORTED_VERSIONS = [1]
    CURRENT_VERSION = 1

    @staticmethod
    def generate_salt() -> bytes:
        """
        Generate a cryptographically secure random salt.

        Returns:
            32 bytes of random data
        """
        return secrets.token_bytes(EncryptionService.SALT_LENGTH)

    @staticmethod
    def validate_encrypted_payload(
        payload: Dict[str, Any],
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that an encrypted payload has the correct structure.

        Expected format:
        {
            "ciphertext": "base64-encoded-string",
            "nonce": "base64-encoded-string",
            "version": 1
        }

        Args:
            payload: The encrypted payload to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        required_fields = ["ciphertext", "nonce", "version"]
        for field in required_fields:
            if field not in payload:
                return False, f"Missing required field: {field}"

        # Validate ciphertext
        if not isinstance(payload["ciphertext"], str):
            return False, "Ciphertext must be a string"

        if len(payload["ciphertext"]) == 0:
            return False, "Ciphertext cannot be empty"

        try:
            # Try to decode base64
            base64.b64decode(payload["ciphertext"])
        except Exception:
            return False, "Ciphertext must be valid base64"

        # Validate nonce
        if not isinstance(payload["nonce"], str):
            return False, "Nonce must be a string"

        try:
            nonce_bytes = base64.b64decode(payload["nonce"])
            # AES-GCM nonce should be 12 bytes (96 bits)
            if len(nonce_bytes) != 12:
                return False, "Nonce must be 12 bytes (96 bits) for AES-GCM"
        except Exception:
            return False, "Nonce must be valid base64"

        # Validate version
        if not isinstance(payload["version"], int):
            return False, "Version must be an integer"

        if payload["version"] not in EncryptionService.SUPPORTED_VERSIONS:
            return False, f"Unsupported encryption version: {payload['version']}"

        return True, None

    @staticmethod
    async def setup_user_encryption(
        db: AsyncSession,
        user_id: str,
        salt: Optional[bytes] = None,
        iterations: Optional[int] = None,
    ) -> UserEncryptionKey:
        """
        Set up encryption parameters for a new user.

        This creates a UserEncryptionKey record with key derivation parameters.
        The actual master key is derived client-side and NEVER stored!

        Args:
            db: Database session
            user_id: User ID
            salt: Optional custom salt (if None, generates random)
            iterations: Optional PBKDF2 iterations (if None, uses default)

        Returns:
            UserEncryptionKey instance
        """
        # Check if user already has encryption setup
        result = await db.execute(
            select(UserEncryptionKey).where(UserEncryptionKey.user_id == user_id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            logger.warning(f"User {user_id} already has encryption setup")
            return existing

        # Generate salt if not provided
        if salt is None:
            salt = EncryptionService.generate_salt()

        # Use default iterations if not provided
        if iterations is None:
            iterations = EncryptionService.DEFAULT_PBKDF2_ITERATIONS

        # Create encryption key metadata
        encryption_key = UserEncryptionKey(
            user_id=user_id,
            key_salt=salt,
            key_iterations=iterations,
            key_algorithm="PBKDF2-SHA256",
            current_key_version=EncryptionService.CURRENT_VERSION,
            has_recovery_key=False,
        )

        db.add(encryption_key)
        await db.commit()
        await db.refresh(encryption_key)

        logger.info(f"Created encryption setup for user {user_id}")

        return encryption_key

    @staticmethod
    async def get_user_encryption_params(
        db: AsyncSession, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get encryption parameters for a user.

        Returns parameters needed for client-side key derivation.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Dict with encryption parameters or None if not set up
        """
        result = await db.execute(
            select(UserEncryptionKey).where(UserEncryptionKey.user_id == user_id)
        )
        encryption_key = result.scalar_one_or_none()

        if not encryption_key:
            return None

        return {
            "salt": base64.b64encode(encryption_key.key_salt).decode("utf-8"),
            "iterations": encryption_key.key_iterations,
            "algorithm": encryption_key.key_algorithm,
            "version": encryption_key.current_key_version,
            "has_recovery_key": encryption_key.has_recovery_key,
        }

    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
        """
        Validate password strength for encryption.

        Requirements:
        - At least 12 characters
        - Contains uppercase and lowercase
        - Contains numbers
        - Contains special characters

        Args:
            password: Password to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < EncryptionService.MIN_PASSWORD_LENGTH:
            return (
                False,
                f"Password must be at least {EncryptionService.MIN_PASSWORD_LENGTH} characters",
            )

        # Check for uppercase
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"

        # Check for lowercase
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"

        # Check for digits
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one number"

        # Check for special characters
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            return False, "Password must contain at least one special character"

        return True, None

    @staticmethod
    def estimate_key_derivation_time(iterations: int) -> float:
        """
        Estimate time to derive key with given iterations.

        This is a rough estimate based on typical hardware.
        Actual time varies by device.

        Args:
            iterations: Number of PBKDF2 iterations

        Returns:
            Estimated time in seconds
        """
        # Rough estimate: 600,000 iterations ≈ 0.5 seconds on modern hardware
        # This is conservative; could be faster on newer devices
        return (iterations / 600000) * 0.5

    @staticmethod
    async def rotate_user_key(db: AsyncSession, user_id: str) -> UserEncryptionKey:
        """
        Rotate user's encryption key (for future use).

        This generates new salt and increments key version.
        User must re-encrypt all data with new key.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Updated UserEncryptionKey
        """
        result = await db.execute(
            select(UserEncryptionKey).where(UserEncryptionKey.user_id == user_id)
        )
        encryption_key = result.scalar_one_or_none()

        if not encryption_key:
            raise ValueError(f"User {user_id} does not have encryption setup")

        # Generate new salt
        new_salt = EncryptionService.generate_salt()

        # Update key metadata
        encryption_key.key_salt = new_salt
        encryption_key.current_key_version += 1
        encryption_key.last_key_rotation = datetime.utcnow()

        await db.commit()
        await db.refresh(encryption_key)

        logger.info(
            f"Rotated encryption key for user {user_id} to version {encryption_key.current_key_version}"
        )

        return encryption_key

    @staticmethod
    def generate_recovery_key() -> str:
        """
        Generate a recovery key for account recovery.

        This is a random 256-bit key encoded as base64.
        User should save this securely offline.

        Returns:
            Base64-encoded recovery key
        """
        recovery_key_bytes = secrets.token_bytes(32)  # 256 bits
        return base64.b64encode(recovery_key_bytes).decode("utf-8")

    @staticmethod
    def validate_encrypted_data_size(
        encrypted_data: bytes, max_size_mb: int = 10
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that encrypted data is not too large.

        Args:
            encrypted_data: The encrypted data bytes
            max_size_mb: Maximum allowed size in MB

        Returns:
            Tuple of (is_valid, error_message)
        """
        max_bytes = max_size_mb * 1024 * 1024

        if len(encrypted_data) > max_bytes:
            return False, f"Encrypted data exceeds maximum size of {max_size_mb}MB"

        return True, None
