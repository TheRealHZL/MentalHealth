"""
Audit Service

Service for querying and analyzing security audit logs.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text, desc
from sqlalchemy.dialects.postgresql import INET

from src.models.audit import AuditLog
import logging

logger = logging.getLogger(__name__)


class AuditService:
    """Service for audit log operations"""

    @staticmethod
    async def log_manual_entry(
        session: AsyncSession,
        user_id: Optional[UUID],
        table_name: str,
        operation: str,
        record_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> AuditLog:
        """
        Manually create an audit log entry

        Usage:
            await AuditService.log_manual_entry(
                session,
                user_id=user.id,
                table_name="users",
                operation="LOGIN",
                ip_address="192.168.1.1"
            )
        """
        audit = AuditLog(
            user_id=user_id,
            table_name=table_name,
            operation=operation,
            record_id=record_id,
            ip_address=ip_address,
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )

        session.add(audit)
        await session.commit()

        logger.info(f"✅ Audit log created: {operation} on {table_name} by user {user_id}")

        return audit

    @staticmethod
    async def get_user_activity(
        session: AsyncSession,
        user_id: UUID,
        hours: int = 24,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get recent activity for a specific user

        Usage:
            logs = await AuditService.get_user_activity(session, user.id, hours=24)
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        result = await session.execute(
            select(AuditLog)
            .where(
                and_(
                    AuditLog.user_id == user_id,
                    AuditLog.timestamp >= cutoff
                )
            )
            .order_by(desc(AuditLog.timestamp))
            .limit(limit)
        )

        return result.scalars().all()

    @staticmethod
    async def get_suspicious_activity(
        session: AsyncSession,
        hours: int = 24,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get all suspicious activity in the last N hours

        Usage:
            suspicious = await AuditService.get_suspicious_activity(session, hours=24)
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        result = await session.execute(
            select(AuditLog)
            .where(
                and_(
                    AuditLog.suspicious == True,
                    AuditLog.timestamp >= cutoff
                )
            )
            .order_by(desc(AuditLog.timestamp))
            .limit(limit)
        )

        return result.scalars().all()

    @staticmethod
    async def get_table_activity(
        session: AsyncSession,
        table_name: str,
        hours: int = 24,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get all activity on a specific table

        Usage:
            logs = await AuditService.get_table_activity(session, "mood_entries")
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        result = await session.execute(
            select(AuditLog)
            .where(
                and_(
                    AuditLog.table_name == table_name,
                    AuditLog.timestamp >= cutoff
                )
            )
            .order_by(desc(AuditLog.timestamp))
            .limit(limit)
        )

        return result.scalars().all()

    @staticmethod
    async def get_activity_summary(
        session: AsyncSession,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get summary statistics for audit activity

        Returns:
            dict: {
                "total_operations": 1234,
                "operations_by_type": {"SELECT": 800, "INSERT": 200, ...},
                "operations_by_table": {"mood_entries": 500, ...},
                "suspicious_count": 5,
                "unique_users": 42
            }
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        # Total operations
        total = await session.execute(
            select(func.count(AuditLog.id))
            .where(AuditLog.timestamp >= cutoff)
        )
        total_ops = total.scalar()

        # Operations by type
        by_type_result = await session.execute(
            select(
                AuditLog.operation,
                func.count(AuditLog.id)
            )
            .where(AuditLog.timestamp >= cutoff)
            .group_by(AuditLog.operation)
        )
        by_type = {row[0]: row[1] for row in by_type_result.fetchall()}

        # Operations by table
        by_table_result = await session.execute(
            select(
                AuditLog.table_name,
                func.count(AuditLog.id)
            )
            .where(AuditLog.timestamp >= cutoff)
            .group_by(AuditLog.table_name)
        )
        by_table = {row[0]: row[1] for row in by_table_result.fetchall()}

        # Suspicious count
        suspicious = await session.execute(
            select(func.count(AuditLog.id))
            .where(
                and_(
                    AuditLog.suspicious == True,
                    AuditLog.timestamp >= cutoff
                )
            )
        )
        suspicious_count = suspicious.scalar()

        # Unique users
        unique = await session.execute(
            select(func.count(func.distinct(AuditLog.user_id)))
            .where(AuditLog.timestamp >= cutoff)
        )
        unique_users = unique.scalar()

        return {
            "total_operations": total_ops,
            "operations_by_type": by_type,
            "operations_by_table": by_table,
            "suspicious_count": suspicious_count,
            "unique_users": unique_users,
            "time_range_hours": hours
        }

    @staticmethod
    async def detect_suspicious_activity(session: AsyncSession):
        """
        Run suspicious activity detection

        This calls the PostgreSQL function to detect and mark suspicious activity.

        Usage:
            await AuditService.detect_suspicious_activity(session)
        """
        try:
            await session.execute(text("SELECT detect_suspicious_activity()"))
            await session.commit()
            logger.info("✅ Suspicious activity detection completed")
        except Exception as e:
            logger.error(f"❌ Failed to detect suspicious activity: {e}")
            raise

    @staticmethod
    async def cleanup_old_logs(session: AsyncSession) -> int:
        """
        Clean up audit logs older than 90 days (GDPR compliance)

        Returns:
            int: Number of logs deleted

        Usage:
            deleted = await AuditService.cleanup_old_logs(session)
        """
        try:
            result = await session.execute(text("SELECT cleanup_old_audit_logs()"))
            deleted_count = result.scalar()
            await session.commit()

            logger.info(f"✅ Cleaned up {deleted_count} old audit logs")
            return deleted_count

        except Exception as e:
            logger.error(f"❌ Failed to cleanup audit logs: {e}")
            raise

    @staticmethod
    async def get_user_access_pattern(
        session: AsyncSession,
        user_id: UUID,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Analyze user's access patterns for anomaly detection

        Returns:
            dict: {
                "total_operations": 1000,
                "average_per_day": 142.8,
                "most_active_hour": 14,
                "most_accessed_table": "mood_entries",
                "unusual_activity": False
            }
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        # Total operations
        total = await session.execute(
            select(func.count(AuditLog.id))
            .where(
                and_(
                    AuditLog.user_id == user_id,
                    AuditLog.timestamp >= cutoff
                )
            )
        )
        total_ops = total.scalar()

        # Average per day
        avg_per_day = total_ops / days if days > 0 else 0

        # Most active hour
        hour_result = await session.execute(
            select(
                func.extract('hour', AuditLog.timestamp).label('hour'),
                func.count(AuditLog.id).label('count')
            )
            .where(
                and_(
                    AuditLog.user_id == user_id,
                    AuditLog.timestamp >= cutoff
                )
            )
            .group_by('hour')
            .order_by(desc('count'))
            .limit(1)
        )
        hour_row = hour_result.fetchone()
        most_active_hour = int(hour_row[0]) if hour_row else None

        # Most accessed table
        table_result = await session.execute(
            select(
                AuditLog.table_name,
                func.count(AuditLog.id).label('count')
            )
            .where(
                and_(
                    AuditLog.user_id == user_id,
                    AuditLog.timestamp >= cutoff
                )
            )
            .group_by(AuditLog.table_name)
            .order_by(desc('count'))
            .limit(1)
        )
        table_row = table_result.fetchone()
        most_accessed_table = table_row[0] if table_row else None

        # Check for unusual activity (simple heuristic)
        unusual = avg_per_day > 1000  # More than 1000 operations per day is unusual

        return {
            "user_id": str(user_id),
            "total_operations": total_ops,
            "average_per_day": round(avg_per_day, 2),
            "most_active_hour": most_active_hour,
            "most_accessed_table": most_accessed_table,
            "unusual_activity": unusual,
            "days_analyzed": days
        }

    @staticmethod
    async def search_logs(
        session: AsyncSession,
        user_id: Optional[UUID] = None,
        table_name: Optional[str] = None,
        operation: Optional[str] = None,
        suspicious_only: bool = False,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Search audit logs with multiple filters

        Usage:
            logs = await AuditService.search_logs(
                session,
                user_id=user.id,
                table_name="mood_entries",
                operation="SELECT",
                suspicious_only=True
            )
        """
        query = select(AuditLog)

        conditions = []

        if user_id:
            conditions.append(AuditLog.user_id == user_id)

        if table_name:
            conditions.append(AuditLog.table_name == table_name)

        if operation:
            conditions.append(AuditLog.operation == operation)

        if suspicious_only:
            conditions.append(AuditLog.suspicious == True)

        if start_date:
            conditions.append(AuditLog.timestamp >= start_date)

        if end_date:
            conditions.append(AuditLog.timestamp <= end_date)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(desc(AuditLog.timestamp)).limit(limit)

        result = await session.execute(query)
        return result.scalars().all()


# Convenience functions
async def log_login(session: AsyncSession, user_id: UUID, ip_address: str):
    """Log user login"""
    return await AuditService.log_manual_entry(
        session,
        user_id=user_id,
        table_name="users",
        operation="LOGIN",
        ip_address=ip_address,
        metadata={"event": "user_login"}
    )


async def log_logout(session: AsyncSession, user_id: UUID):
    """Log user logout"""
    return await AuditService.log_manual_entry(
        session,
        user_id=user_id,
        table_name="users",
        operation="LOGOUT",
        metadata={"event": "user_logout"}
    )


async def log_failed_login(session: AsyncSession, email: str, ip_address: str):
    """Log failed login attempt"""
    return await AuditService.log_manual_entry(
        session,
        user_id=None,  # No user ID for failed login
        table_name="users",
        operation="FAILED_LOGIN",
        ip_address=ip_address,
        metadata={"event": "failed_login", "email": email}
    )


__all__ = [
    'AuditService',
    'log_login',
    'log_logout',
    'log_failed_login'
]
