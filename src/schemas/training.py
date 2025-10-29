"""
AI Training Schemas

Pydantic Schemas für AI Model Training und Trainingsdaten-Management.
"""

from pydantic import Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

from .base import BaseSchema

# =============================================================================
# Training Data Schemas
# =============================================================================

class DatasetType(str, Enum):
    """Dataset type enumeration"""
    MOOD_ANALYSIS = "mood_analysis"
    DREAM_ANALYSIS = "dream_analysis"
    THERAPY_NOTES = "therapy_notes"
    SYMPTOM_TRACKING = "symptom_tracking"
    CRISIS_DETECTION = "crisis_detection"
    GENERAL_WELLNESS = "general_wellness"

class DataFormat(str, Enum):
    """Data format enumeration"""
    JSON = "json"
    CSV = "csv"
    JSONL = "jsonl"
    XML = "xml"

class ModelType(str, Enum):
    """AI model type enumeration"""
    MOOD_CLASSIFIER = "mood_classifier"
    DREAM_INTERPRETER = "dream_interpreter"
    SENTIMENT_ANALYZER = "sentiment_analyzer"
    RISK_ASSESSOR = "risk_assessor"
    RECOMMENDATION_ENGINE = "recommendation_engine"
    PATTERN_DETECTOR = "pattern_detector"

class TrainingStatus(str, Enum):
    """Training status enumeration"""
    QUEUED = "queued"
    PREPARING = "preparing"
    TRAINING = "training"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ModelStatus(str, Enum):
    """Model status enumeration"""
    TRAINING = "training"
    TRAINED = "trained"
    VALIDATING = "validating"
    VALIDATED = "validated"
    DEPLOYED = "deployed"
    DEPRECATED = "deprecated"
    FAILED = "failed"

# =============================================================================
# Training Dataset Schemas
# =============================================================================

