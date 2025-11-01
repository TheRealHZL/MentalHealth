"""
AI Training Schemas

Pydantic Schemas für AI Model Training.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field

from .base import BaseSchema


class TrainingJobStatus(str, Enum):
    """Training job status enumeration"""

    PENDING = "pending"
    PREPROCESSING = "preprocessing"
    TRAINING = "training"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ModelType(str, Enum):
    """Model type enumeration"""

    MOOD_PREDICTOR = "mood_predictor"
    DREAM_ANALYZER = "dream_analyzer"
    THERAPY_RECOMMENDER = "therapy_recommender"
    CRISIS_DETECTOR = "crisis_detector"
    PATTERN_RECOGNIZER = "pattern_recognizer"


class TrainingDataUpload(BaseSchema):
    """Training data upload schema"""

    dataset_name: str = Field(
        ..., min_length=3, max_length=200, description="Dataset name"
    )
    dataset_type: str = Field(..., description="Type of dataset (mood, dream, therapy)")
    description: Optional[str] = Field(
        None, max_length=1000, description="Dataset description"
    )
    data_format: str = Field("json", description="Data format (json, csv)")
    file_content: str = Field(
        ..., description="Base64 encoded file content or JSON string"
    )
    metadata: Optional[Dict[str, Any]] = None


class TrainingDatasetCreate(BaseSchema):
    """Training dataset creation schema"""

    name: str = Field(..., min_length=3, max_length=200, description="Dataset name")
    dataset_type: str = Field(..., description="Type of dataset")
    description: Optional[str] = Field(None, max_length=1000)
    source: str = Field(..., description="Data source")
    preprocessing_config: Optional[Dict[str, Any]] = None
    validation_split: float = Field(
        0.2, ge=0.1, le=0.5, description="Validation split ratio"
    )
    test_split: float = Field(0.1, ge=0.0, le=0.3, description="Test split ratio")


class TrainingDatasetResponse(BaseSchema):
    """Training dataset response schema"""

    id: str
    name: str
    dataset_type: str
    description: Optional[str] = None
    source: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    sample_count: int
    feature_count: int
    validation_split: float
    test_split: float
    preprocessing_status: str
    quality_metrics: Dict[str, Any]
    storage_location: str


class ModelTrainingRequest(BaseSchema):
    """Model training request schema"""

    model_name: str = Field(..., min_length=3, max_length=200, description="Model name")
    model_type: ModelType
    dataset_id: str = Field(..., description="Training dataset ID")
    base_model: Optional[str] = Field(None, description="Base model to fine-tune from")

    # Training configuration
    epochs: int = Field(10, ge=1, le=1000, description="Number of training epochs")
    batch_size: int = Field(32, ge=1, le=512, description="Training batch size")
    learning_rate: float = Field(0.001, ge=0.00001, le=1.0, description="Learning rate")
    optimizer: str = Field("adam", description="Optimizer type")

    # Model architecture
    architecture: str = Field("default", description="Model architecture type")
    hyperparameters: Optional[Dict[str, Any]] = None

    # Training options
    early_stopping: bool = Field(True, description="Use early stopping")
    patience: int = Field(5, ge=1, le=50, description="Early stopping patience")
    save_checkpoints: bool = Field(True, description="Save model checkpoints")
    checkpoint_frequency: int = Field(
        5, ge=1, le=100, description="Checkpoint save frequency"
    )

    # Advanced options
    use_gpu: bool = Field(False, description="Use GPU for training")
    distributed_training: bool = Field(False, description="Use distributed training")
    mixed_precision: bool = Field(False, description="Use mixed precision training")

    tags: Optional[List[str]] = None
    notes: Optional[str] = Field(None, max_length=1000, description="Training notes")


class ModelTrainingResponse(BaseSchema):
    """Model training response schema"""

    training_job_id: str
    model_id: str
    model_name: str
    model_type: ModelType
    status: TrainingJobStatus
    started_at: datetime
    estimated_completion: Optional[datetime] = None
    progress_percentage: float
    current_epoch: int
    total_epochs: int
    training_metrics: Dict[str, Any]
    resource_usage: Dict[str, Any]
    message: str


class TrainingMetrics(BaseSchema):
    """Training metrics schema"""

    epoch: int
    loss: float
    accuracy: Optional[float] = None
    validation_loss: Optional[float] = None
    validation_accuracy: Optional[float] = None
    learning_rate: float
    batch_time: float
    memory_usage: Optional[float] = None
    custom_metrics: Optional[Dict[str, float]] = None


class ModelVersionResponse(BaseSchema):
    """Model version response schema"""

    model_id: str
    version: str
    model_name: str
    model_type: ModelType
    created_at: datetime
    training_completed_at: Optional[datetime] = None
    status: str
    performance_metrics: Dict[str, Any]
    training_config: Dict[str, Any]
    dataset_info: Dict[str, Any]
    file_size_mb: float
    deployment_status: str
    is_active: bool
    download_url: Optional[str] = None
    api_endpoint: Optional[str] = None


class ModelEvaluationRequest(BaseSchema):
    """Model evaluation request schema"""

    model_id: str = Field(..., description="Model ID to evaluate")
    dataset_id: Optional[str] = Field(None, description="Test dataset ID")
    evaluation_metrics: List[str] = Field(
        ["accuracy", "precision", "recall", "f1_score"],
        description="Metrics to calculate",
    )
    generate_confusion_matrix: bool = Field(
        True, description="Generate confusion matrix"
    )
    generate_roc_curve: bool = Field(True, description="Generate ROC curve")
    cross_validation_folds: Optional[int] = Field(
        None, ge=2, le=20, description="Number of CV folds"
    )


class ModelEvaluationResponse(BaseSchema):
    """Model evaluation response schema"""

    model_id: str
    evaluation_id: str
    evaluated_at: datetime
    dataset_used: str
    metrics: Dict[str, float]
    confusion_matrix: Optional[List[List[int]]] = None
    roc_curve_data: Optional[Dict[str, Any]] = None
    feature_importance: Optional[Dict[str, float]] = None
    error_analysis: Optional[Dict[str, Any]] = None
    recommendations: List[str]
    comparison_with_baseline: Optional[Dict[str, Any]] = None
