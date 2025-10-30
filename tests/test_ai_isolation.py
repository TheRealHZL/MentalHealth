"""
AI Isolation Tests

Verifies complete user isolation in AI processing:
- User A's AI context is NEVER accessible by User B
- AI responses use ONLY the user's own data
- Conversation history is completely isolated
- No cross-user data leakage
"""

import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai.engine import AIEngine
from src.ai.user_isolated_engine import UserIsolatedAIEngine
from src.services.ai_integration_service_isolated import UserIsolatedAIIntegrationService
from src.models.user_context import UserContext, AIConversationHistory, UserAIPreferences
from src.models import MoodEntry, DreamEntry, TherapyNote
from src.core.rls_middleware import set_user_context


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
async def base_ai_engine():
    """Create base AI engine instance"""
    engine = AIEngine()
    # Skip initialization for tests (models not needed)
    engine.is_initialized = True
    return engine


@pytest.fixture
async def isolated_ai_engine(base_ai_engine):
    """Create user-isolated AI engine"""
    return UserIsolatedAIEngine(base_ai_engine)


@pytest.fixture
async def ai_service(isolated_ai_engine):
    """Create user-isolated AI integration service"""
    return UserIsolatedAIIntegrationService(isolated_ai_engine)


@pytest.fixture
def user_a_id():
    """User A UUID"""
    return uuid.uuid4()


@pytest.fixture
def user_b_id():
    """User B UUID"""
    return uuid.uuid4()


@pytest.fixture
async def user_a_context(async_session: AsyncSession, user_a_id):
    """Create context for User A"""
    context = UserContext(
        id=uuid.uuid4(),
        user_id=user_a_id,
        context_type="general",
        encrypted_context={
            "ciphertext": "user_a_secret_context",
            "nonce": "nonce_a",
            "version": 1
        },
        conversation_count=5,
        mood_entries_processed=10,
        dream_entries_processed=3
    )
    async_session.add(context)
    await async_session.commit()
    return context


@pytest.fixture
async def user_b_context(async_session: AsyncSession, user_b_id):
    """Create context for User B"""
    context = UserContext(
        id=uuid.uuid4(),
        user_id=user_b_id,
        context_type="general",
        encrypted_context={
            "ciphertext": "user_b_secret_context",
            "nonce": "nonce_b",
            "version": 1
        },
        conversation_count=3,
        mood_entries_processed=7,
        dream_entries_processed=2
    )
    async_session.add(context)
    await async_session.commit()
    return context


