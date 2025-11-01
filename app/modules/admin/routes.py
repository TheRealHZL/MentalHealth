"""
Admin API Endpoints

Spezielle Admin-Endpunkte für System-Management und Monitoring.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.security import get_current_user_id, require_admin
from app.models.chat import ChatMessage, ChatSession
from app.models.training import ModelVersion, TrainingDataset, TrainingJob
from app.models.user_models import User, UserRole
from app.schemas.user import UserResponse

router = APIRouter()

# =============================================================================
# Response Models
# =============================================================================


class AdminStats(BaseModel):
    totalUsers: int
    activeTrainingJobs: int
    totalModels: int
    totalDatasets: int
    systemHealth: str
    totalSessions: int
    totalMessages: int


class ActivityItem(BaseModel):
    id: str
    type: str
    message: str
    timestamp: datetime
    user_id: Optional[str] = None


class ActivityResponse(BaseModel):
    items: List[ActivityItem]
    total: int


# =============================================================================
# Admin Dashboard Stats
# =============================================================================


@router.get("/stats", response_model=AdminStats)
async def get_admin_stats(
    current_user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get admin dashboard statistics

    **Admin Only**
    """
    try:
        # Count total users
        total_users = await db.scalar(select(func.count(User.id)))

        # Count active training jobs
        active_training_jobs = await db.scalar(
            select(func.count(TrainingJob.id)).where(
                TrainingJob.status.in_(["pending", "running"])
            )
        )

        # Count total models
        total_models = await db.scalar(select(func.count(ModelVersion.id)))

        # Count total datasets
        total_datasets = await db.scalar(select(func.count(TrainingDataset.id)))

        # Count total sessions
        total_sessions = await db.scalar(select(func.count(ChatSession.id)))

        # Count total messages
        total_messages = await db.scalar(select(func.count(ChatMessage.id)))

        # Check system health (simple check)
        system_health = "healthy"  # Can be extended with actual health checks

        return AdminStats(
            totalUsers=total_users or 0,
            activeTrainingJobs=active_training_jobs or 0,
            totalModels=total_models or 0,
            totalDatasets=total_datasets or 0,
            systemHealth=system_health,
            totalSessions=total_sessions or 0,
            totalMessages=total_messages or 0,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch stats: {str(e)}",
        )


# =============================================================================
# Recent Activity
# =============================================================================


@router.get("/activity", response_model=ActivityResponse)
async def get_recent_activity(
    limit: int = Query(10, ge=1, le=100),
    current_user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get recent system activity

    **Admin Only**
    """
    try:
        activities = []

        # Get recent training jobs
        recent_training = await db.scalars(
            select(TrainingJob)
            .order_by(TrainingJob.queued_at.desc())  # TrainingJob uses queued_at, not created_at
            .limit(limit // 2)
        )

        for job in recent_training:
            activities.append(
                ActivityItem(
                    id=str(job.id),
                    type="training",
                    message=f"Training job for {job.model_type} {job.status}",
                    timestamp=job.queued_at,  # TrainingJob uses queued_at, not created_at
                    user_id=str(job.started_by) if job.started_by else None,  # TrainingJob uses started_by, not created_by
                )
            )

        # Get recent model versions
        recent_models = await db.scalars(
            select(ModelVersion)
            .order_by(ModelVersion.created_at.desc())
            .limit(limit // 2)
        )

        for model in recent_models:
            activities.append(
                ActivityItem(
                    id=str(model.id),
                    type="model",
                    message=f"New model version {model.version} for {model.model_type} created",
                    timestamp=model.created_at,
                    user_id=str(model.created_by) if model.created_by else None,
                )
            )

        # Sort by timestamp
        activities.sort(key=lambda x: x.timestamp, reverse=True)
        activities = activities[:limit]

        return ActivityResponse(items=activities, total=len(activities))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch activity: {str(e)}",
        )


# =============================================================================
# User Management
# =============================================================================


@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    role: Optional[str] = None,
    search: Optional[str] = None,
    current_user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get all users (paginated)

    **Admin Only**
    """
    try:
        query = select(User)

        # Filter by role if specified
        if role:
            query = query.where(User.role == role)

        # Search by email or name
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    User.email.ilike(search_pattern),
                    User.first_name.ilike(search_pattern),
                    User.last_name.ilike(search_pattern),
                )
            )

        # Pagination
        query = query.offset(skip).limit(limit)

        users = await db.scalars(query)
        user_list = users.all()

        # Convert to response models
        result = []
        for user in user_list:
            result.append(UserResponse(
                id=str(user.id),
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                role=user.role,
                is_verified=user.is_verified,
                timezone=user.timezone,
                created_at=user.created_at,
                last_login=user.last_login,
                license_number=user.license_number if user.role == "therapist" else None,
                specializations=user.specializations if user.role == "therapist" else None,
                practice_address=user.practice_address if user.role == "therapist" else None,
                phone_number=user.phone_number if user.role == "therapist" else None,
                bio=user.bio if user.role == "therapist" else None,
            ))

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch users: {str(e)}",
        )


@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    new_role: str,
    current_user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Update user role

    **Admin Only**
    """
    # Validate role
    valid_roles = ["patient", "therapist", "admin"]
    if new_role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {valid_roles}",
        )

    try:
        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Update role
        user.role = new_role
        await db.commit()

        return {"message": f"User role updated to {new_role}", "user_id": user_id}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user role: {str(e)}",
        )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Delete user account

    **Admin Only** - Use with caution!
    """
    # Prevent self-deletion
    if user_id == current_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    try:
        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Delete user (cascade will delete related data)
        await db.delete(user)
        await db.commit()

        return {"message": "User deleted successfully", "user_id": user_id}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}",
        )


# =============================================================================
# System Health
# =============================================================================


@router.get("/health")
async def check_system_health(
    current_user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Detailed system health check

    **Admin Only**
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {},
    }

    try:
        # Check database
        await db.execute(select(1))
        health_status["components"]["database"] = "healthy"
    except:
        health_status["components"]["database"] = "unhealthy"
        health_status["status"] = "degraded"

    # Check AI engine (can be extended)
    health_status["components"]["ai_engine"] = "healthy"

    # Check storage (can be extended)
    health_status["components"]["storage"] = "healthy"

    return health_status
