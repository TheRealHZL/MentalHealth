"""
User Context API Endpoints

API endpoints for managing user-specific AI context and preferences.
All context data is encrypted client-side before storage.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from uuid import UUID
import logging

from src.core.rls_fastapi_middleware import get_rls_session, require_authentication
from src.services.context_service import (
    ContextService,
    ConversationHistoryService,
    AIPreferencesService
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Schemas
# ============================================================================

class EncryptedPayload(BaseModel):
    """Encrypted data payload"""
    ciphertext: str = Field(description="Base64-encoded encrypted data")
    nonce: str = Field(description="Base64-encoded nonce")
    version: int = Field(default=1, description="Encryption version")


class ContextUpdateRequest(BaseModel):
    """Request to update user context"""
    encrypted_context: EncryptedPayload = Field(description="Encrypted context data")


class ContextResponse(BaseModel):
    """User context response"""
    id: str
    user_id: str
    context_type: str
    encrypted_context: Optional[Dict[str, Any]]
    context_size_bytes: Optional[int]
    last_updated: str
    is_active: bool
    access_count: int
    conversation_count: int
    mood_entries_processed: int
    dream_entries_processed: int
    therapy_notes_processed: int


class ConversationMessageRequest(BaseModel):
    """Request to add message to conversation"""
    message_type: str = Field(description="'user' or 'assistant'")
    encrypted_message: EncryptedPayload = Field(description="Encrypted message content")
    token_count: Optional[int] = Field(None, description="Token count for context window")


class ConversationMessageResponse(BaseModel):
    """Conversation message response"""
    id: str
    session_id: str
    sequence_number: int
    message_type: str
    encrypted_message: Dict[str, Any]
    timestamp: str
    token_count: Optional[int]


class AIPreferencesResponse(BaseModel):
    """AI preferences response"""
    id: str
    user_id: str
    response_style: str
    response_length: str
    formality_level: str
    language: str
    enable_mood_analysis: bool
    enable_dream_interpretation: bool
    enable_pattern_recognition: bool
    remember_conversations: bool
    use_historical_data: bool


class AIPreferencesUpdateRequest(BaseModel):
    """Request to update AI preferences"""
    response_style: Optional[str] = None
    response_length: Optional[str] = None
    formality_level: Optional[str] = None
    language: Optional[str] = None
    enable_mood_analysis: Optional[bool] = None
    enable_dream_interpretation: Optional[bool] = None
    enable_pattern_recognition: Optional[bool] = None
    remember_conversations: Optional[bool] = None
    use_historical_data: Optional[bool] = None
    preferred_therapy_approaches: Optional[List[str]] = None
    topics_of_interest: Optional[List[str]] = None


# ============================================================================
# User Context Endpoints
# ============================================================================

@router.get("/", response_model=ContextResponse)
async def get_user_context(
    user_id: UUID = Depends(require_authentication),
    session: AsyncSession = Depends(get_rls_session)
):
    """
    Get User's AI Context

    Retrieves the encrypted AI context for the authenticated user.
    Context includes conversation history, learned patterns, and preferences.
    """
    try:
        context = await ContextService.get_context(session, user_id)

        if not context:
            # Create new context if doesn't exist
            context = await ContextService.get_or_create_context(session, user_id)

        return ContextResponse(**context.to_dict(include_encrypted=True))

    except Exception as e:
        logger.error(f"Failed to get context for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve AI context"
        )


@router.put("/", response_model=ContextResponse)
async def update_user_context(
    data: ContextUpdateRequest,
    user_id: UUID = Depends(require_authentication),
    session: AsyncSession = Depends(get_rls_session)
):
    """
    Update User's AI Context

    Updates the encrypted AI context with new data.
    Context should be encrypted client-side before sending.
    """
    try:
        # Convert encrypted payload to dict
        encrypted_context = {
            "ciphertext": data.encrypted_context.ciphertext,
            "nonce": data.encrypted_context.nonce,
            "version": data.encrypted_context.version
        }

        context = await ContextService.update_context(
            session,
            user_id,
            encrypted_context
        )

        return ContextResponse(**context.to_dict(include_encrypted=True))

    except Exception as e:
        logger.error(f"Failed to update context for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update AI context"
        )


@router.delete("/")
async def delete_user_context(
    user_id: UUID = Depends(require_authentication),
    session: AsyncSession = Depends(get_rls_session)
):
    """
    Delete User's AI Context

    Permanently deletes the user's AI context (GDPR right to deletion).
    This action cannot be undone.
    """
    try:
        deleted = await ContextService.delete_context(session, user_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AI context not found"
            )

        return {
            "success": True,
            "message": "AI context deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete context for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete AI context"
        )


# ============================================================================
# Conversation History Endpoints
# ============================================================================

@router.get("/conversation/{session_id}", response_model=List[ConversationMessageResponse])
async def get_conversation_history(
    session_id: UUID,
    user_id: UUID = Depends(require_authentication),
    session: AsyncSession = Depends(get_rls_session),
    limit: int = 50
):
    """
    Get Conversation History

    Retrieves encrypted conversation history for a specific session.
    Messages are returned in chronological order.
    """
    try:
        messages = await ConversationHistoryService.get_conversation(
            session,
            user_id,
            session_id,
            limit
        )

        return [
            ConversationMessageResponse(**msg.to_dict(include_encrypted=True))
            for msg in messages
        ]

    except Exception as e:
        logger.error(f"Failed to get conversation {session_id} for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation history"
        )


@router.post("/conversation/{session_id}", response_model=ConversationMessageResponse)
async def add_conversation_message(
    session_id: UUID,
    data: ConversationMessageRequest,
    user_id: UUID = Depends(require_authentication),
    session: AsyncSession = Depends(get_rls_session)
):
    """
    Add Message to Conversation

    Adds an encrypted message to the conversation history.
    Automatically assigns sequence number.
    """
    try:
        # Validate message type
        if data.message_type not in ["user", "assistant"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="message_type must be 'user' or 'assistant'"
            )

        # Convert encrypted payload to dict
        encrypted_message = {
            "ciphertext": data.encrypted_message.ciphertext,
            "nonce": data.encrypted_message.nonce,
            "version": data.encrypted_message.version
        }

        message = await ConversationHistoryService.add_message(
            session,
            user_id,
            session_id,
            data.message_type,
            encrypted_message,
            token_count=data.token_count
        )

        # Increment conversation count in context
        await ContextService.increment_processed_count(session, user_id, "conversation")

        return ConversationMessageResponse(**message.to_dict(include_encrypted=True))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add message to conversation {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add message to conversation"
        )


@router.delete("/conversation/{session_id}")
async def delete_conversation(
    session_id: UUID,
    user_id: UUID = Depends(require_authentication),
    session: AsyncSession = Depends(get_rls_session)
):
    """
    Delete Conversation

    Soft-deletes all messages in a conversation session.
    Messages are marked as deleted but not physically removed.
    """
    try:
        count = await ConversationHistoryService.delete_conversation(
            session,
            user_id,
            session_id
        )

        return {
            "success": True,
            "message": f"Deleted {count} messages from conversation",
            "deleted_count": count
        }

    except Exception as e:
        logger.error(f"Failed to delete conversation {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation"
        )


# ============================================================================
# AI Preferences Endpoints
# ============================================================================

@router.get("/preferences", response_model=AIPreferencesResponse)
async def get_ai_preferences(
    user_id: UUID = Depends(require_authentication),
    session: AsyncSession = Depends(get_rls_session)
):
    """
    Get AI Preferences

    Retrieves the user's AI interaction preferences.
    Includes response style, language, and feature toggles.
    """
    try:
        prefs = await AIPreferencesService.get_or_create_preferences(session, user_id)

        return AIPreferencesResponse(**prefs.to_dict())

    except Exception as e:
        logger.error(f"Failed to get AI preferences for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve AI preferences"
        )


@router.put("/preferences", response_model=AIPreferencesResponse)
async def update_ai_preferences(
    data: AIPreferencesUpdateRequest,
    user_id: UUID = Depends(require_authentication),
    session: AsyncSession = Depends(get_rls_session)
):
    """
    Update AI Preferences

    Updates the user's AI interaction preferences.
    Only provided fields will be updated.
    """
    try:
        # Filter out None values
        updates = {k: v for k, v in data.dict().items() if v is not None}

        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )

        prefs = await AIPreferencesService.update_preferences(
            session,
            user_id,
            updates
        )

        return AIPreferencesResponse(**prefs.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update AI preferences for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update AI preferences"
        )


# ============================================================================
# Utility Endpoints
# ============================================================================

@router.post("/cleanup")
async def cleanup_old_conversations(
    user_id: UUID = Depends(require_authentication),
    session: AsyncSession = Depends(get_rls_session),
    days: int = 90
):
    """
    Cleanup Old Conversations

    Deletes conversations older than specified days (default 90).
    This helps maintain GDPR compliance and reduce storage.
    """
    try:
        if days < 1 or days > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Days must be between 1 and 365"
            )

        count = await ConversationHistoryService.cleanup_old_conversations(
            session,
            user_id,
            days
        )

        return {
            "success": True,
            "message": f"Cleaned up {count} old messages",
            "deleted_count": count,
            "retention_days": days
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cleanup conversations for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup old conversations"
        )


@router.get("/stats")
async def get_context_stats(
    user_id: UUID = Depends(require_authentication),
    session: AsyncSession = Depends(get_rls_session)
):
    """
    Get Context Statistics

    Returns statistics about the user's AI context and usage.
    """
    try:
        context = await ContextService.get_context(session, user_id)

        if not context:
            context = await ContextService.get_or_create_context(session, user_id)

        return {
            "context_size_bytes": context.context_size_bytes,
            "access_count": context.access_count,
            "conversation_count": context.conversation_count,
            "mood_entries_processed": context.mood_entries_processed,
            "dream_entries_processed": context.dream_entries_processed,
            "therapy_notes_processed": context.therapy_notes_processed,
            "last_updated": context.last_updated.isoformat() if context.last_updated else None,
            "last_accessed": context.last_accessed.isoformat() if context.last_accessed else None,
            "days_since_update": context.days_since_update,
            "is_active": context.is_active
        }

    except Exception as e:
        logger.error(f"Failed to get context stats for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve context statistics"
        )
