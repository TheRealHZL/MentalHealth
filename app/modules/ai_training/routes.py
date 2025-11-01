"""
AI Training Endpoints

API für AI-Model Training, Trainingsdaten-Upload und Model Management.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from fastapi import (APIRouter, BackgroundTasks, Depends, File, Form,
                     HTTPException, UploadFile, status)
from fastapi.responses import JSONResponse

from src.ai.engine import AIEngine
from src.core.config import get_settings
from src.core.database import get_async_session
from src.core.security import get_current_user_id, get_current_user_role
from src.models.training import ModelVersion, TrainingDataset, TrainingJob
from src.schemas.ai import (ErrorResponse, ModelEvaluationRequest,
                            ModelTrainingRequest, ModelTrainingResponse,
                            ModelVersionResponse, PaginatedResponse,
                            SuccessResponse, TrainingDatasetCreate,
                            TrainingDatasetResponse, TrainingDataUpload,
                            TrainingJobStatus, TrainingMetrics)
from src.schemas.chat import (ChatModelEvaluationRequest,
                              ChatModelEvaluationResponse,
                              ChatModelTrainingRequest,
                              ChatModelTrainingResponse,
                              ChatTrainingDataCreate, ChatTrainingDataResponse)

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()

# =============================================================================
# Training Data Management
# =============================================================================


@router.post(
    "/datasets",
    response_model=TrainingDatasetResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_training_dataset(
    dataset: TrainingDatasetCreate,
    current_user_id: str = Depends(get_current_user_id),
    current_user_role: str = Depends(get_current_user_role),
    db=Depends(get_async_session),
):
    """
    Create a new training dataset

    **Admin/Therapist Only**: Only verified users can create training datasets
    """

    # Check permissions
    if current_user_role not in ["admin", "therapist"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and verified therapists can create training datasets",
        )

    try:
        # Create dataset record
        new_dataset = TrainingDataset(
            id=str(uuid4()),
            name=dataset.name,
            description=dataset.description,
            dataset_type=dataset.dataset_type,
            data_format=dataset.data_format,
            created_by=current_user_id,
            version="1.0.0",
            is_active=True,
            metadata={"created_via": "api", "initial_config": dataset.dict()},
        )

        db.add(new_dataset)
        await db.commit()
        await db.refresh(new_dataset)

        logger.info(
            f"Training dataset created: {new_dataset.id} by user {current_user_id}"
        )

        return TrainingDatasetResponse(
            id=new_dataset.id,
            name=new_dataset.name,
            description=new_dataset.description,
            dataset_type=new_dataset.dataset_type,
            data_format=new_dataset.data_format,
            version=new_dataset.version,
            sample_count=0,
            file_size_mb=0,
            is_active=new_dataset.is_active,
            created_at=new_dataset.created_at,
            last_updated=new_dataset.updated_at,
            created_by=current_user_id,
            metadata=new_dataset.metadata,
        )

    except Exception as e:
        logger.error(f"Failed to create dataset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create training dataset",
        )


@router.post("/datasets/{dataset_id}/upload", response_model=SuccessResponse)
async def upload_training_data(
    dataset_id: str,
    background_tasks: BackgroundTasks,
    training_data: str = Form(..., description="JSON training data"),
    file: Optional[UploadFile] = File(None, description="Optional file upload"),
    current_user_id: str = Depends(get_current_user_id),
    current_user_role: str = Depends(get_current_user_role),
    db=Depends(get_async_session),
):
    """
    Upload training data to dataset

    Accepts either JSON data or file upload with training examples.

    **JSON Format Examples:**

    For Mood Analysis:
    ```json
    {
        "type": "mood_analysis",
        "samples": [
            {
                "input": {
                    "mood_score": 7,
                    "activities": ["work", "exercise"],
                    "notes": "Had a good day at work, went for a run"
                },
                "output": {
                    "analysis": "Positive mood indicators with healthy coping strategies",
                    "recommendations": ["Continue exercise routine", "Monitor work stress"],
                    "risk_factors": [],
                    "mood_category": "good"
                }
            }
        ]
    }
    ```

    For Dream Analysis:
    ```json
    {
        "type": "dream_analysis",
        "samples": [
            {
                "input": {
                    "description": "I was flying over a beautiful landscape",
                    "symbols": ["flying", "landscape", "freedom"],
                    "emotions": ["joy", "freedom", "peace"]
                },
                "output": {
                    "interpretation": "Dreams of flying often represent desire for freedom and escape from daily constraints",
                    "symbol_meanings": {
                        "flying": "freedom, escape, transcendence",
                        "landscape": "life journey, personal growth"
                    },
                    "emotional_themes": ["liberation", "spiritual_growth"]
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
            detail="Only admins and verified therapists can upload training data",
        )

    try:
        # Get dataset
        dataset = await db.get(TrainingDataset, dataset_id)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Training dataset not found",
            )

        # Check if user owns dataset or is admin
        if dataset.created_by != current_user_id and current_user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only upload data to your own datasets",
            )

        # Parse training data
        try:
            data = json.loads(training_data)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON format in training data",
            )

        # Validate data structure
        if "type" not in data or "samples" not in data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Training data must contain 'type' and 'samples' fields",
            )

        if not isinstance(data["samples"], list) or len(data["samples"]) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Samples must be a non-empty list",
            )

        # Validate sample structure
        for i, sample in enumerate(data["samples"]):
            if "input" not in sample or "output" not in sample:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Sample {i} must contain 'input' and 'output' fields",
                )

        # Handle file upload if provided
        file_path = None
        if file:
            # Create upload directory
            upload_dir = f"data/training/{dataset_id}"
            os.makedirs(upload_dir, exist_ok=True)

            # Save file
            file_path = f"{upload_dir}/{uuid4()}_{file.filename}"
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)

        # Process data in background
        background_tasks.add_task(
            process_training_data,
            dataset_id=dataset_id,
            training_data=data,
            file_path=file_path,
            uploaded_by=current_user_id,
            db=db,
        )

        logger.info(f"Training data upload initiated for dataset {dataset_id}")

        return SuccessResponse(
            message=f"Training data upload initiated. Processing {len(data['samples'])} samples.",
            data={
                "dataset_id": dataset_id,
                "sample_count": len(data["samples"]),
                "data_type": data["type"],
                "file_uploaded": file is not None,
                "processing_status": "queued",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Training data upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload training data",
        )


@router.get("/datasets", response_model=PaginatedResponse)
async def list_training_datasets(
    page: int = 1,
    page_size: int = 20,
    dataset_type: Optional[str] = None,
    current_user_id: str = Depends(get_current_user_id),
    current_user_role: str = Depends(get_current_user_role),
    db=Depends(get_async_session),
):
    """List training datasets with pagination"""

    if current_user_role not in ["admin", "therapist"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and therapists can view training datasets",
        )

    try:
        # Build query
        query = db.query(TrainingDataset)

        # Filter by type if specified
        if dataset_type:
            query = query.filter(TrainingDataset.dataset_type == dataset_type)

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
            items.append(
                TrainingDatasetResponse(
                    id=dataset.id,
                    name=dataset.name,
                    description=dataset.description,
                    dataset_type=dataset.dataset_type,
                    data_format=dataset.data_format,
                    version=dataset.version,
                    sample_count=dataset.sample_count or 0,
                    file_size_mb=dataset.file_size_mb or 0,
                    is_active=dataset.is_active,
                    created_at=dataset.created_at,
                    last_updated=dataset.updated_at,
                    created_by=dataset.created_by,
                    metadata=dataset.metadata,
                )
            )

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
            has_next=page * page_size < total,
            has_prev=page > 1,
        )

    except Exception as e:
        logger.error(f"Failed to list datasets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve training datasets",
        )


# =============================================================================
# Model Training
# =============================================================================


@router.post(
    "/models/train",
    response_model=ModelTrainingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_model_training(
    training_request: ModelTrainingRequest,
    background_tasks: BackgroundTasks,
    current_user_id: str = Depends(get_current_user_id),
    current_user_role: str = Depends(get_current_user_role),
    db=Depends(get_async_session),
):
    """
    Start training a new AI model

    **Admin Only**: Only admins can initiate model training
    """

    if current_user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can start model training",
        )

    try:
        # Validate datasets exist
        for dataset_id in training_request.dataset_ids:
            dataset = await db.get(TrainingDataset, dataset_id)
            if not dataset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Dataset {dataset_id} not found",
                )
            if not dataset.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Dataset {dataset_id} is not active",
                )

        # Create training job
        training_job = TrainingJob(
            id=str(uuid4()),
            model_name=training_request.model_name,
            model_type=training_request.model_type,
            dataset_ids=training_request.dataset_ids,
            training_config=training_request.training_config,
            hyperparameters=training_request.hyperparameters,
            started_by=current_user_id,
            status="queued",
            progress_percentage=0,
        )

        db.add(training_job)
        await db.commit()
        await db.refresh(training_job)

        # Start training in background
        background_tasks.add_task(execute_model_training, job_id=training_job.id, db=db)

        logger.info(f"Model training started: {training_job.id}")

        return ModelTrainingResponse(
            job_id=training_job.id,
            model_name=training_job.model_name,
            model_type=training_job.model_type,
            status=training_job.status,
            progress_percentage=training_job.progress_percentage,
            started_at=training_job.started_at,
            estimated_completion=None,  # Will be calculated during training
            message="Model training job created and queued for execution",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start model training: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start model training",
        )


@router.get("/models/training/{job_id}/status", response_model=TrainingJobStatus)
async def get_training_status(
    job_id: str,
    current_user_id: str = Depends(get_current_user_id),
    current_user_role: str = Depends(get_current_user_role),
    db=Depends(get_async_session),
):
    """Get training job status and progress"""

    if current_user_role not in ["admin", "therapist"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )

    try:
        training_job = await db.get(TrainingJob, job_id)
        if not training_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Training job not found"
            )

        # Non-admins can only see their own jobs
        if current_user_role != "admin" and training_job.started_by != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own training jobs",
            )

        return TrainingJobStatus(
            job_id=training_job.id,
            model_name=training_job.model_name,
            status=training_job.status,
            progress_percentage=training_job.progress_percentage,
            current_step=training_job.current_step,
            total_steps=training_job.total_steps,
            started_at=training_job.started_at,
            completed_at=training_job.completed_at,
            estimated_completion=training_job.estimated_completion,
            training_metrics=training_job.training_metrics,
            error_message=training_job.error_message,
            logs=(
                training_job.logs[-50:] if training_job.logs else []
            ),  # Last 50 log entries
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get training status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve training status",
        )


@router.get("/models", response_model=PaginatedResponse)
async def list_trained_models(
    page: int = 1,
    page_size: int = 20,
    model_type: Optional[str] = None,
    status: Optional[str] = None,
    current_user_role: str = Depends(get_current_user_role),
    db=Depends(get_async_session),
):
    """List trained models"""

    if current_user_role not in ["admin", "therapist"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )

    try:
        # Build query
        query = db.query(ModelVersion)

        # Apply filters
        if model_type:
            query = query.filter(ModelVersion.model_type == model_type)
        if status:
            query = query.filter(ModelVersion.status == status)

        # Get total count
        total = await query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        models = await query.offset(offset).limit(page_size).all()

        # Convert to response format
        items = []
        for model in models:
            items.append(
                ModelVersionResponse(
                    id=model.id,
                    model_name=model.model_name,
                    model_type=model.model_type,
                    version=model.version,
                    status=model.status,
                    is_active=model.is_active,
                    training_job_id=model.training_job_id,
                    created_at=model.created_at,
                    performance_metrics=model.performance_metrics,
                    model_size_mb=model.model_size_mb,
                    inference_time_ms=model.inference_time_ms,
                )
            )

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
            has_next=page * page_size < total,
            has_prev=page > 1,
        )

    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve models",
        )


# =============================================================================
# Model Evaluation & Testing
# =============================================================================


@router.post("/models/{model_id}/evaluate", response_model=SuccessResponse)
async def evaluate_model(
    model_id: str,
    evaluation_request: ModelEvaluationRequest,
    background_tasks: BackgroundTasks,
    current_user_role: str = Depends(get_current_user_role),
    db=Depends(get_async_session),
):
    """Evaluate model performance on test data"""

    if current_user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can evaluate models",
        )

    try:
        # Get model
        model = await db.get(ModelVersion, model_id)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Model not found"
            )

        # Start evaluation in background
        background_tasks.add_task(
            evaluate_model_performance,
            model_id=model_id,
            test_data=evaluation_request.test_data,
            evaluation_config=evaluation_request.evaluation_config,
            db=db,
        )

        return SuccessResponse(
            message="Model evaluation started",
            data={
                "model_id": model_id,
                "test_samples": len(evaluation_request.test_data),
                "evaluation_status": "queued",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start model evaluation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start model evaluation",
        )


# =============================================================================
# Model Management
# =============================================================================


@router.post("/models/{model_id}/activate", response_model=SuccessResponse)
async def activate_model(
    model_id: str,
    current_user_role: str = Depends(get_current_user_role),
    db=Depends(get_async_session),
):
    """Activate a model for production use"""

    if current_user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can activate models",
        )

    try:
        # Get model
        model = await db.get(ModelVersion, model_id)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Model not found"
            )

        # Deactivate other models of same type
        await db.execute(
            "UPDATE model_versions SET is_active = false WHERE model_type = ? AND id != ?",
            (model.model_type, model_id),
        )

        # Activate this model
        model.is_active = True
        model.activated_at = datetime.utcnow()

        await db.commit()

        logger.info(f"Model activated: {model_id}")

        return SuccessResponse(
            message=f"Model {model.model_name} v{model.version} activated for production use",
            data={
                "model_id": model_id,
                "model_name": model.model_name,
                "version": model.version,
                "activated_at": model.activated_at.isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate model",
        )


# =============================================================================
# Background Tasks
# =============================================================================


async def process_training_data(
    dataset_id: str,
    training_data: Dict[str, Any],
    file_path: Optional[str],
    uploaded_by: str,
    db,
):
    """Process uploaded training data"""

    try:
        # Get dataset
        dataset = await db.get(TrainingDataset, dataset_id)
        if not dataset:
            logger.error(f"Dataset {dataset_id} not found during processing")
            return

        # Process samples
        sample_count = len(training_data["samples"])
        total_size = 0

        # Validate and process each sample
        processed_samples = []
        for sample in training_data["samples"]:
            # Add validation logic here
            processed_sample = {
                "id": str(uuid4()),
                "input": sample["input"],
                "output": sample["output"],
                "processed_at": datetime.utcnow().isoformat(),
                "uploaded_by": uploaded_by,
            }
            processed_samples.append(processed_sample)
            total_size += len(json.dumps(processed_sample))

        # Update dataset
        dataset.sample_count = (dataset.sample_count or 0) + sample_count
        dataset.file_size_mb = (dataset.file_size_mb or 0) + (total_size / 1024 / 1024)
        dataset.updated_at = datetime.utcnow()

        # Store processed data (in production, you'd store this in appropriate format)
        data_file_path = f"data/training/{dataset_id}/processed_{uuid4()}.json"
        os.makedirs(os.path.dirname(data_file_path), exist_ok=True)

        with open(data_file_path, "w") as f:
            json.dump(
                {
                    "metadata": {
                        "dataset_id": dataset_id,
                        "uploaded_by": uploaded_by,
                        "processed_at": datetime.utcnow().isoformat(),
                        "sample_count": sample_count,
                        "data_type": training_data["type"],
                    },
                    "samples": processed_samples,
                },
                f,
                indent=2,
            )

        await db.commit()

        logger.info(f"Training data processed successfully for dataset {dataset_id}")

    except Exception as e:
        logger.error(f"Failed to process training data: {e}")


async def execute_model_training(job_id: str, db):
    """Execute model training job"""

    try:
        # Get training job
        job = await db.get(TrainingJob, job_id)
        if not job:
            logger.error(f"Training job {job_id} not found")
            return

        # Update status
        job.status = "running"
        job.started_at = datetime.utcnow()
        job.current_step = 1
        job.total_steps = 10  # Example
        await db.commit()

        # Simulate training progress
        for step in range(1, 11):
            job.current_step = step
            job.progress_percentage = (step / 10) * 100

            # Add log entry
            if not job.logs:
                job.logs = []
            job.logs.append(f"Step {step}/10: Training in progress...")

            await db.commit()

            # Simulate work
            await asyncio.sleep(2)

        # Complete training
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        job.progress_percentage = 100

        # Create model version
        model_version = ModelVersion(
            id=str(uuid4()),
            model_name=job.model_name,
            model_type=job.model_type,
            version="1.0.0",
            training_job_id=job.id,
            status="trained",
            is_active=False,
            performance_metrics={
                "accuracy": 0.85,
                "precision": 0.82,
                "recall": 0.88,
                "f1_score": 0.85,
            },
            model_size_mb=15.5,
            inference_time_ms=120,
        )

        db.add(model_version)
        await db.commit()

        logger.info(f"Model training completed: {job_id}")

    except Exception as e:
        logger.error(f"Model training failed: {e}")

        # Update job with error
        if job:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            await db.commit()


async def evaluate_model_performance(
    model_id: str,
    test_data: List[Dict[str, Any]],
    evaluation_config: Dict[str, Any],
    db,
):
    """Evaluate model performance"""

    try:
        # Get model
        model = await db.get(ModelVersion, model_id)
        if not model:
            logger.error(f"Model {model_id} not found for evaluation")
            return

        # Run evaluation (simplified simulation)
        correct_predictions = 0
        total_predictions = len(test_data)

        for sample in test_data:
            # Simulate prediction and comparison
            # In reality, you'd load the model and make actual predictions
            predicted = simulate_prediction(sample["input"], model.model_type)
            actual = sample["output"]

            if compare_predictions(predicted, actual):
                correct_predictions += 1

        # Calculate metrics
        accuracy = (
            correct_predictions / total_predictions if total_predictions > 0 else 0
        )

        # Update model with evaluation results
        if not model.performance_metrics:
            model.performance_metrics = {}

        model.performance_metrics.update(
            {
                "test_accuracy": accuracy,
                "test_samples": total_predictions,
                "last_evaluated": datetime.utcnow().isoformat(),
            }
        )

        await db.commit()

        logger.info(
            f"Model evaluation completed: {model_id} - Accuracy: {accuracy:.2%}"
        )

    except Exception as e:
        logger.error(f"Model evaluation failed: {e}")


def simulate_prediction(input_data: Dict[str, Any], model_type: str) -> Dict[str, Any]:
    """Simulate model prediction (replace with actual model inference)"""

    if model_type == "mood_analysis":
        return {
            "analysis": "Simulated mood analysis",
            "recommendations": ["Continue current activities"],
            "mood_category": "neutral",
        }
    elif model_type == "dream_analysis":
        return {
            "interpretation": "Simulated dream interpretation",
            "symbol_meanings": {},
            "emotional_themes": ["neutral"],
        }
    else:
        return {"prediction": "unknown"}


def compare_predictions(predicted: Dict[str, Any], actual: Dict[str, Any]) -> bool:
    """Compare predicted vs actual results (simplified)"""

    # Simplified comparison - in reality, you'd have more sophisticated metrics
    return (
        predicted.get("mood_category") == actual.get("mood_category")
        or len(predicted.get("emotional_themes", [])) > 0
    )
