"""
Audit Log Models

Models for security audit logging and monitoring.
"""

import uuid
from datetime import datetime, timedelta

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, INET, JSONB, UUID
from sqlalchemy.sql import func

from src.core.database import Base


class AuditLog(Base):
    """
    Audit Log Entry

    Tracks all database operations for security monitoring.
    """

    __tablename__ = "audit_logs"

    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Operation details
    table_name = Column(String(100), nullable=False, index=True)
    operation = Column(
        String(20), nullable=False, index=True
    )  # SELECT, INSERT, UPDATE, DELETE
    record_id = Column(UUID(as_uuid=True), nullable=True)

    # Data changes
    old_data = Column(JSONB, nullable=True)  # Old values (UPDATE/DELETE)
    new_data = Column(JSONB, nullable=True)  # New values (INSERT/UPDATE)

    # Query information
    query = Column(Text, nullable=True)

    # Request context
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(100), nullable=True)

    # Timing
    timestamp = Column(DateTime, nullable=False, default=func.now(), index=True)
    duration_ms = Column(Integer, nullable=True)

    # Security flags
    suspicious = Column(Boolean, default=False, nullable=False, index=True)
    suspicious_reasons = Column(ARRAY(String), nullable=True)

    # Additional context
    metadata = Column(JSONB, nullable=True)

    def __repr__(self):
        return f"<AuditLog(id={self.id}, user={self.user_id}, table={self.table_name}, op={self.operation})>"

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id) if self.user_id else None,
            "table_name": self.table_name,
            "operation": self.operation,
            "record_id": str(self.record_id) if self.record_id else None,
            "old_data": self.old_data,
            "new_data": self.new_data,
            "ip_address": str(self.ip_address) if self.ip_address else None,
            "user_agent": self.user_agent,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "duration_ms": self.duration_ms,
            "suspicious": self.suspicious,
            "suspicious_reasons": self.suspicious_reasons,
            "metadata": self.metadata,
        }

    @property
    def is_suspicious(self) -> bool:
        """Check if this audit log entry is suspicious"""
        return self.suspicious

    @property
    def is_recent(self) -> bool:
        """Check if this audit log entry is recent (within last hour)"""
        if not self.timestamp:
            return False
        return self.timestamp > datetime.utcnow() - timedelta(hours=1)

    def get_data_diff(self) -> dict:
        """
        Get the difference between old and new data (for UPDATE operations)

        Returns:
            dict: {field: {old: value, new: value}}
        """
        if self.operation != "UPDATE" or not self.old_data or not self.new_data:
            return {}

        diff = {}
        all_keys = set(self.old_data.keys()) | set(self.new_data.keys())

        for key in all_keys:
            old_val = self.old_data.get(key)
            new_val = self.new_data.get(key)

            if old_val != new_val:
                diff[key] = {"old": old_val, "new": new_val}

        return diff

    def get_suspicious_summary(self) -> str:
        """Get human-readable summary of suspicious reasons"""
        if not self.suspicious or not self.suspicious_reasons:
            return "Not suspicious"

        return ", ".join(self.suspicious_reasons)


# Indexes are created in the migration (004_add_audit_logging.py)