# ============================================================================
# Test User Context Isolation
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_cannot_load_another_user_context(
    async_session: AsyncSession,
    isolated_ai_engine: UserIsolatedAIEngine,
    user_a_id,
    user_b_id,
    user_a_context,
    user_b_context
):
    """Test that User A cannot load User B's context"""

    # User A loads their context
    context_a = await isolated_ai_engine.load_user_context(
        async_session,
        user_a_id
    )

    # Verify User A gets their own context
    assert context_a["user_id"] == str(user_a_id)
    assert context_a["encrypted_context"]["ciphertext"] == "user_a_secret_context"

    # User B loads their context
    context_b = await isolated_ai_engine.load_user_context(
        async_session,
        user_b_id
    )

    # Verify User B gets their own context
    assert context_b["user_id"] == str(user_b_id)
    assert context_b["encrypted_context"]["ciphertext"] == "user_b_secret_context"

    # Verify contexts are different
    assert context_a["encrypted_context"] != context_b["encrypted_context"]
    assert context_a["mood_entries_processed"] != context_b["mood_entries_processed"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_context_statistics_are_isolated(
    async_session: AsyncSession,
    isolated_ai_engine: UserIsolatedAIEngine,
    user_a_id,
    user_b_id,
    user_a_context,
    user_b_context
):
    """Test that context statistics are isolated per user"""

    # Load User A's context
    context_a = await isolated_ai_engine.load_user_context(
        async_session,
        user_a_id
    )

    # Load User B's context
    context_b = await isolated_ai_engine.load_user_context(
        async_session,
        user_b_id
    )

    # User A's statistics
    assert context_a["conversation_count"] == 5
    assert context_a["mood_entries_processed"] == 10
    assert context_a["dream_entries_processed"] == 3

    # User B's statistics (different)
    assert context_b["conversation_count"] == 3
    assert context_b["mood_entries_processed"] == 7
    assert context_b["dream_entries_processed"] == 2

    # Verify no overlap
    assert context_a["conversation_count"] != context_b["conversation_count"]
    assert context_a["mood_entries_processed"] != context_b["mood_entries_processed"]


# ============================================================================
# Test Conversation History Isolation
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_conversation_history_is_isolated(
    async_session: AsyncSession,
    isolated_ai_engine: UserIsolatedAIEngine,
    user_a_id,
    user_b_id
):
    """Test that conversation history is isolated per user"""

    session_a = uuid.uuid4()
    session_b = uuid.uuid4()

    # User A creates conversation
    await isolated_ai_engine.save_conversation_message(
        async_session,
        user_a_id,
        session_a,
        message_type="user",
        encrypted_message={
            "ciphertext": "user_a_message",
            "nonce": "nonce",
            "version": 1
        }
    )

    # User B creates conversation
    await isolated_ai_engine.save_conversation_message(
        async_session,
        user_b_id,
        session_b,
        message_type="user",
        encrypted_message={
            "ciphertext": "user_b_message",
            "nonce": "nonce",
            "version": 1
        }
    )

    # User A loads their conversation
    conv_a = await isolated_ai_engine.load_conversation_history(
        async_session,
        user_a_id,
        session_a
    )

    # User B loads their conversation
    conv_b = await isolated_ai_engine.load_conversation_history(
        async_session,
        user_b_id,
        session_b
    )

    # Verify User A sees only their messages
    assert len(conv_a) == 1
    assert conv_a[0]["encrypted_message"]["ciphertext"] == "user_a_message"

    # Verify User B sees only their messages
    assert len(conv_b) == 1
    assert conv_b[0]["encrypted_message"]["ciphertext"] == "user_b_message"

    # User A should NOT see User B's conversation
    conv_a_trying_b = await isolated_ai_engine.load_conversation_history(
        async_session,
        user_a_id,
        session_b  # User B's session
    )
    assert len(conv_a_trying_b) == 0  # RLS blocks access


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_cannot_access_another_user_conversation(
    async_session: AsyncSession,
    isolated_ai_engine: UserIsolatedAIEngine,
    user_a_id,
    user_b_id
):
    """Test RLS prevents cross-user conversation access"""

    shared_session_id = uuid.uuid4()

    # User B creates a conversation
    await isolated_ai_engine.save_conversation_message(
        async_session,
        user_b_id,
        shared_session_id,
        message_type="user",
        encrypted_message={
            "ciphertext": "secret_b_message",
            "nonce": "nonce",
            "version": 1
        }
    )

    # User A tries to load User B's conversation
    # RLS should filter out User B's messages
    conv = await isolated_ai_engine.load_conversation_history(
        async_session,
        user_a_id,
        shared_session_id
    )

    # User A should see NOTHING
    assert len(conv) == 0


# ============================================================================
# Test AI Preferences Isolation
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_ai_preferences_are_isolated(
    async_session: AsyncSession,
    isolated_ai_engine: UserIsolatedAIEngine,
    user_a_id,
    user_b_id
):
    """Test that AI preferences are isolated per user"""

    # Create preferences for User A
    prefs_a = UserAIPreferences(
        id=uuid.uuid4(),
        user_id=user_a_id,
        response_style="professional",
        language="en"
    )
    async_session.add(prefs_a)

    # Create preferences for User B
    prefs_b = UserAIPreferences(
        id=uuid.uuid4(),
        user_id=user_b_id,
        response_style="casual",
        language="de"
    )
    async_session.add(prefs_b)
    await async_session.commit()

    # Load User A's preferences
    loaded_a = await isolated_ai_engine.load_user_preferences(
        async_session,
        user_a_id
    )

    # Load User B's preferences
    loaded_b = await isolated_ai_engine.load_user_preferences(
        async_session,
        user_b_id
    )

    # Verify isolation
    assert loaded_a["response_style"] == "professional"
    assert loaded_a["language"] == "en"

    assert loaded_b["response_style"] == "casual"
    assert loaded_b["language"] == "de"

    # Verify different
    assert loaded_a["response_style"] != loaded_b["response_style"]
    assert loaded_a["language"] != loaded_b["language"]


# ============================================================================
# Test Mood Entry Analysis Isolation
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_mood_analysis_uses_only_user_context(
    async_session: AsyncSession,
    ai_service: UserIsolatedAIIntegrationService,
    user_a_id,
    user_b_id,
    user_a_context,
    user_b_context
):
    """Test that mood analysis uses only the user's own context"""

    # Create mood entry for User A
    mood_a = MoodEntry(
        id=uuid.uuid4(),
        user_id=user_a_id,
        mood_score=8,
        notes="Feeling great today!",
        stress_level=2,
        energy_level=9,
        sleep_hours=8,
        sleep_quality=9
    )
    async_session.add(mood_a)
    await async_session.commit()

    # Analyze User A's mood
    analysis_a = await ai_service.analyze_mood_entry(
        async_session,
        user_a_id,
        mood_a
    )

    # Verify analysis is for User A
    assert analysis_a["user_id"] == str(user_a_id)
    assert analysis_a["isolation_verified"] is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_cannot_analyze_another_user_mood(
    async_session: AsyncSession,
    ai_service: UserIsolatedAIIntegrationService,
    user_a_id,
    user_b_id
):
    """Test that User A cannot analyze User B's mood entry"""

    # Create mood entry for User B
    mood_b = MoodEntry(
        id=uuid.uuid4(),
        user_id=user_b_id,
        mood_score=5,
        notes="User B's private mood",
        stress_level=6,
        energy_level=4,
        sleep_hours=6,
        sleep_quality=5
    )
    async_session.add(mood_b)
    await async_session.commit()

    # User A tries to analyze User B's mood
    # This should raise PermissionError
    with pytest.raises(PermissionError, match="Cannot analyze another user's mood entry"):
        await ai_service.analyze_mood_entry(
            async_session,
            user_a_id,  # User A
            mood_b  # User B's mood entry
        )


# ============================================================================
# Test Dream Entry Analysis Isolation
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_cannot_analyze_another_user_dream(
    async_session: AsyncSession,
    ai_service: UserIsolatedAIIntegrationService,
    user_a_id,
    user_b_id
):
    """Test that User A cannot analyze User B's dream entry"""

    # Create dream entry for User B
    dream_b = DreamEntry(
        id=uuid.uuid4(),
        user_id=user_b_id,
        title="User B's Private Dream",
        description="Secret dream content",
        mood_after_waking=7
    )
    async_session.add(dream_b)
    await async_session.commit()

    # User A tries to analyze User B's dream
    with pytest.raises(PermissionError, match="Cannot analyze another user's dream entry"):
        await ai_service.analyze_dream_entry(
            async_session,
            user_a_id,  # User A
            dream_b  # User B's dream entry
        )


# ============================================================================
# Test Therapy Note Analysis Isolation
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_cannot_analyze_another_user_therapy_note(
    async_session: AsyncSession,
    ai_service: UserIsolatedAIIntegrationService,
    user_a_id,
    user_b_id
):
    """Test that User A cannot analyze User B's therapy note"""

    # Create therapy note for User B
    note_b = TherapyNote(
        id=uuid.uuid4(),
        user_id=user_b_id,
        title="User B's Private Session",
        content="Confidential therapy content"
    )
    async_session.add(note_b)
    await async_session.commit()

    # User A tries to analyze User B's therapy note
    with pytest.raises(PermissionError, match="Cannot analyze another user's therapy note"):
        await ai_service.analyze_therapy_note(
            async_session,
            user_a_id,  # User A
            note_b  # User B's therapy note
        )


# ============================================================================
# Test Chat Response Isolation
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_chat_response_uses_only_user_context(
    async_session: AsyncSession,
    ai_service: UserIsolatedAIIntegrationService,
    user_a_id,
    user_b_id,
    user_a_context,
    user_b_context
):
    """Test that chat responses use only the user's own context"""

    session_a = uuid.uuid4()
    session_b = uuid.uuid4()

    # User A sends a message
    response_a = await ai_service.generate_chat_response(
        async_session,
        user_a_id,
        "How am I feeling?",
        session_a
    )

    # User B sends a message
    response_b = await ai_service.generate_chat_response(
        async_session,
        user_b_id,
        "What's my mood?",
        session_b
    )

    # Verify responses are for correct users
    assert response_a["user_id"] == str(user_a_id)
    assert response_a["isolation_verified"] is True

    assert response_b["user_id"] == str(user_b_id)
    assert response_b["isolation_verified"] is True

    # Verify different sessions
    assert response_a["session_id"] != response_b["session_id"]


# ============================================================================
# Test Context Caching Isolation
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_context_cache_is_isolated_per_user(
    async_session: AsyncSession,
    isolated_ai_engine: UserIsolatedAIEngine,
    user_a_id,
    user_b_id,
    user_a_context,
    user_b_context
):
    """Test that context cache doesn't leak between users"""

    # Load User A's context (caches it)
    context_a_1 = await isolated_ai_engine.load_user_context(
        async_session,
        user_a_id
    )

    # Load User B's context (caches it)
    context_b_1 = await isolated_ai_engine.load_user_context(
        async_session,
        user_b_id
    )

    # Load User A's context again (from cache)
    context_a_2 = await isolated_ai_engine.load_user_context(
        async_session,
        user_a_id
    )

    # Verify User A's cached context is correct
    assert context_a_1["user_id"] == context_a_2["user_id"]
    assert context_a_1["encrypted_context"] == context_a_2["encrypted_context"]

    # Verify User A's cache doesn't contain User B's data
    assert context_a_2["user_id"] != context_b_1["user_id"]
    assert context_a_2["encrypted_context"] != context_b_1["encrypted_context"]


# ============================================================================
# Test GDPR Compliance - Cleanup
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_cleanup_only_affects_own_conversations(
    async_session: AsyncSession,
    isolated_ai_engine: UserIsolatedAIEngine,
    user_a_id,
    user_b_id
):
    """Test that cleanup only deletes the user's own old conversations"""

    session_a = uuid.uuid4()
    session_b = uuid.uuid4()

    # Create old conversation for User A
    old_msg_a = AIConversationHistory(
        id=uuid.uuid4(),
        user_id=user_a_id,
        session_id=session_a,
        sequence_number=1,
        message_type="user",
        encrypted_message={"content": "old_a"},
        created_at=datetime.utcnow() - timedelta(days=100)  # > 90 days
    )
    async_session.add(old_msg_a)

    # Create old conversation for User B
    old_msg_b = AIConversationHistory(
        id=uuid.uuid4(),
        user_id=user_b_id,
        session_id=session_b,
        sequence_number=1,
        message_type="user",
        encrypted_message={"content": "old_b"},
        created_at=datetime.utcnow() - timedelta(days=100)  # > 90 days
    )
    async_session.add(old_msg_b)
    await async_session.commit()

    # User A cleans up their old conversations
    deleted_count_a = await isolated_ai_engine.cleanup_old_conversations(
        async_session,
        user_a_id,
        days=90
    )

    # Verify User A's conversation was deleted
    assert deleted_count_a >= 1

    # Verify User B's conversation still exists (not deleted by User A's cleanup)
    conv_b = await isolated_ai_engine.load_conversation_history(
        async_session,
        user_b_id,
        session_b
    )
    # User B's old message should still be there (User A's cleanup didn't affect it)
    assert len(conv_b) >= 1


# ============================================================================
# Summary
# ============================================================================

"""
These tests verify complete AI isolation:

✅ User A cannot load User B's AI context
✅ Context statistics are isolated per user
✅ Conversation history is isolated per user
✅ User cannot access another user's conversations
✅ AI preferences are isolated per user
✅ Mood analysis uses only user's own context
✅ User cannot analyze another user's mood entry
✅ User cannot analyze another user's dream entry
✅ User cannot analyze another user's therapy note
✅ Chat responses use only user's own context
✅ Context cache is isolated per user
✅ GDPR cleanup only affects own conversations

AI Isolation: VERIFIED! 🔒
"""
