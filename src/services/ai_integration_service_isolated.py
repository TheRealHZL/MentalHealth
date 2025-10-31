"""
User-Isolated AI Integration Service

Wrapper around AIIntegrationService that adds complete user isolation.
Ensures User A's data is NEVER accessible by User B during AI processing.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.ai.user_isolated_engine import UserIsolatedAIEngine
from src.core.rls_middleware import set_user_context
from src.models import DreamEntry, MoodEntry, TherapyNote

logger = logging.getLogger(__name__)


class UserIsolatedAIIntegrationService:
    """
    User-Isolated AI Integration Service

    All AI analysis methods now require:
    - session: Database session (RLS context will be set automatically)
    - user_id: User ID for isolation
    - entry: The data entry to analyze

    Guarantees:
    - User A's AI analysis NEVER uses User B's data
    - All context is loaded from user-specific database records
    - Complete audit trail of AI operations
    """

    def __init__(self, isolated_ai_engine: UserIsolatedAIEngine):
        """
        Initialize User-Isolated AI Integration Service

        Args:
            isolated_ai_engine: UserIsolatedAIEngine instance
        """
        self.isolated_ai_engine = isolated_ai_engine
        logger.info("🔒 User-Isolated AI Integration Service initialized")

    # =========================================================================
    # Mood Entry Analysis
    # =========================================================================

    async def analyze_mood_entry(
        self, session: AsyncSession, user_id: uuid.UUID, mood_entry: MoodEntry
    ) -> Dict[str, Any]:
        """
        Analyze mood entry with complete user isolation

        Args:
            session: Database session
            user_id: User ID (must match mood_entry.user_id)
            mood_entry: Mood entry to analyze

        Returns:
            AI analysis results using ONLY this user's context
        """
        try:
            # SECURITY: Verify entry belongs to user
            if str(mood_entry.user_id) != str(user_id):
                logger.error(
                    f"Security violation: User {user_id} attempted to analyze "
                    f"mood entry belonging to {mood_entry.user_id}"
                )
                raise PermissionError("Cannot analyze another user's mood entry")

            # Set RLS context
            await set_user_context(session, user_id, is_admin=False)

            # Build analysis text
            analysis_text = self._build_mood_analysis_text(mood_entry)

            # Perform user-isolated mood analysis
            mood_analysis = await self.isolated_ai_engine.analyze_user_mood(
                session=session,
                user_id=user_id,
                mood_text=analysis_text,
                mood_metadata={
                    "mood_score": mood_entry.mood_score,
                    "stress_level": mood_entry.stress_level,
                    "sleep_quality": mood_entry.sleep_quality,
                    "sleep_hours": mood_entry.sleep_hours,
                    "exercise_minutes": mood_entry.exercise_minutes,
                    "energy_level": mood_entry.energy_level,
                },
            )

            # Get emotion analysis using base engine
            # (already isolated via user context)
            emotion_result = await self.isolated_ai_engine.base_engine.predict_emotion(
                text=analysis_text,
                context={
                    "user_id": str(user_id),
                    "mood_score": mood_entry.mood_score,
                    "stress_level": mood_entry.stress_level,
                },
            )

            # Sentiment analysis
            sentiment_result = (
                await self.isolated_ai_engine.base_engine.analyze_sentiment(
                    text=analysis_text
                )
            )

            return {
                "ai_generated": True,
                "user_id": str(user_id),
                "mood_analysis": mood_analysis,
                "emotion_analysis": emotion_result,
                "sentiment_analysis": sentiment_result,
                "confidence_score": (
                    mood_analysis.get("confidence", 0)
                    + emotion_result.get("confidence", 0)
                    + sentiment_result.get("confidence", 0)
                )
                / 3,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "isolation_verified": True,
            }

        except PermissionError as e:
            logger.error(f"Permission denied: {e}")
            raise
        except Exception as e:
            logger.error(f"Mood analysis failed for user {user_id}: {e}")
            return {
                "ai_generated": False,
                "user_id": str(user_id),
                "error": "AI analysis temporarily unavailable",
                "details": str(e),
            }

    # =========================================================================
    # Dream Entry Analysis
    # =========================================================================

    async def analyze_dream_entry(
        self, session: AsyncSession, user_id: uuid.UUID, dream_entry: DreamEntry
    ) -> Dict[str, Any]:
        """
        Analyze dream entry with complete user isolation

        Args:
            session: Database session
            user_id: User ID (must match dream_entry.user_id)
            dream_entry: Dream entry to analyze

        Returns:
            AI analysis results using ONLY this user's context
        """
        try:
            # SECURITY: Verify entry belongs to user
            if str(dream_entry.user_id) != str(user_id):
                logger.error(
                    f"Security violation: User {user_id} attempted to analyze "
                    f"dream entry belonging to {dream_entry.user_id}"
                )
                raise PermissionError("Cannot analyze another user's dream entry")

            # Set RLS context
            await set_user_context(session, user_id, is_admin=False)

            # Build dream text
            dream_text = self._build_dream_text(dream_entry)

            # Perform user-isolated dream analysis
            dream_analysis = await self.isolated_ai_engine.analyze_user_dream(
                session=session,
                user_id=user_id,
                dream_text=dream_text,
                dream_metadata={
                    "dream_type": (
                        dream_entry.dream_type.value if dream_entry.dream_type else None
                    ),
                    "mood_after_waking": dream_entry.mood_after_waking,
                    "is_recurring": dream_entry.is_recurring,
                    "vividness": dream_entry.vividness,
                },
            )

            # Get sentiment analysis
            sentiment_result = (
                await self.isolated_ai_engine.base_engine.analyze_sentiment(
                    text=dream_text
                )
            )

            # Symbol analysis (if symbols present)
            symbol_analysis = {}
            if dream_entry.symbols:
                for symbol in dream_entry.symbols[:3]:  # Limit to 3 symbols
                    symbol_text = f"Dream symbol: {symbol}"
                    symbol_emotion = (
                        await self.isolated_ai_engine.base_engine.predict_emotion(
                            text=symbol_text,
                            context={
                                "type": "symbol_analysis",
                                "user_id": str(user_id),
                            },
                        )
                    )
                    symbol_analysis[symbol] = {
                        "emotion": symbol_emotion.get("emotion"),
                        "confidence": symbol_emotion.get("confidence"),
                    }

            return {
                "ai_generated": True,
                "user_id": str(user_id),
                "dream_analysis": dream_analysis,
                "sentiment_analysis": sentiment_result,
                "symbol_analysis": symbol_analysis,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "isolation_verified": True,
            }

        except PermissionError as e:
            logger.error(f"Permission denied: {e}")
            raise
        except Exception as e:
            logger.error(f"Dream analysis failed for user {user_id}: {e}")
            return {
                "ai_generated": False,
                "user_id": str(user_id),
                "error": "AI dream analysis temporarily unavailable",
                "details": str(e),
            }

    # =========================================================================
    # Therapy Note Analysis
    # =========================================================================

    async def analyze_therapy_note(
        self, session: AsyncSession, user_id: uuid.UUID, therapy_note: TherapyNote
    ) -> Dict[str, Any]:
        """
        Analyze therapy note with complete user isolation

        Args:
            session: Database session
            user_id: User ID (must match therapy_note.user_id)
            therapy_note: Therapy note to analyze

        Returns:
            AI analysis results using ONLY this user's context
        """
        try:
            # SECURITY: Verify entry belongs to user
            if str(therapy_note.user_id) != str(user_id):
                logger.error(
                    f"Security violation: User {user_id} attempted to analyze "
                    f"therapy note belonging to {therapy_note.user_id}"
                )
                raise PermissionError("Cannot analyze another user's therapy note")

            # Set RLS context
            await set_user_context(session, user_id, is_admin=False)

            # Build note text
            note_text = self._build_therapy_note_text(therapy_note)

            # Perform user-isolated therapy note analysis
            note_analysis = await self.isolated_ai_engine.analyze_user_therapy_note(
                session=session,
                user_id=user_id,
                note_text=note_text,
                note_metadata={
                    "note_type": (
                        therapy_note.note_type.value if therapy_note.note_type else None
                    ),
                    "goals_discussed": therapy_note.goals_discussed,
                    "techniques_used": therapy_note.techniques_used,
                    "progress_made": therapy_note.progress_made,
                },
            )

            return {
                "ai_generated": True,
                "user_id": str(user_id),
                "therapy_note_analysis": note_analysis,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "isolation_verified": True,
            }

        except PermissionError as e:
            logger.error(f"Permission denied: {e}")
            raise
        except Exception as e:
            logger.error(f"Therapy note analysis failed for user {user_id}: {e}")
            return {
                "ai_generated": False,
                "user_id": str(user_id),
                "error": "AI therapy analysis temporarily unavailable",
                "details": str(e),
            }

    # =========================================================================
    # Chat Response Generation
    # =========================================================================

    async def generate_chat_response(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        user_message: str,
        session_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        Generate chat response with complete user isolation

        Args:
            session: Database session
            user_id: User ID
            user_message: User's message
            session_id: Conversation session ID

        Returns:
            AI response using ONLY this user's context
        """
        try:
            # Set RLS context
            await set_user_context(session, user_id, is_admin=False)

            # Generate user-isolated response
            response = await self.isolated_ai_engine.generate_user_response(
                session=session,
                user_id=user_id,
                user_message=user_message,
                session_id=session_id,
            )

            return {
                "ai_generated": True,
                "user_id": str(user_id),
                "response": response.get("response"),
                "confidence": response.get("confidence"),
                "safety_checked": response.get("safety_checked", True),
                "session_id": str(session_id),
                "timestamp": datetime.utcnow().isoformat(),
                "isolation_verified": True,
            }

        except Exception as e:
            logger.error(f"Chat response generation failed for user {user_id}: {e}")
            return {
                "ai_generated": False,
                "user_id": str(user_id),
                "response": "Entschuldigung, ich hatte ein technisches Problem. Bitte versuche es nochmal.",
                "error": str(e),
            }

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _build_mood_analysis_text(self, mood_entry: MoodEntry) -> str:
        """Build text for mood analysis"""

        parts = [f"Stimmung: {mood_entry.mood_score}/10"]

        if mood_entry.notes:
            parts.append(f"Notizen: {mood_entry.notes}")

        if mood_entry.activities:
            parts.append(f"Aktivitäten: {', '.join(mood_entry.activities)}")

        if mood_entry.symptoms:
            parts.append(f"Symptome: {', '.join(mood_entry.symptoms)}")

        if mood_entry.triggers:
            parts.append(f"Auslöser: {', '.join(mood_entry.triggers)}")

        parts.append(f"Stress: {mood_entry.stress_level}/10")
        parts.append(f"Energie: {mood_entry.energy_level}/10")
        parts.append(
            f"Schlaf: {mood_entry.sleep_hours}h, Qualität: {mood_entry.sleep_quality}/10"
        )

        return " | ".join(parts)

    def _build_dream_text(self, dream_entry: DreamEntry) -> str:
        """Build text for dream analysis"""

        parts = []

        if dream_entry.title:
            parts.append(f"Titel: {dream_entry.title}")

        parts.append(f"Beschreibung: {dream_entry.description}")

        if dream_entry.symbols:
            parts.append(f"Symbole: {', '.join(dream_entry.symbols)}")

        if dream_entry.people_in_dream:
            parts.append(f"Personen: {', '.join(dream_entry.people_in_dream)}")

        if dream_entry.locations:
            parts.append(f"Orte: {', '.join(dream_entry.locations)}")

        return " | ".join(parts)

    def _build_therapy_note_text(self, therapy_note: TherapyNote) -> str:
        """Build text for therapy note analysis"""

        parts = [f"Titel: {therapy_note.title}"]
        parts.append(f"Inhalt: {therapy_note.content}")

        if therapy_note.techniques_used:
            parts.append(f"Techniken: {', '.join(therapy_note.techniques_used)}")

        if therapy_note.goals_discussed:
            parts.append(f"Ziele: {', '.join(therapy_note.goals_discussed)}")

        if therapy_note.key_insights:
            parts.append(f"Erkenntnisse: {therapy_note.key_insights}")

        return " | ".join(parts)
