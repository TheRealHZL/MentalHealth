"""
User Context Models for AI Isolation

Stores user-specific AI context in encrypted format.
Each user has completely isolated AI memory and context.
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import uuid

from src.core.database import Base


class UserContext(Base):
    """
    User-specific AI Context Storage

    Each user has isolated AI context that includes:
    - Conversation history
    - Learned patterns
    - Preferences
    - Behavioral data
    - Emotional state tracking

    All sensitive context data is encrypted client-side.
    """
    __tablename__ = "user_contexts"

    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True, unique=True)

    # Context type and version
    context_type = Column(String(50), nullable=False, default="general", index=True)
    context_version = Column(Integer, nullable=False, default=1)

    # Encrypted context data (JSONB with ciphertext)
    encrypted_context = Column(JSONB, nullable=True)
    # Format: {"ciphertext": "...", "nonce": "...", "version": 1}

    # Metadata (unencrypted for queries)
    context_size_bytes = Column(Integer, nullable=True)  # Size tracking
    last_updated = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), index=True)
    created_at = Column(DateTime, nullable=False, default=func.now())

    # Context lifecycle
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=True)  # Optional expiration

    # Access tracking
    access_count = Column(Integer, default=0, nullable=False)
    last_accessed = Column(DateTime, nullable=True)

    # Context statistics (unencrypted)
    conversation_count = Column(Integer, default=0, nullable=False)
    mood_entries_processed = Column(Integer, default=0, nullable=False)
    dream_entries_processed = Column(Integer, default=0, nullable=False)
    therapy_notes_processed = Column(Integer, default=0, nullable=False)

    # AI model information
    ai_model_version = Column(String(50), nullable=True)
    last_training_date = Column(DateTime, nullable=True)

    # Privacy settings
    allow_learning = Column(Boolean, default=True, nullable=False)
    context_retention_days = Column(Integer, default=90, nullable=False)

    # Relationships
    user = relationship("User", back_populates="ai_context")

    def __repr__(self):
        return f"<UserContext(user_id={self.user_id}, type={self.context_type}, size={self.context_size_bytes})>"

    @property
    def is_expired(self) -> bool:
        """Check if context has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def days_since_update(self) -> int:
        """Calculate days since last update"""
        if not self.last_updated:
            return 0
        delta = datetime.utcnow() - self.last_updated
        return delta.days

    @property
    def should_expire(self) -> bool:
        """Check if context should expire based on retention policy"""
        return self.days_since_update > self.context_retention_days

    def mark_accessed(self):
        """Mark context as accessed (for tracking)"""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()

    def to_dict(self, include_encrypted: bool = False) -> dict:
        """Convert to dictionary"""
        data = {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "context_type": self.context_type,
            "context_version": self.context_version,
            "context_size_bytes": self.context_size_bytes,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "conversation_count": self.conversation_count,
            "mood_entries_processed": self.mood_entries_processed,
            "dream_entries_processed": self.dream_entries_processed,
            "therapy_notes_processed": self.therapy_notes_processed,
            "ai_model_version": self.ai_model_version,
            "allow_learning": self.allow_learning,
            "context_retention_days": self.context_retention_days,
            "is_expired": self.is_expired,
            "days_since_update": self.days_since_update
        }

        if include_encrypted and self.encrypted_context:
            data["encrypted_context"] = self.encrypted_context

        return data


class AIConversationHistory(Base):
    """
    AI Conversation History (per user)

    Stores conversation history for context continuity.
    Each conversation is encrypted separately.
    """
    __tablename__ = "ai_conversation_history"

    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Session information
    session_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    sequence_number = Column(Integer, nullable=False)  # Order within session

    # Message details
    message_type = Column(String(20), nullable=False)  # "user" or "assistant"
    encrypted_message = Column(JSONB, nullable=False)  # Encrypted message content

    # Metadata
    timestamp = Column(DateTime, nullable=False, default=func.now(), index=True)
    token_count = Column(Integer, nullable=True)  # For context window management

    # AI response metadata
    model_version = Column(String(50), nullable=True)
    confidence_score = Column(Integer, nullable=True)  # 0-100
    processing_time_ms = Column(Integer, nullable=True)

    # Privacy
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<AIConversationHistory(user_id={self.user_id}, session={self.session_id}, type={self.message_type})>"

    def to_dict(self, include_encrypted: bool = False) -> dict:
        """Convert to dictionary"""
        data = {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "session_id": str(self.session_id),
            "sequence_number": self.sequence_number,
            "message_type": self.message_type,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "token_count": self.token_count,
            "model_version": self.model_version,
            "confidence_score": self.confidence_score,
            "processing_time_ms": self.processing_time_ms
        }

        if include_encrypted and self.encrypted_message:
            data["encrypted_message"] = self.encrypted_message

        return data


