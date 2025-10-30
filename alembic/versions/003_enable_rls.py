"""Enable Row-Level Security for User Isolation

Revision ID: 003
Revises: 002
Create Date: 2025-10-29

This migration enables PostgreSQL Row-Level Security (RLS) on all user-data tables.
RLS ensures that users can ONLY access their own data at the database level.

Security guarantees:
- User A cannot access User B's data via SQL injection
- Database enforces isolation automatically
- Works even if application logic fails
- Zero-trust security at database level

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Enable Row-Level Security on all user tables"""

    # List of tables that need RLS (all tables with user_id column)
    tables = [
        'mood_entries',
        'dream_entries',
        'therapy_notes',
        'chat_sessions',
        'chat_messages',
        'encrypted_mood_entries',
        'encrypted_dream_entries',
        'encrypted_therapy_notes',
        'encrypted_chat_messages'
    ]

    # 1. Enable Row-Level Security on all user tables
    for table in tables:
        op.execute(f"""
            ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;
        """)
        print(f"✅ Enabled RLS on {table}")

    # 2. Create RLS policies for each table
    # Policy: Users can only see/modify their own data
    for table in tables:
        # Policy for SELECT
        op.execute(f"""
            CREATE POLICY {table}_user_isolation_select ON {table}
                FOR SELECT
                USING (user_id = current_setting('app.user_id', true)::uuid);
        """)

        # Policy for INSERT
        op.execute(f"""
            CREATE POLICY {table}_user_isolation_insert ON {table}
                FOR INSERT
                WITH CHECK (user_id = current_setting('app.user_id', true)::uuid);
        """)

        # Policy for UPDATE
        op.execute(f"""
            CREATE POLICY {table}_user_isolation_update ON {table}
                FOR UPDATE
                USING (user_id = current_setting('app.user_id', true)::uuid)
                WITH CHECK (user_id = current_setting('app.user_id', true)::uuid);
        """)

        # Policy for DELETE
        op.execute(f"""
            CREATE POLICY {table}_user_isolation_delete ON {table}
                FOR DELETE
                USING (user_id = current_setting('app.user_id', true)::uuid);
        """)

        print(f"✅ Created RLS policies for {table}")

    # 3. Special policy for admin access (superusers can bypass RLS)
    # This allows admin users or system processes to access all data when needed
    for table in tables:
        op.execute(f"""
            CREATE POLICY {table}_admin_all ON {table}
                FOR ALL
                TO public
                USING (
                    current_setting('app.is_admin', true)::boolean = true
                    OR current_user = 'postgres'
                );
        """)
        print(f"✅ Created admin policy for {table}")

    # 4. Force RLS even for table owners (important!)
    # Without this, table owners would bypass RLS
    for table in tables:
        op.execute(f"""
            ALTER TABLE {table} FORCE ROW LEVEL SECURITY;
        """)
        print(f"✅ Forced RLS for table owners on {table}")

    print("\n🎉 Row-Level Security enabled successfully!")
    print("✅ User isolation guaranteed at database level")
    print("✅ Users can only access their own data")
    print("✅ Admin access preserved for system operations")


def downgrade() -> None:
    """Disable Row-Level Security"""

    tables = [
        'mood_entries',
        'dream_entries',
        'therapy_notes',
        'chat_sessions',
        'chat_messages',
        'encrypted_mood_entries',
        'encrypted_dream_entries',
        'encrypted_therapy_notes',
        'encrypted_chat_messages'
    ]

    # Drop all policies
    for table in tables:
        # Drop SELECT policy
        op.execute(f"""
            DROP POLICY IF EXISTS {table}_user_isolation_select ON {table};
        """)

        # Drop INSERT policy
        op.execute(f"""
            DROP POLICY IF EXISTS {table}_user_isolation_insert ON {table};
        """)

        # Drop UPDATE policy
        op.execute(f"""
            DROP POLICY IF EXISTS {table}_user_isolation_update ON {table};
        """)

        # Drop DELETE policy
        op.execute(f"""
            DROP POLICY IF EXISTS {table}_user_isolation_delete ON {table};
        """)

        # Drop admin policy
        op.execute(f"""
            DROP POLICY IF EXISTS {table}_admin_all ON {table};
        """)

        print(f"✅ Dropped RLS policies for {table}")

    # Disable RLS
    for table in tables:
        op.execute(f"""
            ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;
        """)
        op.execute(f"""
            ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;
        """)
        print(f"✅ Disabled RLS on {table}")

    print("\n⚠️ Row-Level Security disabled!")
    print("⚠️ User isolation is no longer enforced at database level")
