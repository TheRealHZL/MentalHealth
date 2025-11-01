"""
Encrypted Content Models for Zero-Knowledge Architecture

All sensitive user data is stored in encrypted format.
Only the user with their master key can decrypt the content.

The server NEVER sees plaintext data!
"""

import uuid
from datetime import datetime

from sqlalchemy import (Boolean, Column, DateTime, Integer, LargeBinary,
                        String, Text)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class EncryptedMoodEntry(Base):
    """
    Encrypted Mood Entry

    All mood details are encrypted client-side before reaching the server.

    Encrypted fields:
    - mood_score (encrypted)
    - notes (encrypted)
    - emotions (encrypted)
    - triggers (encrypted)
    - activities (encrypted)

    Metadata (unencrypted for queries):
    - created_at
    - user_id
    - entry_type
    """

    __tablename__ = "encrypted_mood_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Encrypted payload (JSON with ciphertext + nonce)
    # Format: {"ciphertext": "base64...", "nonce": "base64...", "version": 1}
    encrypted_data = Column(LargeBinary, nullable=False)

    # Metadata for queries (unencrypted)
    entry_type = Column(String(20), default="mood", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Encryption metadata
    encryption_version = Column(
        Integer, default=1, nullable=False
    )  # For future algorithm upgrades
    key_id = Column(String(64), nullable=True)  # For key rotation (future)

    # Soft delete (for GDPR compliance)
    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<EncryptedMoodEntry(id={self.id}, user_id={self.user_id}, created_at={self.created_at})>"


class EncryptedDreamEntry(Base):
    """
    Encrypted Dream Journal Entry

    All dream content is encrypted client-side.

    Encrypted fields:
    - title (encrypted)
    - content (encrypted)
    - emotions (encrypted)
    - symbols (encrypted)
    - interpretation (encrypted)
    """

    __tablename__ = "encrypted_dream_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Encrypted payload
    encrypted_data = Column(LargeBinary, nullable=False)

    # Metadata
    entry_type = Column(String(20), default="dream", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Encryption metadata
    encryption_version = Column(Integer, default=1, nullable=False)
    key_id = Column(String(64), nullable=True)

    # Soft delete
    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<EncryptedDreamEntry(id={self.id}, user_id={self.user_id}, created_at={self.created_at})>"


class EncryptedTherapyNote(Base):
    """
    Encrypted Therapy Note

    All therapy notes and worksheets are encrypted client-side.

    Encrypted fields:
    - title (encrypted)
    - content (encrypted)
    - note_type (encrypted)
    - worksheet_data (encrypted)
    - reflection (encrypted)
    """

    __tablename__ = "encrypted_therapy_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Encrypted payload
    encrypted_data = Column(LargeBinary, nullable=False)

    # Metadata
    entry_type = Column(String(20), default="therapy_note", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Encryption metadata
    encryption_version = Column(Integer, default=1, nullable=False)
    key_id = Column(String(64), nullable=True)

    # Soft delete
    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<EncryptedTherapyNote(id={self.id}, user_id={self.user_id}, created_at={self.created_at})>"


class EncryptedChatMessage(Base):
    """
    Encrypted Chat Message (AI Conversations)

    All chat messages are encrypted client-side.

    Encrypted fields:
    - user_message (encrypted)
    - ai_response (encrypted)
    - context (encrypted)
    """

    __tablename__ = "encrypted_chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    session_id = Column(
        UUID(as_uuid=True), nullable=True, index=True
    )  # For grouping conversations

    # Encrypted payload
    encrypted_data = Column(LargeBinary, nullable=False)

    # Metadata
    message_type = Column(
        String(20), default="chat", nullable=False
    )  # 'user' or 'assistant'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Encryption metadata
    encryption_version = Column(Integer, default=1, nullable=False)
    key_id = Column(String(64), nullable=True)

    # Soft delete
    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<EncryptedChatMessage(id={self.id}, user_id={self.user_id}, type={self.message_type})>"


class UserEncryptionKey(Base):
    """
    User Encryption Key Metadata

    Stores metadata about user's encryption keys (NOT the actual keys!)
    Actual master keys are derived from password and NEVER stored.

    This table tracks:
    - Key versions (for rotation)
    - Key derivation parameters (salt, iterations)
    - Key recovery hints (optional)
    """

    __tablename__ = "user_encryption_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)

    # Key derivation parameters
    # Salt is stored here (safe to store, not the key itself!)
    key_salt = Column(LargeBinary, nullable=False)  # Random salt for PBKDF2
    key_iterations = Column(
        Integer, default=600000, nullable=False
    )  # PBKDF2 iterations
    key_algorithm = Column(String(50), default="PBKDF2-SHA256", nullable=False)

    # Current key version (for rotation)
    current_key_version = Column(Integer, default=1, nullable=False)

    # Recovery options (optional, user-controlled)
    has_recovery_key = Column(Boolean, default=False, nullable=False)
    recovery_key_encrypted = Column(
        LargeBinary, nullable=True
    )  # Encrypted with secondary password

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_key_rotation = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<UserEncryptionKey(user_id={self.user_id}, version={self.current_key_version})>"
