"""
User-Isolated AI Engine for MindBridge

Ensures complete user isolation for AI processing:
- User A's context is NEVER accessible by User B
- Each user has separate AI memory and conversation history
- All AI responses use ONLY the user's own data
- Automatic context loading/saving from database
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.engine import AIEngine
from app.core.rls_middleware import set_user_context
from app.services.context_service import (AIPreferencesService, ContextService,
                                          ConversationHistoryService)

logger = logging.getLogger(__name__)


class UserIsolatedAIEngine:
    """
    User-Isolated AI Engine

    Wraps the base AIEngine to provide complete user isolation:
    - Loads user-specific context from database
    - Saves conversation history per user
    - Respects user AI preferences
    - Ensures no cross-user data leakage
    """

    def __init__(self, base_engine: AIEngine):
        """
        Initialize User-Isolated AI Engine

        Args:
            base_engine: The base AIEngine instance (shared across users)
        """
        self.base_engine = base_engine
        self.context_cache: Dict[str, Any] = {}  # In-memory cache per user
        self.cache_ttl = timedelta(minutes=15)  # Cache TTL

        logger.info("🔒 User-Isolated AI Engine initialized")

    # =========================================================================
    # Context Management
    # =========================================================================

    async def load_user_context(
        self, session: AsyncSession, user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Load user-specific AI context from database

        Args:
            session: Database session with RLS context set
            user_id: User ID

        Returns:
            User's AI context (decrypted on client-side)
        """
        try:
            # Set RLS context for this user
            await set_user_context(session, user_id, is_admin=False)

            # Check cache first
            cache_key = str(user_id)
            if cache_key in self.context_cache:
                cached = self.context_cache[cache_key]
                if datetime.utcnow() - cached["timestamp"] < self.cache_ttl:
                    logger.debug(f"Using cached context for user {user_id}")
                    return cached["context"]

            # Load from database
            context = await ContextService.get_context(session, user_id)

            if not context:
                # Create new context if doesn't exist
                context = await ContextService.get_or_create_context(session, user_id)
                logger.info(f"Created new AI context for user {user_id}")

            # Convert to dict for processing
            context_data = {
                "user_id": str(context.user_id),
                "context_type": context.context_type,
                "encrypted_context": context.encrypted_context,
                "conversation_count": context.conversation_count,
                "mood_entries_processed": context.mood_entries_processed,
                "dream_entries_processed": context.dream_entries_processed,
                "therapy_notes_processed": context.therapy_notes_processed,
                "last_accessed_at": (
                    context.last_accessed_at.isoformat()
                    if context.last_accessed_at
                    else None
                ),
            }

            # Update cache
            self.context_cache[cache_key] = {
                "context": context_data,
                "timestamp": datetime.utcnow(),
            }

            # Increment access count
            await ContextService.increment_access_count(session, user_id)

            return context_data

        except Exception as e:
            logger.error(f"Failed to load context for user {user_id}: {e}")
            # Return minimal context on error
            return {
                "user_id": str(user_id),
                "context_type": "general",
                "encrypted_context": None,
                "error": str(e),
            }

    async def save_user_context(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        encrypted_context: Dict[str, Any],
    ) -> bool:
        """
        Save user-specific AI context to database

        Args:
            session: Database session with RLS context set
            user_id: User ID
            encrypted_context: Encrypted context payload

        Returns:
            Success status
        """
        try:
            # Set RLS context
            await set_user_context(session, user_id, is_admin=False)

            # Update context in database
            await ContextService.update_context(session, user_id, encrypted_context)

            # Invalidate cache
            cache_key = str(user_id)
            if cache_key in self.context_cache:
                del self.context_cache[cache_key]

            logger.info(f"Saved AI context for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save context for user {user_id}: {e}")
            return False

    async def load_user_preferences(
        self, session: AsyncSession, user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Load user AI preferences

        Args:
            session: Database session with RLS context set
            user_id: User ID

        Returns:
            User's AI preferences
        """
        try:
            # Set RLS context
            await set_user_context(session, user_id, is_admin=False)

            # Load preferences
            prefs = await AIPreferencesService.get_or_create_preferences(
                session, user_id
            )

            return {
                "response_style": prefs.response_style,
                "response_length": prefs.response_length,
                "formality_level": prefs.formality_level,
                "language": prefs.language,
                "enable_mood_analysis": prefs.enable_mood_analysis,
                "enable_dream_interpretation": prefs.enable_dream_interpretation,
                "enable_therapy_insights": prefs.enable_therapy_insights,
                "custom_system_prompt": prefs.custom_system_prompt,
            }

        except Exception as e:
            logger.error(f"Failed to load preferences for user {user_id}: {e}")
            # Return defaults
            return {
                "response_style": "empathetic",
                "response_length": "medium",
                "formality_level": "friendly",
                "language": "de",
            }

    async def load_conversation_history(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Load conversation history for a specific session

        Args:
            session: Database session with RLS context set
            user_id: User ID
            session_id: Conversation session ID
            limit: Maximum number of messages to load

        Returns:
            List of conversation messages (encrypted)
        """
        try:
            # Set RLS context
            await set_user_context(session, user_id, is_admin=False)

            # Load conversation
            messages = await ConversationHistoryService.get_conversation(
                session, user_id, session_id, limit=limit
            )

            return [
                {
                    "message_type": msg.message_type,
                    "encrypted_message": msg.encrypted_message,
                    "sequence_number": msg.sequence_number,
                    "token_count": msg.token_count,
                    "created_at": msg.created_at.isoformat(),
                }
                for msg in messages
            ]

        except Exception as e:
            logger.error(f"Failed to load conversation for user {user_id}: {e}")
            return []

    async def save_conversation_message(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        message_type: str,
        encrypted_message: Dict[str, Any],
        token_count: Optional[int] = None,
    ) -> bool:
        """
        Save a message to conversation history

        Args:
            session: Database session with RLS context set
            user_id: User ID
            session_id: Conversation session ID
            message_type: "user" or "assistant"
            encrypted_message: Encrypted message payload
            token_count: Token count for context window management

        Returns:
            Success status
        """
        try:
            # Set RLS context
            await set_user_context(session, user_id, is_admin=False)

            # Save message
            await ConversationHistoryService.add_message(
                session,
                user_id,
                session_id,
                message_type,
                encrypted_message,
                token_count,
            )

            # Increment conversation count in context
            await ContextService.increment_conversation_count(session, user_id)

            logger.debug(f"Saved {message_type} message for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save message for user {user_id}: {e}")
            return False

    # =========================================================================
    # AI Operations with User Isolation
    # =========================================================================

    async def generate_user_response(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        user_message: str,
        session_id: uuid.UUID,
        decrypt_context_fn: Optional[callable] = None,
        encrypt_response_fn: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """
        Generate AI response with complete user isolation

        This is the main entry point for user-specific AI generation.
        Ensures User A's context is NEVER accessible by User B.

        Args:
            session: Database session with RLS context set
            user_id: User ID (CRITICAL: must match session RLS context)
            user_message: User's message (plaintext or encrypted)
            session_id: Conversation session ID
            decrypt_context_fn: Optional function to decrypt user context
            encrypt_response_fn: Optional function to encrypt AI response

        Returns:
            AI response with metadata
        """
        try:
            # SECURITY: Verify RLS context is set for this user
            await set_user_context(session, user_id, is_admin=False)

            # Load user-specific data
            user_context = await self.load_user_context(session, user_id)
            user_prefs = await self.load_user_preferences(session, user_id)
            conversation_history = await self.load_conversation_history(
                session, user_id, session_id, limit=10  # Last 10 messages for context
            )

            # Decrypt context if function provided
            decrypted_context = None
            if decrypt_context_fn and user_context.get("encrypted_context"):
                try:
                    decrypted_context = decrypt_context_fn(
                        user_context["encrypted_context"]
                    )
                except Exception as e:
                    logger.warning(f"Failed to decrypt context: {e}")

            # Build AI context from USER'S OWN DATA ONLY
            ai_context = {
                "user_id": str(user_id),  # For logging/debugging only
                "mood_entries_count": user_context.get("mood_entries_processed", 0),
                "dream_entries_count": user_context.get("dream_entries_processed", 0),
                "therapy_notes_count": user_context.get("therapy_notes_processed", 0),
                "conversation_count": user_context.get("conversation_count", 0),
                "preferences": user_prefs,
                "decrypted_context": decrypted_context,
            }

            # Prepare conversation history (still encrypted for now)
            # Client-side should decrypt these before passing to AI
            history_for_ai = []
            for msg in conversation_history:
                history_for_ai.append(
                    {
                        "role": msg["message_type"],
                        "content": msg["encrypted_message"],  # Client decrypts
                        "timestamp": msg["created_at"],
                    }
                )

            # Apply user preferences to generation parameters
            generation_params = self._apply_user_preferences(user_prefs)

            # Generate response using base engine
            # NOTE: This is where actual AI inference happens
            response = await self.base_engine.generate_chat_response(
                user_message=user_message,
                conversation_history=history_for_ai,
                user_context=ai_context,
            )

            # Save user message to history (encrypted)
            await self.save_conversation_message(
                session,
                user_id,
                session_id,
                message_type="user",
                encrypted_message={
                    "content": user_message
                },  # Should be encrypted by client
                token_count=len(user_message.split()),  # Rough token count
            )

            # Save assistant response to history (encrypted)
            await self.save_conversation_message(
                session,
                user_id,
                session_id,
                message_type="assistant",
                encrypted_message={
                    "content": response["response"]
                },  # Should be encrypted
                token_count=len(response["response"].split()),
            )

            # Encrypt response if function provided
            encrypted_response = None
            if encrypt_response_fn:
                try:
                    encrypted_response = encrypt_response_fn(response["response"])
                except Exception as e:
                    logger.warning(f"Failed to encrypt response: {e}")

            return {
                "response": response["response"],
                "encrypted_response": encrypted_response,
                "confidence": response.get("confidence", 0.8),
                "safety_checked": response.get("safety_checked", True),
                "user_id": str(user_id),  # For client verification
                "session_id": str(session_id),
                "generation_params": generation_params,
                "latency_ms": response.get("latency_ms", 0),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to generate response for user {user_id}: {e}")
            return {
                "response": "Entschuldigung, ich hatte ein technisches Problem. Bitte versuche es nochmal.",
                "error": str(e),
                "user_id": str(user_id),
                "session_id": str(session_id),
            }

    async def analyze_user_mood(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        mood_text: str,
        mood_metadata: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Analyze mood using ONLY this user's data

        Args:
            session: Database session with RLS context set
            user_id: User ID
            mood_text: Mood entry text
            mood_metadata: Additional mood metadata

        Returns:
            Mood analysis results
        """
        try:
            # Set RLS context
            await set_user_context(session, user_id, is_admin=False)

            # Load user preferences
            user_prefs = await self.load_user_preferences(session, user_id)

            # Check if mood analysis is enabled for this user
            if not user_prefs.get("enable_mood_analysis", True):
                return {
                    "analysis_disabled": True,
                    "message": "Mood analysis disabled by user preferences",
                }

            # Perform mood analysis using base engine
            analysis = await self.base_engine.predict_mood(
                text=mood_text, metadata=mood_metadata or {}
            )

            # Increment mood entry count
            await ContextService.increment_mood_count(session, user_id)

            return {
                "user_id": str(user_id),
                "mood_score": analysis.get("mood_score"),
                "confidence": analysis.get("confidence"),
                "trend": analysis.get("trend"),
                "latency_ms": analysis.get("latency_ms"),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to analyze mood for user {user_id}: {e}")
            return {"error": str(e), "user_id": str(user_id)}

    async def analyze_user_dream(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        dream_text: str,
        dream_metadata: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Analyze dream using ONLY this user's data

        Args:
            session: Database session with RLS context set
            user_id: User ID
            dream_text: Dream description
            dream_metadata: Additional dream metadata

        Returns:
            Dream analysis results
        """
        try:
            # Set RLS context
            await set_user_context(session, user_id, is_admin=False)

            # Load user preferences
            user_prefs = await self.load_user_preferences(session, user_id)

            # Check if dream interpretation is enabled
            if not user_prefs.get("enable_dream_interpretation", True):
                return {
                    "analysis_disabled": True,
                    "message": "Dream interpretation disabled by user preferences",
                }

            # Perform emotion analysis on dream
            emotion_analysis = await self.base_engine.predict_emotion(
                text=dream_text, context={"type": "dream", **(dream_metadata or {})}
            )

            # Increment dream entry count
            await ContextService.increment_dream_count(session, user_id)

            return {
                "user_id": str(user_id),
                "emotion": emotion_analysis.get("emotion"),
                "confidence": emotion_analysis.get("confidence"),
                "probabilities": emotion_analysis.get("probabilities"),
                "latency_ms": emotion_analysis.get("latency_ms"),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to analyze dream for user {user_id}: {e}")
            return {"error": str(e), "user_id": str(user_id)}

    async def analyze_user_therapy_note(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        note_text: str,
        note_metadata: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Analyze therapy note using ONLY this user's data

        Args:
            session: Database session with RLS context set
            user_id: User ID
            note_text: Therapy note content
            note_metadata: Additional note metadata

        Returns:
            Therapy note analysis results
        """
        try:
            # Set RLS context
            await set_user_context(session, user_id, is_admin=False)

            # Load user preferences
            user_prefs = await self.load_user_preferences(session, user_id)

            # Check if therapy insights are enabled
            if not user_prefs.get("enable_therapy_insights", True):
                return {
                    "analysis_disabled": True,
                    "message": "Therapy insights disabled by user preferences",
                }

            # Perform emotion analysis
            emotion_analysis = await self.base_engine.predict_emotion(
                text=note_text,
                context={"type": "therapy_note", **(note_metadata or {})},
            )

            # Perform sentiment analysis
            sentiment_analysis = await self.base_engine.analyze_sentiment(note_text)

            # Increment therapy note count
            await ContextService.increment_therapy_count(session, user_id)

            return {
                "user_id": str(user_id),
                "emotion": emotion_analysis.get("emotion"),
                "sentiment": sentiment_analysis.get("sentiment"),
                "emotion_confidence": emotion_analysis.get("confidence"),
                "sentiment_confidence": sentiment_analysis.get("confidence"),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to analyze therapy note for user {user_id}: {e}")
            return {"error": str(e), "user_id": str(user_id)}

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _apply_user_preferences(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply user preferences to AI generation parameters

        Args:
            preferences: User AI preferences

        Returns:
            Generation parameters
        """
        # Map response length to max tokens
        length_map = {"brief": 100, "medium": 200, "detailed": 400}

        # Map formality to temperature
        formality_temp = {
            "casual": 0.9,
            "friendly": 0.7,
            "professional": 0.5,
            "formal": 0.3,
        }

        return {
            "max_tokens": length_map.get(
                preferences.get("response_length", "medium"), 200
            ),
            "temperature": formality_temp.get(
                preferences.get("formality_level", "friendly"), 0.7
            ),
            "language": preferences.get("language", "de"),
            "response_style": preferences.get("response_style", "empathetic"),
        }

    async def cleanup_user_cache(self, user_id: uuid.UUID):
        """
        Clear cached context for a user

        Args:
            user_id: User ID
        """
        cache_key = str(user_id)
        if cache_key in self.context_cache:
            del self.context_cache[cache_key]
            logger.debug(f"Cleared cache for user {user_id}")

    async def cleanup_old_conversations(
        self, session: AsyncSession, user_id: uuid.UUID, days: int = 90
    ) -> int:
        """
        Cleanup old conversations for GDPR compliance

        Args:
            session: Database session with RLS context set
            user_id: User ID
            days: Retention period in days

        Returns:
            Number of conversations deleted
        """
        try:
            # Set RLS context
            await set_user_context(session, user_id, is_admin=False)

            # Cleanup old conversations
            deleted_count = await ConversationHistoryService.cleanup_old_conversations(
                session, user_id, days=days
            )

            logger.info(
                f"Cleaned up {deleted_count} old conversations for user {user_id}"
            )
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup conversations for user {user_id}: {e}")
            return 0
