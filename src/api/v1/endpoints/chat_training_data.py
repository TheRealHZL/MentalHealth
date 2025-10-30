"""
Chat Training Data Endpoints

API für Chat Training Dataset Management und Data Upload.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Optional
from datetime import datetime
import json
import os
import logging
from uuid import uuid4

from src.core.security import get_current_user_id, get_current_user_role
from src.core.database import get_async_session
from src.schemas.chat import ChatTrainingDataCreate, ChatTrainingDataResponse
from src.schemas.ai import SuccessResponse, PaginatedResponse
from src.models.training import TrainingDataset, TrainingJob
from src.core.config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()

@router.post("/datasets", response_model=ChatTrainingDataResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_training_dataset(
    dataset: ChatTrainingDataCreate,
    current_user_id: str = Depends(get_current_user_id),
    current_user_role: str = Depends(get_current_user_role),
    db = Depends(get_async_session)
):
    """
    Create a chat conversation training dataset
    
    **Admin/Therapist Only**: Only verified users can create chat training datasets
    
    **Chat Training Data Format:**
    ```json
    {
        "dataset_name": "Empathetic Chat Responses v1.0",
        "description": "Training data for therapeutic chat conversations",
        "training_pairs": [
            {
                "user_input": "Ich fühle mich heute sehr niedergeschlagen",
                "ai_response": "Es tut mir leid zu hören, dass du dich so fühlst...",
                "therapeutic_intent": "validation",
                "safety_rating": 5,
                "empathy_rating": 5,
                "therapeutic_quality": 4,
                "context": {
                    "session_type": "depression_support",
                    "user_mood": 3
                }
            }
        ]
    }
    ```
    """
    
    # Check permissions
    if current_user_role not in ["admin", "therapist"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and verified therapists can create chat training datasets"
        )
    
    try:
        # Create chat dataset
        chat_dataset = TrainingDataset(
            id=str(uuid4()),
            name=dataset.dataset_name,
            description=dataset.description,
            dataset_type="chat_conversation",
            data_format="json",
            created_by=current_user_id,
            version="1.0.0",
            is_active=True,
            sample_count=len(dataset.training_pairs),
            metadata={
                "created_via": "chat_api",
                "therapeutic_focus": dataset.therapeutic_focus,
                "language": dataset.language,
                "quality_threshold": dataset.quality_threshold,
                "average_ratings": {
                    "safety": sum(p.safety_rating for p in dataset.training_pairs) / len(dataset.training_pairs),
                    "empathy": sum(p.empathy_rating for p in dataset.training_pairs) / len(dataset.training_pairs),
                    "therapeutic_quality": sum(p.therapeutic_quality for p in dataset.training_pairs) / len(dataset.training_pairs)
                }
            }
        )
        
        db.add(chat_dataset)
        await db.commit()
        await db.refresh(chat_dataset)
        
        # Process chat training pairs in background
        background_tasks = BackgroundTasks()
        background_tasks.add_task(
            process_chat_training_data,
            dataset_id=chat_dataset.id,
            training_pairs=dataset.training_pairs,
            uploaded_by=current_user_id,
            db=db
        )
        
        logger.info(f"Chat training dataset created: {chat_dataset.id}")
        
        # Calculate quality metrics
        high_quality_pairs = sum(
            1 for pair in dataset.training_pairs 
            if (pair.safety_rating + pair.empathy_rating + pair.therapeutic_quality) / 3 >= 4.0
        )
        
        return ChatTrainingDataResponse(
            dataset_id=chat_dataset.id,
            dataset_name=chat_dataset.name,
            description=chat_dataset.description,
            total_pairs=len(dataset.training_pairs),
            high_quality_pairs=high_quality_pairs,
            average_safety_rating=sum(p.safety_rating for p in dataset.training_pairs) / len(dataset.training_pairs),
            average_empathy_rating=sum(p.empathy_rating for p in dataset.training_pairs) / len(dataset.training_pairs),
            average_therapeutic_quality=sum(p.therapeutic_quality for p in dataset.training_pairs) / len(dataset.training_pairs),
            therapeutic_focus=dataset.therapeutic_focus,
            language=dataset.language,
            created_at=chat_dataset.created_at,
            processing_status="processing"
        )
        
    except Exception as e:
        logger.error(f"Failed to create chat training dataset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create chat training dataset"
        )

@router.get("/datasets", response_model=PaginatedResponse)
async def list_chat_training_datasets(
    page: int = 1,
    page_size: int = 20,
    language: Optional[str] = None,
    current_user_id: str = Depends(get_current_user_id),
    current_user_role: str = Depends(get_current_user_role),
    db = Depends(get_async_session)
):
    """List chat training datasets"""
    
    if current_user_role not in ["admin", "therapist"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and therapists can view chat training datasets"
        )
    
    try:
        # Build query for chat datasets
        query = db.query(TrainingDataset).filter(TrainingDataset.dataset_type == "chat_conversation")
        
        # Filter by language if specified
        if language:
            query = query.filter(TrainingDataset.metadata["language"].astext == language)
        
        # Filter by user if not admin
        if current_user_role != "admin":
            query = query.filter(TrainingDataset.created_by == current_user_id)
        
        # Get total count
        total = await query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        datasets = await query.offset(offset).limit(page_size).all()
        
        # Convert to response format
        items = []
        for dataset in datasets:
            avg_ratings = dataset.metadata.get("average_ratings", {})
            items.append(ChatTrainingDataResponse(
                dataset_id=dataset.id,
                dataset_name=dataset.name,
                description=dataset.description,
                total_pairs=dataset.sample_count or 0,
                high_quality_pairs=int((dataset.sample_count or 0) * 0.8),  # Estimate
                average_safety_rating=avg_ratings.get("safety", 0.0),
                average_empathy_rating=avg_ratings.get("empathy", 0.0),
                average_therapeutic_quality=avg_ratings.get("therapeutic_quality", 0.0),
                therapeutic_focus=dataset.metadata.get("therapeutic_focus"),
                language=dataset.metadata.get("language", "de"),
                created_at=dataset.created_at,
                processing_status="completed"
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
        logger.error(f"Failed to list chat datasets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat training datasets"
        )

@router.delete("/datasets/{dataset_id}", response_model=SuccessResponse)
async def delete_chat_training_dataset(
    dataset_id: str,
    current_user_id: str = Depends(get_current_user_id),
    current_user_role: str = Depends(get_current_user_role),
    db = Depends(get_async_session)
):
    """Delete a chat training dataset"""
    
    if current_user_role not in ["admin", "therapist"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and therapists can delete chat training datasets"
        )
    
    try:
        # Get dataset
        dataset = await db.get(TrainingDataset, dataset_id)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat training dataset not found"
            )
        
        # Check ownership or admin
        if dataset.created_by != current_user_id and current_user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own datasets"
            )
        
        # Check if dataset is being used in active training
        active_jobs = await db.query(TrainingJob).filter(
            TrainingJob.dataset_ids.contains([dataset_id]),
            TrainingJob.status.in_(["queued", "running"])
        ).count()
        
        if active_jobs > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete dataset while it's being used in active training jobs"
            )
        
        # Mark as inactive instead of actual deletion
        dataset.is_active = False
        dataset.updated_at = datetime.utcnow()
        await db.commit()
        
        logger.info(f"Chat training dataset deactivated: {dataset_id}")
        
        return SuccessResponse(
            message="Chat training dataset successfully deleted",
            data={"dataset_id": dataset_id, "deleted_at": datetime.utcnow().isoformat()}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete chat training dataset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete chat training dataset"
        )

# =============================================================================
# Background Tasks
# =============================================================================

async def process_chat_training_data(
    dataset_id: str,
    training_pairs: List,
    uploaded_by: str,
    db
):
    """Process chat training pairs and store them"""
    
    try:
        # Convert training pairs to standardized format
        processed_pairs = []
        for pair in training_pairs:
            processed_pair = {
                "id": str(uuid4()),
                "user_input": pair.user_input,
                "ai_response": pair.ai_response,
                "context": pair.context or {},
                "therapeutic_intent": pair.therapeutic_intent,
                "emotional_tone": pair.emotional_tone,
                "crisis_level": pair.crisis_level,
                "ratings": {
                    "safety": pair.safety_rating,
                    "empathy": pair.empathy_rating,
                    "therapeutic_quality": pair.therapeutic_quality
                },
                "processed_at": datetime.utcnow().isoformat(),
                "uploaded_by": uploaded_by
            }
            processed_pairs.append(processed_pair)
        
        # Store processed chat training data
        data_file_path = f"data/training/{dataset_id}/chat_pairs_{uuid4()}.json"
        os.makedirs(os.path.dirname(data_file_path), exist_ok=True)
        
        with open(data_file_path, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {
                    "dataset_id": dataset_id,
                    "uploaded_by": uploaded_by,
                    "processed_at": datetime.utcnow().isoformat(),
                    "pair_count": len(processed_pairs),
                    "data_type": "chat_conversation"
                },
                "training_pairs": processed_pairs
            }, f, indent=2, ensure_ascii=False)
        
        # Update dataset statistics
        dataset = await db.get(TrainingDataset, dataset_id)
        if dataset:
            dataset.updated_at = datetime.utcnow()
            await db.commit()
        
        logger.info(f"Chat training data processed successfully for dataset {dataset_id}")
        
    except Exception as e:
        logger.error(f"Failed to process chat training data: {e}")