class UserAIPreferences(Base):
    """
    User AI Preferences

    Stores user preferences for AI interactions.
    These are NOT encrypted (user preferences, not sensitive data).
    """
    __tablename__ = "user_ai_preferences"

    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True, unique=True)

    # Conversation preferences
    response_style = Column(String(50), default="empathetic", nullable=False)
    # Options: "empathetic", "professional", "casual", "supportive", "direct"

    response_length = Column(String(20), default="medium", nullable=False)
    # Options: "brief", "medium", "detailed"

    formality_level = Column(String(20), default="friendly", nullable=False)
    # Options: "formal", "friendly", "casual"

    # Language preferences
    language = Column(String(10), default="de", nullable=False)
    include_emotional_validation = Column(Boolean, default=True, nullable=False)
    include_actionable_advice = Column(Boolean, default=True, nullable=False)

    # Feature preferences
    enable_mood_analysis = Column(Boolean, default=True, nullable=False)
    enable_dream_interpretation = Column(Boolean, default=True, nullable=False)
    enable_pattern_recognition = Column(Boolean, default=True, nullable=False)
    enable_recommendations = Column(Boolean, default=True, nullable=False)

    # Privacy preferences
    remember_conversations = Column(Boolean, default=True, nullable=False)
    use_historical_data = Column(Boolean, default=True, nullable=False)
    personalize_responses = Column(Boolean, default=True, nullable=False)

    # Notification preferences
    notify_on_insights = Column(Boolean, default=True, nullable=False)
    notify_on_patterns = Column(Boolean, default=True, nullable=False)
    notify_on_concerns = Column(Boolean, default=True, nullable=False)

    # Advanced preferences
    preferred_therapy_approaches = Column(ARRAY(String), nullable=True)
    # Options: ["CBT", "DBT", "Mindfulness", "ACT", etc.]

    topics_of_interest = Column(ARRAY(String), nullable=True)
    # Topics user wants AI to focus on

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<UserAIPreferences(user_id={self.user_id}, style={self.response_style})>"

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "response_style": self.response_style,
            "response_length": self.response_length,
            "formality_level": self.formality_level,
            "language": self.language,
            "include_emotional_validation": self.include_emotional_validation,
            "include_actionable_advice": self.include_actionable_advice,
            "enable_mood_analysis": self.enable_mood_analysis,
            "enable_dream_interpretation": self.enable_dream_interpretation,
            "enable_pattern_recognition": self.enable_pattern_recognition,
            "enable_recommendations": self.enable_recommendations,
            "remember_conversations": self.remember_conversations,
            "use_historical_data": self.use_historical_data,
            "personalize_responses": self.personalize_responses,
            "notify_on_insights": self.notify_on_insights,
            "notify_on_patterns": self.notify_on_patterns,
            "notify_on_concerns": self.notify_on_concerns,
            "preferred_therapy_approaches": self.preferred_therapy_approaches,
            "topics_of_interest": self.topics_of_interest
        }


# Indexes for performance
from sqlalchemy import Index

Index('idx_user_contexts_user_type', UserContext.user_id, UserContext.context_type)
Index('idx_user_contexts_updated', UserContext.last_updated.desc())
Index('idx_conversation_history_user_session', AIConversationHistory.user_id, AIConversationHistory.session_id)
Index('idx_conversation_history_timestamp', AIConversationHistory.timestamp.desc())
