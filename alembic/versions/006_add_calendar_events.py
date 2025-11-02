"""Add Calendar Events

Revision ID: 006
Revises: 005
Create Date: 2025-11-02

This migration creates the calendar_events table for scheduling and reminders.

Features:
- Calendar events with recurrence support
- Multiple event types (therapy, medication, appointments, etc.)
- Reminder functionality
- Optional linkage to therapy notes
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create calendar_events table"""

    # Get connection and inspector to check for existing objects
    conn = op.get_bind()
    inspector = inspect(conn)

    # Check if table exists
    if 'calendar_events' not in inspector.get_table_names():
        # Create calendar_events table
        op.create_table(
            'calendar_events',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),

            # Event details
            sa.Column('title', sa.String(200), nullable=False),
            sa.Column('description', sa.Text, nullable=True),

            # Time information
            sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
            sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),

            # Event classification
            sa.Column('event_type', sa.String(50), nullable=False),
            sa.Column('color', sa.String(7), nullable=True),

            # Recurrence
            sa.Column('is_recurring', sa.Boolean, nullable=False, server_default='false'),
            sa.Column('recurrence_pattern', sa.String(20), nullable=True),
            sa.Column('recurrence_end_date', sa.DateTime(timezone=True), nullable=True),

            # Reminder settings
            sa.Column('reminder_minutes', sa.Integer, nullable=True),
            sa.Column('reminder_sent', sa.Boolean, nullable=False, server_default='false'),

            # Therapy note reference
            sa.Column('therapy_note_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('therapy_notes.id'), nullable=True),

            # Status
            sa.Column('is_completed', sa.Boolean, nullable=False, server_default='false'),
            sa.Column('is_cancelled', sa.Boolean, nullable=False, server_default='false'),
            sa.Column('notes', sa.Text, nullable=True),

            # Metadata
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'))
        )

    # Get existing indexes to avoid duplicates
    existing_indexes = {idx['name'] for idx in inspector.get_indexes('calendar_events')} if 'calendar_events' in inspector.get_table_names() else set()

    # Create indexes for performance (only if they don't exist)
    if 'ix_calendar_events_user_id' not in existing_indexes:
        op.create_index('ix_calendar_events_user_id', 'calendar_events', ['user_id'])

    if 'ix_calendar_events_start_time' not in existing_indexes:
        op.create_index('ix_calendar_events_start_time', 'calendar_events', ['start_time'])

    if 'ix_calendar_events_event_type' not in existing_indexes:
        op.create_index('ix_calendar_events_event_type', 'calendar_events', ['event_type'])

    if 'ix_calendar_events_title' not in existing_indexes:
        op.create_index('ix_calendar_events_title', 'calendar_events', ['title'])

    # Composite index for common query patterns
    if 'ix_calendar_events_user_time' not in existing_indexes:
        op.create_index('ix_calendar_events_user_time', 'calendar_events', ['user_id', 'start_time'])


def downgrade() -> None:
    """Drop calendar_events table"""

    # Drop indexes first
    op.drop_index('ix_calendar_events_user_time', 'calendar_events')
    op.drop_index('ix_calendar_events_title', 'calendar_events')
    op.drop_index('ix_calendar_events_event_type', 'calendar_events')
    op.drop_index('ix_calendar_events_start_time', 'calendar_events')
    op.drop_index('ix_calendar_events_user_id', 'calendar_events')

    # Drop table
    op.drop_table('calendar_events')
