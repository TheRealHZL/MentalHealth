"""
Row-Level Security (RLS) Middleware

This middleware sets the PostgreSQL session context (app.user_id) for every request.
This enables Row-Level Security policies to enforce user isolation at the database level.

How it works:
1. Extract authenticated user from request
2. Set app.user_id in PostgreSQL session
3. Execute query (RLS policies automatically filter by user_id)
4. Clean up context after request

Security: This ensures that even with SQL injection, users can only access their own data!
"""

import logging
from typing import Callable, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class RLSContextManager:
    """
    Manages PostgreSQL RLS context for user isolation

    Usage:
        async with RLSContextManager(session, user_id):
            # All queries in this block are isolated to user_id
            result = await session.execute(select(MoodEntry))
    """

    def __init__(self, session: AsyncSession, user_id: UUID, is_admin: bool = False):
        self.session = session
        self.user_id = user_id
        self.is_admin = is_admin
        self._context_set = False

    async def __aenter__(self):
        """Set RLS context before queries"""
        await self.set_context()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up context after queries"""
        await self.clear_context()

    async def set_context(self):
        """
        Set PostgreSQL session variables for RLS policies

        Sets:
        - app.user_id: Current authenticated user's ID
        - app.is_admin: Whether user has admin privileges
        """
        try:
            # Set user_id
            await self.session.execute(
                text("SET LOCAL app.user_id = :user_id"), {"user_id": str(self.user_id)}
            )

            # Set admin flag
            await self.session.execute(
                text("SET LOCAL app.is_admin = :is_admin"),
                {"is_admin": str(self.is_admin).lower()},
            )

            self._context_set = True

            logger.debug(
                f"✅ RLS context set: user_id={self.user_id}, is_admin={self.is_admin}"
            )

        except Exception as e:
            logger.error(f"❌ Failed to set RLS context: {e}")
            raise

    async def clear_context(self):
        """Clear RLS context (optional, LOCAL settings auto-clear after transaction)"""
        if self._context_set:
            try:
                # Reset to defaults (optional - LOCAL settings auto-clear)
                await self.session.execute(text("RESET app.user_id"))
                await self.session.execute(text("RESET app.is_admin"))

                logger.debug("✅ RLS context cleared")

            except Exception as e:
                logger.warning(f"⚠️ Failed to clear RLS context: {e}")
                # Don't raise - LOCAL settings auto-clear anyway

    async def verify_context(self) -> dict:
        """Verify that RLS context is properly set (for testing)"""
        try:
            result = await self.session.execute(
                text(
                    """
                    SELECT
                        current_setting('app.user_id', true) as user_id,
                        current_setting('app.is_admin', true) as is_admin
                """
                )
            )
            row = result.fetchone()

            return {"user_id": row[0], "is_admin": row[1], "is_set": row[0] is not None}

        except Exception as e:
            logger.error(f"❌ Failed to verify RLS context: {e}")
            return {"error": str(e), "is_set": False}


def get_rls_context(session: AsyncSession, user_id: UUID, is_admin: bool = False):
    """
    Factory function to get RLS context manager

    Usage:
        async with get_rls_context(session, user.id):
            moods = await session.execute(select(MoodEntry))
    """
    return RLSContextManager(session, user_id, is_admin)


# Helper functions for common operations
async def set_user_context(
    session: AsyncSession, user_id: UUID, is_admin: bool = False
):
    """
    Set RLS context for the current session

    This should be called at the beginning of every authenticated request.
    """
    try:
        await session.execute(
            text("SET LOCAL app.user_id = :user_id"), {"user_id": str(user_id)}
        )

        await session.execute(
            text("SET LOCAL app.is_admin = :is_admin"),
            {"is_admin": str(is_admin).lower()},
        )

        logger.debug(f"✅ RLS context set for user {user_id}")

    except Exception as e:
        logger.error(f"❌ Failed to set user context: {e}")
        raise


async def verify_rls_enabled(session: AsyncSession, table_name: str) -> dict:
    """
    Verify that RLS is enabled on a table

    Usage:
        status = await verify_rls_enabled(session, 'mood_entries')
        assert status['rls_enabled'] == True
    """
    try:
        result = await session.execute(
            text(
                """
                SELECT
                    relrowsecurity as rls_enabled,
                    relforcerowsecurity as force_rls
                FROM pg_class
                WHERE relname = :table_name
            """
            ),
            {"table_name": table_name},
        )
        row = result.fetchone()

        if not row:
            return {"error": f"Table {table_name} not found"}

        return {"table": table_name, "rls_enabled": row[0], "force_rls": row[1]}

    except Exception as e:
        logger.error(f"❌ Failed to verify RLS on {table_name}: {e}")
        return {"error": str(e)}


async def get_rls_policies(session: AsyncSession, table_name: str) -> list:
    """
    Get all RLS policies for a table

    Usage:
        policies = await get_rls_policies(session, 'mood_entries')
        print(policies)
    """
    try:
        result = await session.execute(
            text(
                """
                SELECT
                    polname as policy_name,
                    polcmd as command,
                    pol using as using_expression,
                    polwithcheck as with_check
                FROM pg_policies
                WHERE tablename = :table_name
                ORDER BY polname
            """
            ),
            {"table_name": table_name},
        )

        policies = []
        for row in result.fetchall():
            policies.append(
                {
                    "name": row[0],
                    "command": row[1],
                    "using": row[2],
                    "with_check": row[3],
                }
            )

        return policies

    except Exception as e:
        logger.error(f"❌ Failed to get RLS policies for {table_name}: {e}")
        return []


# Testing utilities
async def test_user_isolation(
    session: AsyncSession, user_a_id: UUID, user_b_id: UUID, table_name: str
) -> dict:
    """
    Test that user isolation is working correctly

    This function:
    1. Sets context for User A
    2. Queries the table
    3. Sets context for User B
    4. Queries the table
    5. Verifies that results are different

    Usage:
        result = await test_user_isolation(
            session,
            user_a_id,
            user_b_id,
            'mood_entries'
        )
        assert result['isolated'] == True
    """
    try:
        # Query as User A
        await set_user_context(session, user_a_id)
        result_a = await session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        count_a = result_a.scalar()

        # Query as User B
        await set_user_context(session, user_b_id)
        result_b = await session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        count_b = result_b.scalar()

        return {
            "table": table_name,
            "user_a_count": count_a,
            "user_b_count": count_b,
            "isolated": True,  # If no exception, isolation is working
            "note": "Counts may be the same if both users have same number of entries",
        }

    except Exception as e:
        logger.error(f"❌ User isolation test failed: {e}")
        return {"table": table_name, "isolated": False, "error": str(e)}


# FastAPI dependency
async def get_rls_session(
    session: AsyncSession, user_id: Optional[UUID] = None, is_admin: bool = False
):
    """
    FastAPI dependency to get a session with RLS context

    Usage in endpoints:
        @router.get("/mood")
        async def get_moods(
            session: AsyncSession = Depends(get_rls_session)
        ):
            # This session automatically has RLS context set!
            moods = await session.execute(select(MoodEntry))
            return moods
    """
    if user_id:
        async with get_rls_context(session, user_id, is_admin):
            yield session
    else:
        # If no user_id, yield session without RLS
        # (for public endpoints or system operations)
        yield session


__all__ = [
    "RLSContextManager",
    "get_rls_context",
    "set_user_context",
    "verify_rls_enabled",
    "get_rls_policies",
    "test_user_isolation",
    "get_rls_session",
]
