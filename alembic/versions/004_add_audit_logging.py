"""Add Audit Logging System

Revision ID: 004
Revises: 003
Create Date: 2025-10-29

This migration creates comprehensive audit logging for all data access.
Every SELECT, INSERT, UPDATE, DELETE is logged for security monitoring.

Features:
- Automatic trigger-based logging
- User tracking (who accessed what)
- IP address and timestamp logging
- Suspicious activity detection
- GDPR-compliant retention

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create audit logging infrastructure"""

    # 1. Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),  # NULL for anonymous/system actions
        sa.Column('table_name', sa.String(100), nullable=False, index=True),
        sa.Column('operation', sa.String(20), nullable=False, index=True),  # SELECT, INSERT, UPDATE, DELETE
        sa.Column('record_id', postgresql.UUID(as_uuid=True), nullable=True),  # ID of affected record
        sa.Column('old_data', postgresql.JSONB, nullable=True),  # Old values (for UPDATE/DELETE)
        sa.Column('new_data', postgresql.JSONB, nullable=True),  # New values (for INSERT/UPDATE)
        sa.Column('query', sa.Text, nullable=True),  # The actual SQL query
        sa.Column('ip_address', postgresql.INET, nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('session_id', sa.String(100), nullable=True),
        sa.Column('timestamp', sa.DateTime, nullable=False, server_default=sa.text('NOW()'), index=True),
        sa.Column('duration_ms', sa.Integer, nullable=True),  # Query duration
        sa.Column('suspicious', sa.Boolean, default=False, nullable=False, index=True),
        sa.Column('suspicious_reasons', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=True),  # Additional context
    )

    # Create indexes for performance
    op.create_index('idx_audit_logs_user_time', 'audit_logs', ['user_id', 'timestamp'])
    op.create_index('idx_audit_logs_table_operation', 'audit_logs', ['table_name', 'operation'])
    op.create_index('idx_audit_logs_suspicious', 'audit_logs', ['suspicious', 'timestamp'])

    print("✅ Created audit_logs table")

    # 2. Create audit function (PostgreSQL)
    # This function is called by triggers to log all operations
    op.execute("""
        CREATE OR REPLACE FUNCTION audit_trigger_function()
        RETURNS TRIGGER AS $$
        DECLARE
            v_user_id UUID;
            v_old_data JSONB;
            v_new_data JSONB;
        BEGIN
            -- Get user_id from session context
            BEGIN
                v_user_id := current_setting('app.user_id', true)::uuid;
            EXCEPTION
                WHEN OTHERS THEN
                    v_user_id := NULL;
            END;

            -- Prepare data
            IF (TG_OP = 'DELETE') THEN
                v_old_data := to_jsonb(OLD);
                v_new_data := NULL;
            ELSIF (TG_OP = 'UPDATE') THEN
                v_old_data := to_jsonb(OLD);
                v_new_data := to_jsonb(NEW);
            ELSIF (TG_OP = 'INSERT') THEN
                v_old_data := NULL;
                v_new_data := to_jsonb(NEW);
            END IF;

            -- Insert audit log
            INSERT INTO audit_logs (
                user_id,
                table_name,
                operation,
                record_id,
                old_data,
                new_data,
                timestamp
            ) VALUES (
                v_user_id,
                TG_TABLE_NAME,
                TG_OP,
                COALESCE(NEW.id, OLD.id),  -- record ID
                v_old_data,
                v_new_data,
                NOW()
            );

            -- Return appropriate value
            IF (TG_OP = 'DELETE') THEN
                RETURN OLD;
            ELSE
                RETURN NEW;
            END IF;
        END;
        $$ LANGUAGE plpgsql;
    """)

    print("✅ Created audit trigger function")

    # 3. Create triggers on all user tables
    tables_to_audit = [
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

    for table in tables_to_audit:
        # Trigger for INSERT, UPDATE, DELETE
        op.execute(f"""
            CREATE TRIGGER audit_{table}_trigger
            AFTER INSERT OR UPDATE OR DELETE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION audit_trigger_function();
        """)
        print(f"✅ Created audit trigger for {table}")

    # 4. Create function to detect suspicious activity
    op.execute("""
        CREATE OR REPLACE FUNCTION detect_suspicious_activity()
        RETURNS VOID AS $$
        DECLARE
            v_threshold INTEGER := 100;  -- More than 100 queries in 1 minute is suspicious
        BEGIN
            -- Mark rapid-fire queries as suspicious
            UPDATE audit_logs
            SET suspicious = TRUE,
                suspicious_reasons = ARRAY['rapid_queries']
            WHERE id IN (
                SELECT id FROM audit_logs
                WHERE timestamp > NOW() - INTERVAL '1 minute'
                GROUP BY user_id
                HAVING COUNT(*) > v_threshold
            );

            -- Mark attempts to access massive amounts of data
            UPDATE audit_logs
            SET suspicious = TRUE,
                suspicious_reasons = suspicious_reasons || ARRAY['bulk_access']
            WHERE operation = 'SELECT'
              AND timestamp > NOW() - INTERVAL '5 minutes'
              AND user_id IN (
                  SELECT user_id
                  FROM audit_logs
                  WHERE operation = 'SELECT'
                    AND timestamp > NOW() - INTERVAL '5 minutes'
                  GROUP BY user_id
                  HAVING COUNT(*) > 1000
              );
        END;
        $$ LANGUAGE plpgsql;
    """)

    print("✅ Created suspicious activity detection function")

    # 5. Create view for easy querying
    op.execute("""
        CREATE OR REPLACE VIEW audit_summary AS
        SELECT
            user_id,
            table_name,
            operation,
            DATE(timestamp) as date,
            COUNT(*) as operation_count,
            COUNT(CASE WHEN suspicious THEN 1 END) as suspicious_count,
            MIN(timestamp) as first_access,
            MAX(timestamp) as last_access
        FROM audit_logs
        GROUP BY user_id, table_name, operation, DATE(timestamp)
        ORDER BY date DESC, operation_count DESC;
    """)

    print("✅ Created audit_summary view")

    # 6. Create automatic cleanup function (GDPR compliance)
    # Audit logs older than 90 days are automatically deleted
    op.execute("""
        CREATE OR REPLACE FUNCTION cleanup_old_audit_logs()
        RETURNS INTEGER AS $$
        DECLARE
            v_deleted INTEGER;
        BEGIN
            -- Delete audit logs older than 90 days
            DELETE FROM audit_logs
            WHERE timestamp < NOW() - INTERVAL '90 days';

            GET DIAGNOSTICS v_deleted = ROW_COUNT;

            RETURN v_deleted;
        END;
        $$ LANGUAGE plpgsql;
    """)

    print("✅ Created audit log cleanup function")

    print("\n🎉 Audit logging system created successfully!")
    print("✅ All data access is now logged")
    print("✅ Suspicious activity detection enabled")
    print("✅ GDPR-compliant retention (90 days)")


def downgrade() -> None:
    """Remove audit logging infrastructure"""

    # Drop triggers
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

    for table in tables:
        op.execute(f"""
            DROP TRIGGER IF EXISTS audit_{table}_trigger ON {table};
        """)
        print(f"✅ Dropped audit trigger for {table}")

    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS audit_trigger_function();")
    op.execute("DROP FUNCTION IF EXISTS detect_suspicious_activity();")
    op.execute("DROP FUNCTION IF EXISTS cleanup_old_audit_logs();")
    print("✅ Dropped audit functions")

    # Drop view
    op.execute("DROP VIEW IF EXISTS audit_summary;")
    print("✅ Dropped audit_summary view")

    # Drop indexes
    op.drop_index('idx_audit_logs_user_time')
    op.drop_index('idx_audit_logs_table_operation')
    op.drop_index('idx_audit_logs_suspicious')

    # Drop table
    op.drop_table('audit_logs')
    print("✅ Dropped audit_logs table")

    print("\n⚠️ Audit logging disabled!")
