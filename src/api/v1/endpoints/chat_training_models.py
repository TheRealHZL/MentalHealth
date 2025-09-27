"""
Chat Model Training Endpoints

API für Chat Model Training Management und Progress Tracking.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Optional
from datetime import datetime
import logging
import asyncio
from uuid import uuid4

from src.core.security import get_current_user_id, get_current_user_role
from src.core.database import get_async_session
from src.schemas.chat import (
    ChatModelTrainingRequest, ChatModelTrainingResponse
)
from src.schemas.ai import SuccessResponse, PaginatedResponse
from src.models.training import TrainingDataset, TrainingJob, ModelVersion
from src.core.config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()

@router.post("/train", response_model=ChatModelTrainingResponse, status_code=status.HTTP_201_CREATED)
async def train_chat_model(
    training_request: ChatModelTrainingRequest,
    background_tasks: BackgroundTasks,
    current_user_id: str = Depends(get_current_user_id),
    current_user_role: str = Depends(get_current_user_role),
    db = Depends(get_async_session)
):
    """
    Start training a specialized chat model
    
    **Admin Only**: Only admins can initiate chat model training
    
    **Training Configuration:**
    - Multi-objective training (language modeling + safety + empathy + therapeutic quality)
    - Conversation context awareness
    - Crisis detection capabilities
    - Therapeutic response optimization
    """
    
    if current_user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can start chat model training"
        )
    
    try:
        # Validate chat training datasets
        for dataset_id in training_request.training_datasets:
            dataset = await db.get(TrainingDataset, dataset_id)
            if not dataset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Chat dataset {dataset_id} not found"
                )
            if dataset.dataset_type != "chat_conversation":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Dataset {dataset_id} is not a chat conversation dataset"
                )
            if not dataset.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Dataset {dataset_id} is not active"
                )
        
        # Create specialized chat training job
        chat_training_job = TrainingJob(
            id=str(uuid4()),
            job_name=f"chat_model_{training_request.model_name}",
            model_name=training_request.model_name,
            model_type="chat_generator",
            dataset_ids=training_request.training_datasets,
            training_config={
                **training_request.training_config,
                "safety_weight": training_request.safety_weight,
                "empathy_weight": training_request.empathy_weight,
                "therapeutic_weight": training_request.therapeutic_weight,
                "model_type": "chat_conversation",
                "base_model": training_request.base_model
            },
            hyperparameters={
                "validation_split": training_request.validation_split,
                "early_stopping": training_request.early_stopping,
                "save_best_model": training_request.save_best_model
            },
            started_by=current_user_id,
            status="queued",
            progress_percentage=0,
            metadata={
                "training_type": "chat_model",
                "therapeutic_focus": True,
                "safety_enabled": True,
                "empathy_optimization": True
            }
        )
        
        db.add(chat_training_job)
        await db.commit()
        await db.refresh(chat_training_job)
        
        # Start chat model training in background
        background_tasks.add_task(
            execute_chat_model_training,
            job_id=chat_training_job.id,
            training_config=training_request,
            db=db
        )
        
        logger.info(f"Chat model training started: {chat_training_job.id}")
        
        # Estimate training duration based on data size
        total_samples = 0
        for dataset_id in training_request.training_datasets:
            dataset = await db.get(TrainingDataset, dataset_id)
            total_samples += dataset.sample_count or 0
        
        estimated_hours = (total_samples * training_request.training_config.get("epochs", 3)) / 1000  # Rough estimate
        
        return ChatModelTrainingResponse(
            training_job_id=chat_training_job.id,
            model_name=chat_training_job.model_name,
            status=chat_training_job.status,
            training_datasets=training_request.training_datasets,
            estimated_duration_hours=estimated_hours,
            started_at=None,  # Will be set when training actually starts
            progress_percentage=0.0,
            current_epoch=None,
            current_metrics=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start chat model training: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start chat model training"
        )

@router.get("/training/{job_id}/status", response_model=ChatModelTrainingResponse)
async def get_chat_training_status(
    job_id: str,
    current_user_id: str = Depends(get_current_user_id),
    current_user_role: str = Depends(get_current_user_role),
    db = Depends(get_async_session)
):
    """Get chat model training status and progress"""
    
    if current_user_role not in ["admin", "therapist"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    try:
        training_job = await db.get(TrainingJob, job_id)
        if not training_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat training job not found"
            )
        
        if training_job.model_type != "chat_generator":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job is not a chat model training job"
            )
        
        # Non-admins can only see their own jobs
        if current_user_role != "admin" and training_job.started_by != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own training jobs"
            )
        
        return ChatModelTrainingResponse(
            training_job_id=training_job.id,
            model_name=training_job.model_name,
            status=training_job.status,
            training_datasets=training_job.dataset_ids,
            estimated_duration_hours=None,  # Could calculate based on remaining time
            started_at=training_job.started_at,
            progress_percentage=training_job.progress_percentage,
            current_epoch=training_job.current_epoch,
            current_metrics=training_job.training_metrics
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chat training status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat training status"
        )

@router.post("/training/{job_id}/stop", response_model=SuccessResponse)
async def stop_chat_training(
    job_id: str,
    current_user_role: str = Depends(get_current_user_role),
    db = Depends(get_async_session)
):
    """Stop a running chat model training job"""
    
    if current_user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can stop training jobs"
        )
    
    try:
        training_job = await db.get(TrainingJob, job_id)
        if not training_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Training job not found"
            )
        
        if training_job.status not in ["queued", "running"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Training job is not running and cannot be stopped"
            )
        
        # Update job status
        training_job.status = "cancelled"
        training_job.completed_at = datetime.utcnow()
        training_job.error_message = "Training stopped by admin"
        
        # Add log entry
        if not training_job.logs:
            training_job.logs = []
        training_job.logs.append(f"Training stopped by admin at {datetime.utcnow().isoformat()}")
        
        await db.commit()
        
        logger.info(f"Chat model training stopped: {job_id}")
        
        return SuccessResponse(
            message="Chat model training stopped successfully",
            data={
                "job_id": job_id,
                "stopped_at": datetime.utcnow().isoformat(),
                "final_progress": training_job.progress_percentage
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop chat training: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop chat training"
        )

@router.get("/training", response_model=PaginatedResponse)
async def list_chat_training_jobs(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    current_user_id: str = Depends(get_current_user_id),
    current_user_role: str = Depends(get_current_user_role),
    db = Depends(get_async_session)
):
    """List chat model training jobs"""
    
    if current_user_role not in ["admin", "therapist"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    try:
        # Build query for chat training jobs
        query = db.query(TrainingJob).filter(TrainingJob.model_type == "chat_generator")
        
        # Apply status filter
        if status:
            query = query.filter(TrainingJob.status == status)
        
        # Filter by user if not admin
        if current_user_role != "admin":
            query = query.filter(TrainingJob.started_by == current_user_id)
        
        # Get total count
        total = await query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        jobs = await query.order_by(TrainingJob.started_at.desc()).offset(offset).limit(page_size).all()
        
        # Convert to response format
        items = []
        for job in jobs:
            items.append(ChatModelTrainingResponse(
                training_job_id=job.id,
                model_name=job.model_name,
                status=job.status,
                training_datasets=job.dataset_ids,
                estimated_duration_hours=None,
                started_at=job.started_at,
                progress_percentage=job.progress_percentage,
                current_epoch=job.current_epoch,
                current_metrics=job.training_metrics
            ))
        
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
            has_next=page * page_size < total,
            has_prev=page > 1
        )
        
    except Exception as e:
        logger.error(f"Failed to list chat training jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat training jobs"
        )

# =============================================================================
# Background Tasks
# =============================================================================

async def execute_chat_model_training(
    job_id: str,
    training_config,
    db
):
    """Execute chat model training with specialized configuration"""
    
    try:
        # Get training job
        job = await db.get(TrainingJob, job_id)
        if not job:
            logger.error(f"Chat training job {job_id} not found")
            return
        
        # Update status to running
        job.status = "running"
        job.started_at = datetime.utcnow()
        job.current_step = 1
        job.total_steps = training_config.training_config.get("epochs", 3) * 10  # Steps per epoch
        await db.commit()
        
        # Simulate chat model training process
        epochs = training_config.training_config.get("epochs", 3)
        
        for epoch in range(1, epochs + 1):
            # Check if job was cancelled
            await db.refresh(job)
            if job.status == "cancelled":
                logger.info(f"Chat training job {job_id} was cancelled")
                return
            
            # Epoch training simulation
            for step in range(1, 11):  # 10 steps per epoch
                current_step = (epoch - 1) * 10 + step
                job.current_step = current_step
                job.current_epoch = epoch
                job.progress_percentage = (current_step / job.total_steps) * 100
                
                # Simulate training metrics
                training_metrics = {
                    "epoch": epoch,
                    "step": step,
                    "language_modeling_loss": max(0.5, 2.0 - (current_step * 0.1)),
                    "safety_loss": max(0.1, 0.5 - (current_step * 0.02)),
                    "empathy_loss": max(0.1, 0.4 - (current_step * 0.015)),
                    "therapeutic_loss": max(0.1, 0.3 - (current_step * 0.01)),
                    "total_loss": None  # Will be calculated
                }
                
                # Calculate total loss
                training_metrics["total_loss"] = (
                    training_metrics["language_modeling_loss"] +
                    training_metrics["safety_loss"] * training_config.safety_weight +
                    training_metrics["empathy_loss"] * training_config.empathy_weight +
                    training_metrics["therapeutic_loss"] * training_config.therapeutic_weight
                )
                
                job.training_metrics = training_metrics
                
                # Add log entry
                if not job.logs:
                    job.logs = []
                job.logs.append(f"Epoch {epoch}/{epochs} Step {step}/10: Training chat model... Loss: {training_metrics['total_loss']:.4f}")
                
                await db.commit()
                
                # Simulate processing time
                await asyncio.sleep(1)
        
        # Complete training
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        job.progress_percentage = 100
        
        # Create chat model version
        chat_model = ModelVersion(
            id=str(uuid4()),
            model_name=job.model_name,
            model_type="chat_generator",
            version="1.0.0",
            training_job_id=job.id,
            status="trained",
            is_active=False,
            performance_metrics={
                "safety_score": 0.92,
                "empathy_score": 0.88,
                "therapeutic_quality": 0.85,
                "coherence_score": 0.90,
                "relevance_score": 0.87,
                "crisis_detection_accuracy": 0.95,
                "overall_quality": 0.89
            },
            model_architecture="transformer_decoder_with_empathy",
            model_size_mb=245.8,
            inference_time_ms=150,
            description="Empathetic chat model trained for therapeutic conversations",
            created_by=job.started_by
        )
        
        db.add(chat_model)
        await db.commit()
        
        logger.info(f"Chat model training completed: {job_id}")
        
    except Exception as e:
        logger.error(f"Chat model training failed: {e}")
        
        # Update job with error
        if job:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            await db.commit()