class TrainingDatasetCreate(BaseSchema):
    """Create training dataset schema"""
    name: str = Field(..., min_length=3, max_length=100, description="Dataset name")
    description: str = Field(..., min_length=10, max_length=1000, description="Dataset description")
    dataset_type: DatasetType = Field(..., description="Type of dataset")
    data_format: DataFormat = Field(DataFormat.JSON, description="Data format")
    is_public: bool = Field(False, description="Is dataset publicly available?")
    tags: Optional[List[str]] = Field(None, max_items=10, description="Dataset tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate dataset name"""
        if not v.strip():
            raise ValueError('Dataset name cannot be empty')
        return v.strip()

class TrainingDataUpload(BaseSchema):
    """Training data upload schema"""
    data_type: DatasetType = Field(..., description="Type of training data")
    samples: List[Dict[str, Any]] = Field(..., min_items=1, max_items=10000, description="Training samples")
    validation_split: float = Field(0.2, ge=0.1, le=0.5, description="Validation split ratio")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Upload metadata")
    
    @validator('samples')
    def validate_samples(cls, v):
        """Validate training samples structure"""
        for i, sample in enumerate(v):
            if 'input' not in sample or 'output' not in sample:
                raise ValueError(f'Sample {i} must contain "input" and "output" fields')
            if not isinstance(sample['input'], dict) or not isinstance(sample['output'], dict):
                raise ValueError(f'Sample {i} input and output must be dictionaries')
        return v

class MoodAnalysisTrainingSample(BaseSchema):
    """Mood analysis training sample"""
    input: Dict[str, Any] = Field(..., description="Input features")
    output: Dict[str, Any] = Field(..., description="Expected output")
    
    class Config:
        json_schema_extra = {
            "example": {
                "input": {
                    "mood_score": 7,
                    "stress_level": 4,
                    "energy_level": 6,
                    "sleep_hours": 7.5,
                    "activities": ["work", "exercise", "reading"],
                    "symptoms": [],
                    "notes": "Had a productive day at work and felt energized after exercise"
                },
                "output": {
                    "analysis": "Positive mood with good stress management and healthy activities",
                    "recommendations": [
                        "Continue regular exercise routine",
                        "Maintain consistent sleep schedule",
                        "Consider stress-reduction techniques for work"
                    ],
                    "risk_factors": [],
                    "mood_category": "good",
                    "wellness_score": 7.2,
                    "trend_prediction": "stable_positive"
                }
            }
        }

class DreamAnalysisTrainingSample(BaseSchema):
    """Dream analysis training sample"""
    input: Dict[str, Any] = Field(..., description="Dream input data")
    output: Dict[str, Any] = Field(..., description="Dream analysis output")
    
    class Config:
        json_schema_extra = {
            "example": {
                "input": {
                    "description": "I was flying over a beautiful forest, feeling completely free and peaceful",
                    "dream_type": "lucid",
                    "symbols": ["flying", "forest", "freedom"],
                    "emotions": ["joy", "peace", "liberation"],
                    "vividness": 9,
                    "mood_after_waking": 8
                },
                "output": {
                    "interpretation": "Dreams of flying often represent a desire for freedom and escape from life's constraints. The forest symbolizes personal growth and natural wisdom.",
                    "symbol_meanings": {
                        "flying": "freedom, transcendence, rising above challenges",
                        "forest": "unconscious mind, personal growth, natural wisdom",
                        "freedom": "liberation from restrictions, personal empowerment"
                    },
                    "emotional_themes": ["liberation", "spiritual_growth", "inner_peace"],
                    "psychological_insights": [
                        "Strong desire for personal freedom",
                        "Connection with nature and natural rhythms",
                        "Positive self-image and confidence"
                    ],
                    "life_connections": [
                        "May indicate recent stress or feeling constrained",
                        "Positive outlook on personal growth",
                        "Need for more freedom in daily life"
                    ]
                }
            }
        }

class TrainingDatasetResponse(BaseSchema):
    """Training dataset response schema"""
    id: str
    name: str
    description: str
    dataset_type: DatasetType
    data_format: DataFormat
    version: str
    sample_count: int
    file_size_mb: float
    is_active: bool
    is_public: bool = False
    created_at: datetime
    last_updated: datetime
    created_by: str
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

# =============================================================================
# Model Training Schemas
# =============================================================================

class ModelTrainingRequest(BaseSchema):
    """Model training request schema"""
    model_name: str = Field(..., min_length=3, max_length=100, description="Model name")
    model_type: ModelType = Field(..., description="Type of model to train")
    dataset_ids: List[str] = Field(..., min_items=1, max_items=10, description="Training dataset IDs")
    
    # Training configuration
    training_config: Optional[Dict[str, Any]] = Field(
        default={
            "epochs": 10,
            "batch_size": 32,
            "learning_rate": 0.001,
            "validation_split": 0.2
        },
        description="Training configuration"
    )
    
    # Hyperparameters
    hyperparameters: Optional[Dict[str, Any]] = Field(
        default={},
        description="Model-specific hyperparameters"
    )
    
    # Training options
    use_pretrained: bool = Field(True, description="Use pretrained base model?")
    save_checkpoints: bool = Field(True, description="Save training checkpoints?")
    early_stopping: bool = Field(True, description="Enable early stopping?")
    
    # Resource configuration
    gpu_enabled: bool = Field(True, description="Use GPU acceleration?")
    max_training_time_hours: int = Field(24, ge=1, le=168, description="Max training time in hours")
    
    @validator('model_name')
    def validate_model_name(cls, v):
        """Validate model name"""
        if not v.strip():
            raise ValueError('Model name cannot be empty')
        return v.strip()

class ModelTrainingResponse(BaseSchema):
    """Model training response schema"""
    job_id: str
    model_name: str
    model_type: ModelType
    status: TrainingStatus
    progress_percentage: float
    started_at: Optional[datetime]
    estimated_completion: Optional[datetime]
    message: str

class TrainingJobStatus(BaseSchema):
    """Training job status schema"""
    job_id: str
    model_name: str
    status: TrainingStatus
    progress_percentage: float
    current_step: Optional[int] = None
    total_steps: Optional[int] = None
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    estimated_completion: Optional[datetime]
    training_metrics: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    logs: Optional[List[str]] = None

class TrainingMetrics(BaseSchema):
    """Training metrics schema"""
    epoch: int
    training_loss: float
    validation_loss: float
    training_accuracy: Optional[float] = None
    validation_accuracy: Optional[float] = None
    learning_rate: float
    timestamp: datetime
    additional_metrics: Optional[Dict[str, float]] = None

# =============================================================================
# Model Management Schemas
# =============================================================================

class ModelVersionResponse(BaseSchema):
    """Model version response schema"""
    id: str
    model_name: str
    model_type: ModelType
    version: str
    status: ModelStatus
    is_active: bool
    training_job_id: Optional[str]
    created_at: datetime
    activated_at: Optional[datetime] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    model_size_mb: Optional[float] = None
    inference_time_ms: Optional[float] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None

class ModelEvaluationRequest(BaseSchema):
    """Model evaluation request schema"""
    test_data: List[Dict[str, Any]] = Field(..., min_items=1, max_items=1000, description="Test samples")
    evaluation_config: Optional[Dict[str, Any]] = Field(
        default={
            "metrics": ["accuracy", "precision", "recall", "f1_score"],
            "detailed_report": True
        },
        description="Evaluation configuration"
    )
    
    @validator('test_data')
    def validate_test_data(cls, v):
        """Validate test data structure"""
        for i, sample in enumerate(v):
            if 'input' not in sample or 'output' not in sample:
                raise ValueError(f'Test sample {i} must contain "input" and "output" fields')
        return v

class ModelEvaluationResponse(BaseSchema):
    """Model evaluation response schema"""
    model_id: str
    evaluation_id: str
    status: str
    metrics: Dict[str, float]
    detailed_results: Optional[Dict[str, Any]] = None
    evaluated_at: datetime
    test_sample_count: int

# =============================================================================
# AI Prediction Schemas
# =============================================================================

class PredictionRequest(BaseSchema):
    """AI prediction request schema"""
    model_type: ModelType = Field(..., description="Type of model to use")
    input_data: Dict[str, Any] = Field(..., description="Input data for prediction")
    include_confidence: bool = Field(True, description="Include confidence scores?")
    include_explanation: bool = Field(True, description="Include explanation/reasoning?")
    model_version: Optional[str] = Field(None, description="Specific model version (latest if not specified)")

class PredictionResponse(BaseSchema):
    """AI prediction response schema"""
    prediction_id: str
    model_type: ModelType
    model_version: str
    input_data: Dict[str, Any]
    prediction: Dict[str, Any]
    confidence_score: Optional[float] = None
    explanation: Optional[str] = None
    processing_time_ms: float
    timestamp: datetime

class MoodPredictionResponse(BaseSchema):
    """Mood analysis prediction response"""
    mood_analysis: str
    mood_category: str
    wellness_score: float
    risk_factors: List[str]
    recommendations: List[str]
    trend_prediction: str
    confidence_score: float
    detailed_insights: Dict[str, Any]

class DreamPredictionResponse(BaseSchema):
    """Dream analysis prediction response"""
    interpretation: str
    symbol_meanings: Dict[str, str]
    emotional_themes: List[str]
    psychological_insights: List[str]
    life_connections: List[str]
    spiritual_significance: Optional[str] = None
    confidence_score: float

# =============================================================================
# Data Export Schemas
# =============================================================================

class TrainingDataExportRequest(BaseSchema):
    """Training data export request"""
    dataset_ids: List[str] = Field(..., min_items=1, description="Dataset IDs to export")
    format: DataFormat = Field(DataFormat.JSON, description="Export format")
    include_metadata: bool = Field(True, description="Include metadata?")
    anonymize_data: bool = Field(True, description="Anonymize sensitive data?")
    date_range_start: Optional[datetime] = Field(None, description="Export data from this date")
    date_range_end: Optional[datetime] = Field(None, description="Export data until this date")

class TrainingDataExportResponse(BaseSchema):
    """Training data export response"""
    export_id: str
    status: str
    download_url: Optional[str] = None
    file_size_mb: Optional[float] = None
    expires_at: Optional[datetime] = None
    created_at: datetime

# =============================================================================
# Analytics Schemas
# =============================================================================

class TrainingAnalyticsRequest(BaseSchema):
    """Training analytics request"""
    start_date: Optional[datetime] = Field(None, description="Analytics start date")
    end_date: Optional[datetime] = Field(None, description="Analytics end date")
    model_types: Optional[List[ModelType]] = Field(None, description="Filter by model types")
    include_performance_trends: bool = Field(True, description="Include performance trends?")
    include_usage_stats: bool = Field(True, description="Include usage statistics?")

class TrainingAnalyticsResponse(BaseSchema):
    """Training analytics response"""
    period_summary: Dict[str, Any]
    model_performance: Dict[str, Dict[str, float]]
    training_trends: Dict[str, Any]
    usage_statistics: Dict[str, Any]
    resource_utilization: Dict[str, Any]
    recommendations: List[str]
    generated_at: datetime

# =============================================================================
# Batch Processing Schemas
# =============================================================================

class BatchPredictionRequest(BaseSchema):
    """Batch prediction request schema"""
    model_type: ModelType = Field(..., description="Type of model to use")
    input_samples: List[Dict[str, Any]] = Field(..., min_items=1, max_items=1000, description="Input samples")
    batch_config: Optional[Dict[str, Any]] = Field(
        default={"parallel_processing": True, "chunk_size": 100},
        description="Batch processing configuration"
    )
    
    @validator('input_samples')
    def validate_input_samples(cls, v):
        """Validate input samples"""
        if len(v) > 1000:
            raise ValueError('Maximum 1000 samples per batch')
        return v

class BatchPredictionResponse(BaseSchema):
    """Batch prediction response schema"""
    batch_id: str
    status: str
    total_samples: int
    processed_samples: int
    failed_samples: int
    predictions: List[Dict[str, Any]]
    started_at: datetime
    completed_at: Optional[datetime] = None
    processing_time_seconds: Optional[float] = None

# =============================================================================
# Model Deployment Schemas
# =============================================================================

class ModelDeploymentRequest(BaseSchema):
    """Model deployment request"""
    model_id: str = Field(..., description="Model ID to deploy")
    deployment_environment: str = Field(..., description="Deployment environment")
    scaling_config: Optional[Dict[str, Any]] = Field(
        default={"min_instances": 1, "max_instances": 5, "auto_scaling": True},
        description="Scaling configuration"
    )
    health_check_config: Optional[Dict[str, Any]] = Field(
        default={"enabled": True, "interval_seconds": 30},
        description="Health check configuration"
    )

class ModelDeploymentResponse(BaseSchema):
    """Model deployment response"""
    deployment_id: str
    model_id: str
    environment: str
    status: str
    endpoint_url: Optional[str] = None
    deployed_at: Optional[datetime] = None
    health_status: str
    performance_metrics: Optional[Dict[str, Any]] = None
