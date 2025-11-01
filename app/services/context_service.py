"""
User Context Service

Service for managing user-specific AI context.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_context import (AIConversationHistory, UserAIPreferences,
                                     UserContext)

logger = logging.getLogger(__name__)


class ContextService:
    """Service for user context operations"""

    @staticmethod
    async def get_or_create_context(
        session: AsyncSession, user_id: UUID
    ) -> UserContext:
        """
        Get user context or create if doesn't exist

        Usage:
            context = await ContextService.get_or_create_context(session, user.id)
        """
        # Try to get existing context
        result = await session.execute(
            select(UserContext).where(UserContext.user_id == user_id)
        )
        context = result.scalar_one_or_none()

        if context:
            # Mark as accessed
            context.mark_accessed()
            await session.commit()
            return context

        # Create new context
        context = UserContext(
            user_id=user_id, context_type="general", context_version=1, is_active=True
        )

        session.add(context)
        await session.commit()
        await session.refresh(context)

        logger.info(f"✅ Created new AI context for user {user_id}")

        return context

    @staticmethod
    async def update_context(
        session: AsyncSession, user_id: UUID, encrypted_context: Dict[str, Any]
    ) -> UserContext:
        """
        Update user's encrypted context

        Args:
            encrypted_context: {"ciphertext": "...", "nonce": "...", "version": 1}

        Usage:
            context = await ContextService.update_context(session, user.id, encrypted_data)
        """
        context = await ContextService.get_or_create_context(session, user_id)

        # Update encrypted context
        context.encrypted_context = encrypted_context
        context.last_updated = datetime.utcnow()

        # Update size
        import json

        context.context_size_bytes = len(json.dumps(encrypted_context))

        await session.commit()
        await session.refresh(context)

        logger.info(
            f"✅ Updated AI context for user {user_id} ({context.context_size_bytes} bytes)"
        )

        return context

    @staticmethod
    async def get_context(
        session: AsyncSession, user_id: UUID
    ) -> Optional[UserContext]:
        """
        Get user's context

        Usage:
            context = await ContextService.get_context(session, user.id)
            if context and context.encrypted_context:
                # Decrypt and use
        """
        result = await session.execute(
            select(UserContext).where(
                and_(UserContext.user_id == user_id, UserContext.is_active == True)
            )
        )
        context = result.scalar_one_or_none()

        if context:
            context.mark_accessed()
            await session.commit()

        return context

    @staticmethod
    async def delete_context(session: AsyncSession, user_id: UUID) -> bool:
        """
        Delete user's context (for privacy/GDPR)

        Usage:
            deleted = await ContextService.delete_context(session, user.id)
        """
        result = await session.execute(
            select(UserContext).where(UserContext.user_id == user_id)
        )
        context = result.scalar_one_or_none()

        if not context:
            return False

        await session.delete(context)
        await session.commit()

        logger.info(f"✅ Deleted AI context for user {user_id}")

        return True

    @staticmethod
    async def increment_processed_count(
        session: AsyncSession, user_id: UUID, entry_type: str
    ):
        """
        Increment processed entry count

        Args:
            entry_type: "mood", "dream", "therapy", or "conversation"

        Usage:
            await ContextService.increment_processed_count(session, user.id, "mood")
        """
        context = await ContextService.get_or_create_context(session, user_id)

        if entry_type == "mood":
            context.mood_entries_processed += 1
        elif entry_type == "dream":
            context.dream_entries_processed += 1
        elif entry_type == "therapy":
            context.therapy_notes_processed += 1
        elif entry_type == "conversation":
            context.conversation_count += 1

        await session.commit()


class ConversationHistoryService:
    """Service for conversation history operations"""

    @staticmethod
    async def add_message(
        session: AsyncSession,
        user_id: UUID,
        session_id: UUID,
        message_type: str,
        encrypted_message: Dict[str, Any],
        sequence_number: Optional[int] = None,
        token_count: Optional[int] = None,
        model_version: Optional[str] = None,
    ) -> AIConversationHistory:
        """
        Add message to conversation history

        Args:
            message_type: "user" or "assistant"
            encrypted_message: {"ciphertext": "...", "nonce": "...", "version": 1}

        Usage:
            await ConversationHistoryService.add_message(
                session, user.id, session_id, "user", encrypted_msg
            )
        """
        # Auto-calculate sequence number if not provided
        if sequence_number is None:
            result = await session.execute(
                select(AIConversationHistory)
                .where(
                    and_(
                        AIConversationHistory.user_id == user_id,
                        AIConversationHistory.session_id == session_id,
                    )
                )
                .order_by(desc(AIConversationHistory.sequence_number))
                .limit(1)
            )
            last_message = result.scalar_one_or_none()
            sequence_number = (last_message.sequence_number + 1) if last_message else 1

        # Create message
        message = AIConversationHistory(
            user_id=user_id,
            session_id=session_id,
            sequence_number=sequence_number,
            message_type=message_type,
            encrypted_message=encrypted_message,
            token_count=token_count,
            model_version=model_version,
        )

        session.add(message)
        await session.commit()
        await session.refresh(message)

        logger.info(f"✅ Added {message_type} message to conversation {session_id}")

        return message

    @staticmethod
    async def get_conversation(
        session: AsyncSession, user_id: UUID, session_id: UUID, limit: int = 50
    ) -> List[AIConversationHistory]:
        """
        Get conversation history for a session

        Usage:
            messages = await ConversationHistoryService.get_conversation(
                session, user.id, session_id
            )
        """
        result = await session.execute(
            select(AIConversationHistory)
            .where(
                and_(
                    AIConversationHistory.user_id == user_id,
                    AIConversationHistory.session_id == session_id,
                    AIConversationHistory.is_deleted == False,
                )
            )
            .order_by(AIConversationHistory.sequence_number)
            .limit(limit)
        )

        return result.scalars().all()

    @staticmethod
    async def delete_conversation(
        session: AsyncSession, user_id: UUID, session_id: UUID
    ) -> int:
        """
        Soft delete a conversation

        Returns:
            Number of messages deleted

        Usage:
            count = await ConversationHistoryService.delete_conversation(
                session, user.id, session_id
            )
        """
        result = await session.execute(
            select(AIConversationHistory).where(
                and_(
                    AIConversationHistory.user_id == user_id,
                    AIConversationHistory.session_id == session_id,
                    AIConversationHistory.is_deleted == False,
                )
            )
        )
        messages = result.scalars().all()

        count = len(messages)

        for message in messages:
            message.is_deleted = True
            message.deleted_at = datetime.utcnow()

        await session.commit()

        logger.info(f"✅ Soft-deleted {count} messages from conversation {session_id}")

        return count

    @staticmethod
    async def cleanup_old_conversations(
        session: AsyncSession, user_id: UUID, days: int = 90
    ) -> int:
        """
        Delete conversations older than specified days

        Usage:
            deleted = await ConversationHistoryService.cleanup_old_conversations(
                session, user.id, days=90
            )
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        result = await session.execute(
            select(AIConversationHistory).where(
                and_(
                    AIConversationHistory.user_id == user_id,
                    AIConversationHistory.timestamp < cutoff,
                    AIConversationHistory.is_deleted == False,
                )
            )
        )
        messages = result.scalars().all()

        count = len(messages)

        for message in messages:
            message.is_deleted = True
            message.deleted_at = datetime.utcnow()

        await session.commit()

        logger.info(f"✅ Cleaned up {count} old messages for user {user_id}")

        return count


