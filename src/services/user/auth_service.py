"""
User Authentication Service

Zuständig für Login, Authentication und User-Retrieval.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime
import uuid
import logging

from src.models import User, LoginAttempt

logger = logging.getLogger(__name__)

class AuthService:
    """Authentication Service"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        
        result = await self.db.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        
        result = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()
    
    async def update_last_login(self, user_id: str) -> None:
        """Update user's last login timestamp"""
        
        result = await self.db.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        user = result.scalar_one_or_none()
        
        if user:
            user.last_login = datetime.utcnow()
            await self.db.commit()
            logger.info(f"Last login updated: {user.email}")
    
    async def log_failed_login(self, user_id: uuid.UUID, email: str) -> None:
        """Log failed login attempt"""
        
        login_attempt = LoginAttempt(
            user_id=user_id,
            email=email,
            successful=False,
            attempted_at=datetime.utcnow()
        )
        
        self.db.add(login_attempt)
        await self.db.commit()
        
        logger.warning(f"Failed login attempt logged: {email}")
    
    async def log_successful_login(self, user_id: str, email: str) -> None:
        """Log successful login attempt"""
        
        login_attempt = LoginAttempt(
            user_id=uuid.UUID(user_id),
            email=email,
            successful=True,
            attempted_at=datetime.utcnow()
        )
        
        self.db.add(login_attempt)
        await self.db.commit()
        
        logger.info(f"Successful login logged: {email}")
    
    async def is_account_locked(self, email: str) -> bool:
        """Check if account is locked due to too many failed attempts"""
        
        # Check last 5 failed attempts in last hour
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        result = await self.db.execute(
            select(func.count(LoginAttempt.id)).where(
                and_(
                    LoginAttempt.email == email.lower(),
                    LoginAttempt.successful == False,
                    LoginAttempt.attempted_at >= one_hour_ago
                )
            )
        )
        
        failed_attempts = result.scalar()
        return failed_attempts >= 5  # Lock after 5 failed attempts
    
    async def get_recent_login_attempts(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent login attempts for user"""
        
        result = await self.db.execute(
            select(LoginAttempt).where(
                LoginAttempt.user_id == uuid.UUID(user_id)
            ).order_by(desc(LoginAttempt.attempted_at)).limit(limit)
        )
        
        attempts = list(result.scalars().all())
        
        return [{
            "attempted_at": attempt.attempted_at,
            "successful": attempt.successful,
            "ip_address": attempt.ip_address,
            "user_agent": attempt.user_agent[:100] if attempt.user_agent else None
        } for attempt in attempts]
