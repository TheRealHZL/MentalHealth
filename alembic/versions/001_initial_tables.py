"""
Initial Migration - Create all tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_initial_tables'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Create all tables for MindBridge AI Platform"""
    
    # Users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('role', sa.String(20), nullable=False, server_default='patient'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('registration_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('date_of_birth', sa.DateTime(), nullable=True),
        sa.Column('timezone', sa.String(50), server_default='Europe/Berlin'),
        sa.Column('profile_picture_url', sa.String(500), nullable=True),
        sa.Column('notification_preferences', sa.JSON(), nullable=True),
        sa.Column('privacy_settings', sa.JSON(), nullable=True),
        # Therapist-specific fields
        sa.Column('license_number', sa.String(100), nullable=True),
        sa.Column('specializations', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('practice_address', sa.Text(), nullable=True),
        sa.Column('phone_number', sa.String(20), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('license_file_path', sa.String(500), nullable=True),
        # Verification fields
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('verification_notes', sa.Text(), nullable=True),
        sa.Column('verification_rejected', sa.Boolean(), server_default='false'),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # Create indexes for users
    op.create_index('ix_users_email_active', 'users', ['email', 'is_active'])
    op.create_index('ix_users_role_verified', 'users', ['role', 'is_verified'])
    
    # Login attempts table
    op.create_table('login_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('successful', sa.Boolean(), nullable=False),
        sa.Column('attempted_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('failure_reason', sa.String(100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'])
    )
    
    op.create_index('ix_login_attempts_email_time', 'login_attempts', ['email', 'attempted_at'])
    
    # User sessions table
    op.create_table('user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_token', sa.String(255), nullable=False),
        sa.Column('refresh_token', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('last_activity', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('revocation_reason', sa.String(100), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('device_info', sa.JSON(), nullable=True),
        sa.Column('location_info', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.UniqueConstraint('session_token'),
        sa.UniqueConstraint('refresh_token')
    )
    
    op.create_index('ix_user_sessions_user_active', 'user_sessions', ['user_id', 'is_active'])
    
    # Mood entries table
    op.create_table('mood_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entry_date', sa.Date(), nullable=False),
        sa.Column('mood_score', sa.Integer(), nullable=False),
        sa.Column('stress_level', sa.Integer(), nullable=False),
        sa.Column('energy_level', sa.Integer(), nullable=False),
        # Sleep data
        sa.Column('sleep_hours', sa.Float(), nullable=True),
        sa.Column('sleep_quality', sa.Integer(), nullable=True),
        sa.Column('sleep_notes', sa.Text(), nullable=True),
        # Physical health
        sa.Column('exercise_minutes', sa.Integer(), nullable=True),
        sa.Column('exercise_type', sa.String(100), nullable=True),
        # Activities and context
        sa.Column('activities', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('location', sa.String(200), nullable=True),
        sa.Column('weather', sa.String(50), nullable=True),
        # Mental health specifics
        sa.Column('symptoms', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('triggers', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('coping_strategies', postgresql.ARRAY(sa.String()), nullable=True),
        # Medication
        sa.Column('medication_taken', sa.Boolean(), server_default='false'),
        sa.Column('medication_names', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('medication_effects', sa.Text(), nullable=True),
        sa.Column('medication_notes', sa.Text(), nullable=True),
        # Social and emotional context
        sa.Column('social_interactions', sa.Integer(), nullable=True),
        sa.Column('relationship_quality', sa.Integer(), nullable=True),
        sa.Column('work_stress', sa.Integer(), nullable=True),
        # Free text
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('gratitude', sa.Text(), nullable=True),
        sa.Column('goals_achieved', postgresql.ARRAY(sa.String()), nullable=True),
        # AI-generated insights
        sa.Column('ai_mood_analysis', sa.JSON(), nullable=True),
        sa.Column('ai_recommendations', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('ai_sentiment_score', sa.Float(), nullable=True),
        # Metadata
        sa.Column('entry_duration_seconds', sa.Integer(), nullable=True),
        sa.Column('is_private', sa.Boolean(), server_default='true'),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'])
    )
    
    op.create_index('ix_mood_entries_user_date', 'mood_entries', ['user_id', 'entry_date'])
    op.create_index('ix_mood_entries_date_score', 'mood_entries', ['entry_date', 'mood_score'])
    
    # Dream entries table
    op.create_table('dream_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dream_date', sa.Date(), nullable=False),
        sa.Column('dream_type', sa.String(20), server_default='normal', nullable=False),
        sa.Column('title', sa.String(200), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        # Dream characteristics
        sa.Column('vividness', sa.Integer(), nullable=True),
        sa.Column('emotional_intensity', sa.Integer(), nullable=True),
        sa.Column('mood_during_dream', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('mood_after_waking', sa.Integer(), nullable=False),
        # Dream content
        sa.Column('people_in_dream', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('locations', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('objects', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('colors', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('symbols', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('emotions_felt', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('physical_sensations', postgresql.ARRAY(sa.String()), nullable=True),
        # Sleep context
        sa.Column('sleep_quality', sa.Integer(), nullable=True),
        sa.Column('time_to_sleep', sa.String(10), nullable=True),
        sa.Column('wake_up_time', sa.String(10), nullable=True),
        sa.Column('sleep_duration', sa.Float(), nullable=True),
        # Lucid dreaming
        sa.Column('became_lucid', sa.Boolean(), server_default='false'),
        sa.Column('lucidity_trigger', sa.String(200), nullable=True),
        sa.Column('lucid_actions', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('lucid_control_level', sa.Integer(), nullable=True),
        # Personal interpretation
        sa.Column('personal_interpretation', sa.Text(), nullable=True),
        sa.Column('life_connection', sa.Text(), nullable=True),
        sa.Column('recurring_elements', postgresql.ARRAY(sa.String()), nullable=True),
        # AI analysis
        sa.Column('ai_dream_analysis', sa.JSON(), nullable=True),
        sa.Column('symbol_interpretations', sa.JSON(), nullable=True),
        sa.Column('emotional_insights', postgresql.ARRAY(sa.String()), nullable=True),
        # Metadata
        sa.Column('dream_recall_clarity', sa.Integer(), nullable=True),
        sa.Column('entry_delay_hours', sa.Integer(), nullable=True),
        sa.Column('is_private', sa.Boolean(), server_default='true'),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'])
    )
    
    op.create_index('ix_dream_entries_user_date', 'dream_entries', ['user_id', 'dream_date'])
    op.create_index('ix_dream_entries_type_date', 'dream_entries', ['dream_type', 'dream_date'])
    
    # Therapy notes table
    op.create_table('therapy_notes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('note_date', sa.Date(), nullable=False),
        sa.Column('note_type', sa.String(30), server_default='self_reflection', nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        # Session information
        sa.Column('session_number', sa.Integer(), nullable=True),
        sa.Column('therapist_name', sa.String(200), nullable=True),
        sa.Column('session_duration', sa.Integer(), nullable=True),
        sa.Column('session_format', sa.String(20), nullable=True),
        # Therapy techniques and methods
        sa.Column('techniques_used', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('homework_assigned', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('homework_completed', postgresql.ARRAY(sa.String()), nullable=True),
        # Goals and progress
        sa.Column('goals_discussed', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('goals_achieved', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('progress_made', sa.Text(), nullable=True),
        sa.Column('challenges_faced', postgresql.ARRAY(sa.String()), nullable=True),
        # Emotional state
        sa.Column('mood_before_session', sa.Integer(), nullable=True),
        sa.Column('mood_after_session', sa.Integer(), nullable=True),
        sa.Column('anxiety_level', sa.Integer(), nullable=True),
        sa.Column('key_emotions', postgresql.ARRAY(sa.String()), nullable=True),
        # Insights and breakthroughs
        sa.Column('key_insights', sa.Text(), nullable=True),
        sa.Column('breakthrough_moments', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('patterns_recognized', postgresql.ARRAY(sa.String()), nullable=True),
        # Action items and next steps
        sa.Column('action_items', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('next_session_focus', postgresql.ARRAY(sa.String()), nullable=True),
        # AI analysis
        sa.Column('ai_insights', sa.JSON(), nullable=True),
        sa.Column('progress_analysis', sa.JSON(), nullable=True),
        sa.Column('suggested_techniques', postgresql.ARRAY(sa.String()), nullable=True),
        # Privacy and sharing
        sa.Column('is_private', sa.Boolean(), server_default='true'),
        sa.Column('share_with_therapist', sa.Boolean(), server_default='false'),
        sa.Column('therapist_can_comment', sa.Boolean(), server_default='false'),
        # Metadata
        sa.Column('entry_duration_seconds', sa.Integer(), nullable=True),
        sa.Column('structured_format', sa.JSON(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'])
    )
    
    op.create_index('ix_therapy_notes_user_date', 'therapy_notes', ['user_id', 'note_date'])
    op.create_index('ix_therapy_notes_shareable', 'therapy_notes', ['share_with_therapist', 'note_date'])
    
    # Share keys table
    op.create_table('share_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('share_key', sa.String(255), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('therapist_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('therapist_email', sa.String(255), nullable=False),
        # Permissions
        sa.Column('permission_level', sa.String(20), server_default='read_only', nullable=False),
        sa.Column('include_mood_entries', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('include_dream_entries', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('include_therapy_notes', sa.Boolean(), server_default='true', nullable=False),
        # Time and session limits
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('max_sessions', sa.Integer(), nullable=True),
        # Status tracking
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_accepted', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        # Access tracking
        sa.Column('access_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_accessed', sa.DateTime(), nullable=True),
        # Revocation
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('revocation_reason', sa.String(100), nullable=True),
        # Notes
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('therapist_message', sa.Text(), nullable=True),
        # Advanced options
        sa.Column('date_range_start', sa.DateTime(), nullable=True),
        sa.Column('date_range_end', sa.DateTime(), nullable=True),
        sa.Column('exclude_tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('emergency_contact', sa.Boolean(), server_default='false'),
        sa.Column('crisis_access', sa.Boolean(), server_default='false'),
        # Metadata
        sa.Column('ip_address_created', sa.String(45), nullable=True),
        sa.Column('user_agent_created', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['patient_id'], ['users.id']),
        sa.ForeignKeyConstraint(['therapist_id'], ['users.id']),
        sa.UniqueConstraint('share_key')
    )
    
    op.create_index('ix_share_keys_patient_active', 'share_keys', ['patient_id', 'is_active'])
    op.create_index('ix_share_keys_therapist_active', 'share_keys', ['therapist_id', 'is_active'])
    op.create_index('ix_share_keys_email_active', 'share_keys', ['therapist_email', 'is_active'])
    
    # Share key access logs table
    op.create_table('share_key_access_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('share_key_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('accessed_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('accessed_resource', sa.String(100), nullable=False),
        sa.Column('resource_count', sa.Integer(), server_default='1', nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('session_id', sa.String(255), nullable=True),
        sa.Column('data_filters', sa.JSON(), nullable=True),
        sa.Column('data_range', sa.JSON(), nullable=True),
        sa.Column('action_type', sa.String(50), server_default='view', nullable=False),
        sa.Column('action_details', sa.JSON(), nullable=True),
        sa.Column('session_duration_seconds', sa.Integer(), nullable=True),
        sa.Column('items_viewed', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['share_key_id'], ['share_keys.id'])
    )
    
    op.create_index('ix_access_logs_share_key_time', 'share_key_access_logs', ['share_key_id', 'accessed_at'])

def downgrade() -> None:
    """Drop all tables"""
    
    op.drop_table('share_key_access_logs')
    op.drop_table('share_keys')
    op.drop_table('therapy_notes')
    op.drop_table('dream_entries')
    op.drop_table('mood_entries')
    op.drop_table('user_sessions')
    op.drop_table('login_attempts')
    op.drop_table('users')