class AIPreferencesService:
    """Service for AI preferences operations"""

    @staticmethod
    async def get_or_create_preferences(
        session: AsyncSession, user_id: UUID
    ) -> UserAIPreferences:
        """
        Get user AI preferences or create with defaults

        Usage:
            prefs = await AIPreferencesService.get_or_create_preferences(session, user.id)
        """
        # Try to get existing preferences
        result = await session.execute(
            select(UserAIPreferences).where(UserAIPreferences.user_id == user_id)
        )
        prefs = result.scalar_one_or_none()

        if prefs:
            return prefs

        # Create with defaults
        prefs = UserAIPreferences(
            user_id=user_id,
            response_style="empathetic",
            response_length="medium",
            formality_level="friendly",
            language="de",
        )

        session.add(prefs)
        await session.commit()
        await session.refresh(prefs)

        logger.info(f"✅ Created AI preferences for user {user_id}")

        return prefs

    @staticmethod
    async def update_preferences(
        session: AsyncSession, user_id: UUID, updates: Dict[str, Any]
    ) -> UserAIPreferences:
        """
        Update user AI preferences

        Usage:
            prefs = await AIPreferencesService.update_preferences(
                session,
                user.id,
                {"response_style": "professional", "language": "en"}
            )
        """
        prefs = await AIPreferencesService.get_or_create_preferences(session, user_id)

        # Update fields
        for key, value in updates.items():
            if hasattr(prefs, key):
                setattr(prefs, key, value)

        prefs.updated_at = datetime.utcnow()

        await session.commit()
        await session.refresh(prefs)

        logger.info(f"✅ Updated AI preferences for user {user_id}")

        return prefs


__all__ = ["ContextService", "ConversationHistoryService", "AIPreferencesService"]
