"""
Add Encrypted Models for Zero-Knowledge Architecture

This migration adds encrypted storage tables for user data.
All sensitive user content is encrypted client-side before reaching the server.

The server can NEVER decrypt this data!

Revision ID: 002_add_encrypted_models
Revises: 001_initial_tables
Create Date: 2025-01-15 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import datetime

# revision identifiers
revision = '002_add_encrypted_models'
down_revision = '001_initial_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create encrypted storage tables for Zero-Knowledge Architecture.

    Tables created:
    - encrypted_mood_entries: Encrypted mood tracking data
    - encrypted_dream_entries: Encrypted dream journal entries
    - encrypted_therapy_notes: Encrypted therapy notes and worksheets
    - encrypted_chat_messages: Encrypted AI chat messages
    - user_encryption_keys: Key derivation metadata (NOT actual keys!)
    """

    # ========================================
    # Encrypted Mood Entries
    # ========================================
    op.create_table(
        'encrypted_mood_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Encrypted payload (ciphertext + nonce)
        sa.Column('encrypted_data', sa.LargeBinary(), nullable=False),

        # Metadata for queries (unencrypted)
        sa.Column('entry_type', sa.String(20), nullable=False, server_default='mood'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=datetime.datetime.utcnow),

        # Encryption metadata
        sa.Column('encryption_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('key_id', sa.String(64), nullable=True),

        # Soft delete (GDPR compliance)
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),

        sa.PrimaryKeyConstraint('id')
    )

    # Indexes for encrypted_mood_entries
    op.create_index('ix_encrypted_mood_user_id', 'encrypted_mood_entries', ['user_id'])
    op.create_index('ix_encrypted_mood_created_at', 'encrypted_mood_entries', ['created_at'])
    op.create_index('ix_encrypted_mood_user_time', 'encrypted_mood_entries', ['user_id', 'created_at'])
    op.create_index('ix_encrypted_mood_not_deleted', 'encrypted_mood_entries', ['is_deleted'])


    # ========================================
    # Encrypted Dream Entries
    # ========================================
    op.create_table(
        'encrypted_dream_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Encrypted payload
        sa.Column('encrypted_data', sa.LargeBinary(), nullable=False),

        # Metadata
        sa.Column('entry_type', sa.String(20), nullable=False, server_default='dream'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=datetime.datetime.utcnow),

        # Encryption metadata
        sa.Column('encryption_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('key_id', sa.String(64), nullable=True),

        # Soft delete
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),

        sa.PrimaryKeyConstraint('id')
    )

    # Indexes for encrypted_dream_entries
    op.create_index('ix_encrypted_dream_user_id', 'encrypted_dream_entries', ['user_id'])
    op.create_index('ix_encrypted_dream_created_at', 'encrypted_dream_entries', ['created_at'])
    op.create_index('ix_encrypted_dream_user_time', 'encrypted_dream_entries', ['user_id', 'created_at'])
    op.create_index('ix_encrypted_dream_not_deleted', 'encrypted_dream_entries', ['is_deleted'])


    # ========================================
    # Encrypted Therapy Notes
    # ========================================
    op.create_table(
        'encrypted_therapy_notes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Encrypted payload
        sa.Column('encrypted_data', sa.LargeBinary(), nullable=False),

        # Metadata
        sa.Column('entry_type', sa.String(20), nullable=False, server_default='therapy_note'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=datetime.datetime.utcnow),

        # Encryption metadata
        sa.Column('encryption_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('key_id', sa.String(64), nullable=True),

        # Soft delete
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),

        sa.PrimaryKeyConstraint('id')
    )

    # Indexes for encrypted_therapy_notes
    op.create_index('ix_encrypted_therapy_user_id', 'encrypted_therapy_notes', ['user_id'])
    op.create_index('ix_encrypted_therapy_created_at', 'encrypted_therapy_notes', ['created_at'])
    op.create_index('ix_encrypted_therapy_user_time', 'encrypted_therapy_notes', ['user_id', 'created_at'])
    op.create_index('ix_encrypted_therapy_not_deleted', 'encrypted_therapy_notes', ['is_deleted'])


    # ========================================
    # Encrypted Chat Messages
    # ========================================
    op.create_table(
        'encrypted_chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True),  # For grouping conversations

        # Encrypted payload
        sa.Column('encrypted_data', sa.LargeBinary(), nullable=False),

        # Metadata
        sa.Column('message_type', sa.String(20), nullable=False, server_default='chat'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),

        # Encryption metadata
        sa.Column('encryption_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('key_id', sa.String(64), nullable=True),

        # Soft delete
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),

        sa.PrimaryKeyConstraint('id')
    )

    # Indexes for encrypted_chat_messages
    op.create_index('ix_encrypted_chat_user_id', 'encrypted_chat_messages', ['user_id'])
    op.create_index('ix_encrypted_chat_session_id', 'encrypted_chat_messages', ['session_id'])
    op.create_index('ix_encrypted_chat_created_at', 'encrypted_chat_messages', ['created_at'])
    op.create_index('ix_encrypted_chat_user_time', 'encrypted_chat_messages', ['user_id', 'created_at'])
    op.create_index('ix_encrypted_chat_not_deleted', 'encrypted_chat_messages', ['is_deleted'])


    # ========================================
    # User Encryption Keys (Metadata Only!)
    # ========================================
    op.create_table(
        'user_encryption_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Key derivation parameters (NOT the actual keys!)
        sa.Column('key_salt', sa.LargeBinary(), nullable=False),  # Random salt for PBKDF2
        sa.Column('key_iterations', sa.Integer(), nullable=False, server_default='600000'),  # PBKDF2 iterations
        sa.Column('key_algorithm', sa.String(50), nullable=False, server_default='PBKDF2-SHA256'),

        # Current key version (for rotation)
        sa.Column('current_key_version', sa.Integer(), nullable=False, server_default='1'),

        # Recovery options (optional, user-controlled)
        sa.Column('has_recovery_key', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('recovery_key_encrypted', sa.LargeBinary(), nullable=True),  # Encrypted with secondary password

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=datetime.datetime.utcnow),
        sa.Column('last_key_rotation', sa.DateTime(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )

    # Indexes for user_encryption_keys
    op.create_index('ix_user_encryption_keys_user_id', 'user_encryption_keys', ['user_id'], unique=True)


def downgrade() -> None:
    """
    Remove encrypted storage tables.

    WARNING: This will delete all encrypted user data!
    """

    # Drop tables in reverse order
    op.drop_table('user_encryption_keys')
    op.drop_table('encrypted_chat_messages')
    op.drop_table('encrypted_therapy_notes')
    op.drop_table('encrypted_dream_entries')
    op.drop_table('encrypted_mood_entries')
