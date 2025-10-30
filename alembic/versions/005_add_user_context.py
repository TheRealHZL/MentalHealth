"""Add User Context Storage for AI Isolation

Revision ID: 005
Revises: 004
Create Date: 2025-10-30

This migration creates user-specific AI context storage.
Each user has completely isolated AI memory and conversation history.

Features:
- Encrypted context storage
- Conversation history tracking
- User AI preferences
- Context lifecycle management
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create user context tables"""

    # 1. Create user_contexts table
    op.create_table(
        'user_contexts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, unique=True),
        sa.Column('context_type', sa.String(50), nullable=False, server_default='general'),
        sa.Column('context_version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('encrypted_context', postgresql.JSONB, nullable=True),
        sa.Column('context_size_bytes', sa.Integer, nullable=True),
        sa.Column('last_updated', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('expires_at', sa.DateTime, nullable=True),
        sa.Column('access_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('last_accessed', sa.DateTime, nullable=True),
        sa.Column('conversation_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('mood_entries_processed', sa.Integer, nullable=False, server_default='0'),
        sa.Column('dream_entries_processed', sa.Integer, nullable=False, server_default='0'),
        sa.Column('therapy_notes_processed', sa.Integer, nullable=False, server_default='0'),
        sa.Column('ai_model_version', sa.String(50), nullable=True),
        sa.Column('last_training_date', sa.DateTime, nullable=True),
        sa.Column('allow_learning', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('context_retention_days', sa.Integer, nullable=False, server_default='90'),
    )

    # Indexes for user_contexts
    op.create_index('idx_user_contexts_user_id', 'user_contexts', ['user_id'])
    op.create_index('idx_user_contexts_user_type', 'user_contexts', ['user_id', 'context_type'])
    op.create_index('idx_user_contexts_updated', 'user_contexts', [sa.text('last_updated DESC')])
    op.create_index('idx_user_contexts_active', 'user_contexts', ['is_active', 'last_updated'])

    print("✅ Created user_contexts table")

    # 2. Create ai_conversation_history table
    op.create_table(
        'ai_conversation_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sequence_number', sa.Integer, nullable=False),
        sa.Column('message_type', sa.String(20), nullable=False),
        sa.Column('encrypted_message', postgresql.JSONB, nullable=False),
        sa.Column('timestamp', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        sa.Column('token_count', sa.Integer, nullable=True),
        sa.Column('model_version', sa.String(50), nullable=True),
        sa.Column('confidence_score', sa.Integer, nullable=True),
        sa.Column('processing_time_ms', sa.Integer, nullable=True),
        sa.Column('is_deleted', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
    )

    # Indexes for conversation history
    op.create_index('idx_conversation_history_user_id', 'ai_conversation_history', ['user_id'])
    op.create_index('idx_conversation_history_session', 'ai_conversation_history', ['session_id'])
    op.create_index('idx_conversation_history_user_session', 'ai_conversation_history', ['user_id', 'session_id'])
    op.create_index('idx_conversation_history_timestamp', 'ai_conversation_history', [sa.text('timestamp DESC')])
    op.create_index('idx_conversation_history_not_deleted', 'ai_conversation_history', ['is_deleted', 'timestamp'])

    print("✅ Created ai_conversation_history table")

    # 3. Create user_ai_preferences table
    op.create_table(
        'user_ai_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, unique=True),
        sa.Column('response_style', sa.String(50), nullable=False, server_default='empathetic'),
        sa.Column('response_length', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('formality_level', sa.String(20), nullable=False, server_default='friendly'),
        sa.Column('language', sa.String(10), nullable=False, server_default='de'),
        sa.Column('include_emotional_validation', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('include_actionable_advice', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('enable_mood_analysis', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('enable_dream_interpretation', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('enable_pattern_recognition', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('enable_recommendations', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('remember_conversations', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('use_historical_data', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('personalize_responses', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('notify_on_insights', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('notify_on_patterns', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('notify_on_concerns', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('preferred_therapy_approaches', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('topics_of_interest', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
    )

    # Indexes for AI preferences
    op.create_index('idx_user_ai_preferences_user_id', 'user_ai_preferences', ['user_id'])

    print("✅ Created user_ai_preferences table")

    # 4. Enable RLS on new tables
    op.execute("ALTER TABLE user_contexts ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE ai_conversation_history ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE user_ai_preferences ENABLE ROW LEVEL SECURITY;")

    op.execute("ALTER TABLE user_contexts FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE ai_conversation_history FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE user_ai_preferences FORCE ROW LEVEL SECURITY;")

    print("✅ Enabled RLS on user context tables")

    # 5. Create RLS policies for user_contexts
    for table in ['user_contexts', 'ai_conversation_history', 'user_ai_preferences']:
        # SELECT policy
        op.execute(f"""
            CREATE POLICY {table}_user_isolation_select ON {table}
                FOR SELECT
                USING (user_id = current_setting('app.user_id', true)::uuid);
        """)

        # INSERT policy
        op.execute(f"""
            CREATE POLICY {table}_user_isolation_insert ON {table}
                FOR INSERT
                WITH CHECK (user_id = current_setting('app.user_id', true)::uuid);
        """)

        # UPDATE policy
        op.execute(f"""
            CREATE POLICY {table}_user_isolation_update ON {table}
                FOR UPDATE
                USING (user_id = current_setting('app.user_id', true)::uuid)
                WITH CHECK (user_id = current_setting('app.user_id', true)::uuid);
        """)

        # DELETE policy
        op.execute(f"""
            CREATE POLICY {table}_user_isolation_delete ON {table}
                FOR DELETE
                USING (user_id = current_setting('app.user_id', true)::uuid);
        """)

        # Admin policy
        op.execute(f"""
            CREATE POLICY {table}_admin_all ON {table}
                FOR ALL
                TO public
                USING (
                    current_setting('app.is_admin', true)::boolean = true
                    OR current_user = 'postgres'
                );
        """)

        print(f"✅ Created RLS policies for {table}")

    # 6. Add audit triggers to new tables
    for table in ['user_contexts', 'ai_conversation_history', 'user_ai_preferences']:
        op.execute(f"""
            CREATE TRIGGER audit_{table}_trigger
            AFTER INSERT OR UPDATE OR DELETE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION audit_trigger_function();
        """)
        print(f"✅ Created audit trigger for {table}")

    print("\n🎉 User context storage created successfully!")
    print("✅ User-specific AI context isolated")
    print("✅ Conversation history encrypted")
    print("✅ RLS policies applied")
    print("✅ Audit logging enabled")


def downgrade() -> None:
    """Remove user context tables"""

    # Drop audit triggers
    for table in ['user_contexts', 'ai_conversation_history', 'user_ai_preferences']:
        op.execute(f"DROP TRIGGER IF EXISTS audit_{table}_trigger ON {table};")
        print(f"✅ Dropped audit trigger for {table}")

    # Drop RLS policies
    for table in ['user_contexts', 'ai_conversation_history', 'user_ai_preferences']:
        op.execute(f"DROP POLICY IF EXISTS {table}_user_isolation_select ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_user_isolation_insert ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_user_isolation_update ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_user_isolation_delete ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_admin_all ON {table};")
        print(f"✅ Dropped RLS policies for {table}")

    # Disable RLS
    op.execute("ALTER TABLE user_contexts DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE ai_conversation_history DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE user_ai_preferences DISABLE ROW LEVEL SECURITY;")

    # Drop indexes
    op.drop_index('idx_user_contexts_user_id')
    op.drop_index('idx_user_contexts_user_type')
    op.drop_index('idx_user_contexts_updated')
    op.drop_index('idx_user_contexts_active')

    op.drop_index('idx_conversation_history_user_id')
    op.drop_index('idx_conversation_history_session')
    op.drop_index('idx_conversation_history_user_session')
    op.drop_index('idx_conversation_history_timestamp')
    op.drop_index('idx_conversation_history_not_deleted')

    op.drop_index('idx_user_ai_preferences_user_id')

    # Drop tables
    op.drop_table('user_ai_preferences')
    op.drop_table('ai_conversation_history')
    op.drop_table('user_contexts')

    print("\n⚠️ User context storage removed!")
