"""
AI Training Models

SQLAlchemy Models für AI Training und Model Management.
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from src.core.database import Base

class TrainingDataset(Base):
    """Training dataset model"""
    __tablename__ = "training_datasets"
    
    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=False)
    dataset_type = Column(String(30), nullable=False, index=True)
    data_format = Column(String(10), nullable=False, default="json")
    version = Column(String(20), nullable=False, default="1.0.0")
    
    # Dataset statistics
    sample_count = Column(Integer, default=0, nullable=False)
    file_size_mb = Column(Float, default=0.0, nullable=False)
    validation_split = Column(Float, default=0.2, nullable=False)
    
    # Status and configuration
    is_active = Column(Boolean, default=True, nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)
    is_validated = Column(Boolean, default=False, nullable=False)
    validation_status = Column(String(20), default="pending")
    validation_notes = Column(Text, nullable=True)
    
    # Data quality metrics
    data_quality_score = Column(Float, nullable=True)
    missing_data_percentage = Column(Float, nullable=True)
    duplicate_data_percentage = Column(Float, nullable=True)
    data_distribution = Column(JSON, nullable=True)
    
    # Storage information
    storage_path = Column(String(500), nullable=True)
    backup_path = Column(String(500), nullable=True)
    checksum = Column(String(64), nullable=True)
    compression_ratio = Column(Float, nullable=True)
    
    # Metadata and tags
    tags = Column(ARRAY(String), nullable=True)
    metadata = Column(JSON, nullable=True)
    schema_definition = Column(JSON, nullable=True)
    
    # User and access control
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    access_level = Column(String(20), default="private", nullable=False)
    allowed_users = Column(ARRAY(String), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_accessed = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    # Usage tracking
    download_count = Column(Integer, default=0, nullable=False)
    training_jobs_count = Column(Integer, default=0, nullable=False)
    last_used_for_training = Column(DateTime, nullable=True)
    
    # Relationships
    training_jobs = relationship("TrainingJob", back_populates="datasets")
    creator = relationship("User", back_populates="training_datasets")
    
    def __repr__(self):
        return f"<TrainingDataset(id={self.id}, name={self.name}, type={self.dataset_type})>"

class TrainingJob(Base):
    """Training job model"""
    __tablename__ = "training_jobs"
    
    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_name = Column(String(100), nullable=False)
    model_name = Column(String(100), nullable=False, index=True)
    model_type = Column(String(30), nullable=False, index=True)
    
    # Job configuration
    dataset_ids = Column(ARRAY(String), nullable=False)
    training_config = Column(JSON, nullable=False)
    hyperparameters = Column(JSON, nullable=True)
    resource_requirements = Column(JSON, nullable=True)
    
    # Status tracking
    status = Column(String(20), default="queued", nullable=False, index=True)
    progress_percentage = Column(Float, default=0.0, nullable=False)
    current_step = Column(Integer, nullable=True)
    total_steps = Column(Integer, nullable=True)
    current_epoch = Column(Integer, nullable=True)
    total_epochs = Column(Integer, nullable=True)
    
    # Timing information
    queued_at = Column(DateTime, default=func.now(), nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    estimated_completion = Column(DateTime, nullable=True)
    total_training_time_seconds = Column(Integer, nullable=True)
    
    # Performance metrics
    training_metrics = Column(JSON, nullable=True)  # Loss, accuracy per epoch
    validation_metrics = Column(JSON, nullable=True)
    best_validation_score = Column(Float, nullable=True)
    final_training_loss = Column(Float, nullable=True)
    final_validation_loss = Column(Float, nullable=True)
    
    # Resource usage
    gpu_hours_used = Column(Float, nullable=True)
    cpu_hours_used = Column(Float, nullable=True)
    memory_peak_gb = Column(Float, nullable=True)
    storage_used_gb = Column(Float, nullable=True)
    
    # Error handling and logging
    error_message = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)
    logs = Column(ARRAY(String), nullable=True)  # Training logs
    checkpoint_path = Column(String(500), nullable=True)
    
    # User and priority
    started_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    priority = Column(Integer, default=5, nullable=False)  # 1-10, higher = more priority
    auto_deploy = Column(Boolean, default=False, nullable=False)
    
    # Experiment tracking
    experiment_id = Column(String(100), nullable=True)
    experiment_tags = Column(ARRAY(String), nullable=True)
    parent_job_id = Column(UUID(as_uuid=True), ForeignKey('training_jobs.id'), nullable=True)
    
    # Notifications
    notify_on_completion = Column(Boolean, default=True, nullable=False)
    notification_channels = Column(ARRAY(String), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    datasets = relationship("TrainingDataset", back_populates="training_jobs")
    starter = relationship("User", back_populates="training_jobs", foreign_keys=[started_by])
    model_versions = relationship("ModelVersion", back_populates="training_job")
    parent_job = relationship("TrainingJob", remote_side=[id])
    child_jobs = relationship("TrainingJob", back_populates="parent_job")
    
    def __repr__(self):
        return f"<TrainingJob(id={self.id}, model={self.model_name}, status={self.status})>"

class ModelVersion(Base):
    """Model version model"""
    __tablename__ = "model_versions"
    
    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String(100), nullable=False, index=True)
    model_type = Column(String(30), nullable=False, index=True)
    version = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    
    # Training information
    training_job_id = Column(UUID(as_uuid=True), ForeignKey('training_jobs.id'), nullable=True)
    trained_on_datasets = Column(ARRAY(String), nullable=True)
    training_duration_hours = Column(Float, nullable=True)
    training_samples_count = Column(Integer, nullable=True)
    
    # Model status and lifecycle
    status = Column(String(20), default="training", nullable=False, index=True)
    is_active = Column(Boolean, default=False, nullable=False)
    is_deprecated = Column(Boolean, default=False, nullable=False)
    deprecation_reason = Column(Text, nullable=True)
    replacement_model_id = Column(UUID(as_uuid=True), ForeignKey('model_versions.id'), nullable=True)
    
    # Performance metrics
    performance_metrics = Column(JSON, nullable=True)  # Accuracy, F1, precision, recall, etc.
    benchmark_scores = Column(JSON, nullable=True)
    validation_results = Column(JSON, nullable=True)
    test_results = Column(JSON, nullable=True)
    
    # Technical specifications
    model_architecture = Column(String(50), nullable=True)
    model_size_mb = Column(Float, nullable=True)
    parameter_count = Column(Integer, nullable=True)
    inference_time_ms = Column(Float, nullable=True)
    memory_requirements_mb = Column(Float, nullable=True)
    
    # Storage and deployment
    model_path = Column(String(500), nullable=True)
    model_format = Column(String(20), nullable=True)  # pytorch, tensorflow, onnx, etc.
    serialization_format = Column(String(20), nullable=True)
    model_checksum = Column(String(64), nullable=True)
    
    # API and deployment information
    api_endpoint = Column(String(500), nullable=True)
    deployment_config = Column(JSON, nullable=True)
    scaling_config = Column(JSON, nullable=True)
    health_check_url = Column(String(500), nullable=True)
    
    # Usage tracking
    prediction_count = Column(Integer, default=0, nullable=False)
    total_inference_time_ms = Column(Float, default=0.0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    last_used = Column(DateTime, nullable=True)
    
    # Quality and monitoring
    drift_detection_enabled = Column(Boolean, default=True, nullable=False)
    monitoring_config = Column(JSON, nullable=True)
    alert_thresholds = Column(JSON, nullable=True)
    quality_score = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    validated_at = Column(DateTime, nullable=True)
    deployed_at = Column(DateTime, nullable=True)
    activated_at = Column(DateTime, nullable=True)
    deprecated_at = Column(DateTime, nullable=True)
    
    # User and access
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    access_level = Column(String(20), default="internal", nullable=False)
    
    # Metadata and tags
    tags = Column(ARRAY(String), nullable=True)
    metadata = Column(JSON, nullable=True)
    changelog = Column(JSON, nullable=True)
    
    # Relationships
    training_job = relationship("TrainingJob", back_populates="model_versions")
    creator = relationship("User", back_populates="model_versions")
    prediction_logs = relationship("PredictionLog", back_populates="model_version")
    evaluations = relationship("ModelEvaluation", back_populates="model_version")
    replacement_model = relationship("ModelVersion", remote_side=[id])
    
    def __repr__(self):
        return f"<ModelVersion(id={self.id}, name={self.model_name}, version={self.version})>"

class PredictionLog(Base):
    """Prediction log model for tracking AI predictions"""
    __tablename__ = "prediction_logs"
    
    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id = Column(String(100), nullable=False, unique=True, index=True)
    
    # Model information
    model_id = Column(UUID(as_uuid=True), ForeignKey('model_versions.id'), nullable=False, index=True)
    model_version = Column(String(20), nullable=False)
    model_type = Column(String(30), nullable=False, index=True)
    
    # User and session
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    session_id = Column(String(100), nullable=True)
    request_source = Column(String(50), nullable=True)  # web, mobile, api, batch
    
    # Input and output data
    input_data = Column(JSON, nullable=False)
    prediction_result = Column(JSON, nullable=False)
    confidence_score = Column(Float, nullable=True)
    
    # Performance metrics
    processing_time_ms = Column(Float, nullable=False)
    queue_time_ms = Column(Float, nullable=True)
    model_inference_time_ms = Column(Float, nullable=True)
    postprocessing_time_ms = Column(Float, nullable=True)
    
    # Quality and feedback
    prediction_quality_score = Column(Float, nullable=True)
    user_feedback_rating = Column(Integer, nullable=True)  # 1-5 stars
    user_feedback_text = Column(Text, nullable=True)
    is_correct_prediction = Column(Boolean, nullable=True)
    
    # Error tracking
    has_error = Column(Boolean, default=False, nullable=False)
    error_type = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Context and metadata
    request_metadata = Column(JSON, nullable=True)
    response_metadata = Column(JSON, nullable=True)
    business_context = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    feedback_received_at = Column(DateTime, nullable=True)
    
    # Privacy and compliance
    is_sensitive_data = Column(Boolean, default=False, nullable=False)
    data_retention_days = Column(Integer, default=365, nullable=False)
    
    # Relationships
    model_version = relationship("ModelVersion", back_populates="prediction_logs")
    user = relationship("User", back_populates="prediction_logs")
    
    def __repr__(self):
        return f"<PredictionLog(id={self.prediction_id}, model={self.model_type})>"

class ModelEvaluation(Base):
    """Model evaluation results"""
    __tablename__ = "model_evaluations"
    
    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_id = Column(String(100), nullable=False, unique=True)
    model_id = Column(UUID(as_uuid=True), ForeignKey('model_versions.id'), nullable=False, index=True)
    
    # Evaluation configuration
    evaluation_type = Column(String(30), nullable=False)  # validation, test, benchmark
    test_dataset_id = Column(UUID(as_uuid=True), ForeignKey('training_datasets.id'), nullable=True)
    test_sample_count = Column(Integer, nullable=False)
    evaluation_config = Column(JSON, nullable=True)
    
    # Results and metrics
    overall_score = Column(Float, nullable=True)
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    
    # Detailed results
    detailed_metrics = Column(JSON, nullable=True)
    confusion_matrix = Column(JSON, nullable=True)
    classification_report = Column(JSON, nullable=True)
    performance_by_class = Column(JSON, nullable=True)
    
    # Error analysis
    error_rate = Column(Float, nullable=True)
    error_analysis = Column(JSON, nullable=True)
    failed_predictions = Column(JSON, nullable=True)
    
    # Performance characteristics
    average_inference_time_ms = Column(Float, nullable=True)
    memory_usage_mb = Column(Float, nullable=True)
    throughput_predictions_per_second = Column(Float, nullable=True)
    
    # Quality and robustness
    robustness_score = Column(Float, nullable=True)
    bias_metrics = Column(JSON, nullable=True)
    fairness_metrics = Column(JSON, nullable=True)
    
    # Status and metadata
    status = Column(String(20), default="completed", nullable=False)
    evaluation_notes = Column(Text, nullable=True)
    recommendations = Column(ARRAY(String), nullable=True)
    
    # Timestamps
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # User information
    evaluated_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Relationships
    model_version = relationship("ModelVersion", back_populates="evaluations")
    test_dataset = relationship("TrainingDataset")
    evaluator = relationship("User")
    
    def __repr__(self):
        return f"<ModelEvaluation(id={self.evaluation_id}, model={self.model_id}, score={self.overall_score})>"

class TrainingDataSample(Base):
    """Individual training data samples"""
    __tablename__ = "training_data_samples"
    
    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey('training_datasets.id'), nullable=False, index=True)
    sample_id = Column(String(100), nullable=False, index=True)
    
    # Sample data
    input_data = Column(JSON, nullable=False)
    output_data = Column(JSON, nullable=False)
    metadata = Column(JSON, nullable=True)
    
    # Quality and validation
    is_validated = Column(Boolean, default=False, nullable=False)
    validation_score = Column(Float, nullable=True)
    validation_notes = Column(Text, nullable=True)
    
    # Sample characteristics
    difficulty_level = Column(Integer, nullable=True)  # 1-10
    sample_weight = Column(Float, default=1.0, nullable=False)
    is_synthetic = Column(Boolean, default=False, nullable=False)
    
    # Usage tracking
    used_in_training = Column(Boolean, default=False, nullable=False)
    used_in_validation = Column(Boolean, default=False, nullable=False)
    used_in_testing = Column(Boolean, default=False, nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)
    
    # Data lineage
    source_type = Column(String(50), nullable=True)  # user_generated, synthetic, imported
    source_reference = Column(String(200), nullable=True)
    parent_sample_id = Column(UUID(as_uuid=True), ForeignKey('training_data_samples.id'), nullable=True)
    
    # Annotations and labels
    annotations = Column(JSON, nullable=True)
    human_verified = Column(Boolean, default=False, nullable=False)
    expert_reviewed = Column(Boolean, default=False, nullable=False)
    review_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    validated_at = Column(DateTime, nullable=True)
    
    # User information
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    validated_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    
    # Relationships
    dataset = relationship("TrainingDataset")
    creator = relationship("User", foreign_keys=[created_by])
    validator = relationship("User", foreign_keys=[validated_by])
    parent_sample = relationship("TrainingDataSample", remote_side=[id])
    child_samples = relationship("TrainingDataSample", back_populates="parent_sample")
    
    def __repr__(self):
        return f"<TrainingDataSample(id={self.sample_id}, dataset={self.dataset_id})>"

class AIModelDeployment(Base):
    """AI model deployment tracking"""
    __tablename__ = "ai_model_deployments"
    
    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deployment_id = Column(String(100), nullable=False, unique=True)
    model_id = Column(UUID(as_uuid=True), ForeignKey('model_versions.id'), nullable=False)
    
    # Deployment configuration
    environment = Column(String(20), nullable=False)  # development, staging, production
    deployment_type = Column(String(30), nullable=False)  # api, batch, streaming
    endpoint_url = Column(String(500), nullable=True)
    
    # Scaling and resource configuration
    min_instances = Column(Integer, default=1, nullable=False)
    max_instances = Column(Integer, default=5, nullable=False)
    current_instances = Column(Integer, default=1, nullable=False)
    auto_scaling_enabled = Column(Boolean, default=True, nullable=False)
    
    # Resource allocation
    cpu_allocation = Column(Float, nullable=True)  # CPU cores
    memory_allocation_mb = Column(Integer, nullable=True)
    gpu_allocation = Column(Float, nullable=True)  # GPU units
    storage_allocation_gb = Column(Integer, nullable=True)
    
    # Status and health
    status = Column(String(20), default="deploying", nullable=False, index=True)
    health_status = Column(String(20), default="unknown", nullable=False)
    last_health_check = Column(DateTime, nullable=True)
    uptime_percentage = Column(Float, default=0.0, nullable=False)
    
    # Performance metrics
    request_count = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    average_response_time_ms = Column(Float, nullable=True)
    throughput_requests_per_second = Column(Float, nullable=True)
    
    # Configuration and settings
    deployment_config = Column(JSON, nullable=True)
    environment_variables = Column(JSON, nullable=True)
    security_config = Column(JSON, nullable=True)
    monitoring_config = Column(JSON, nullable=True)
    
    # Timestamps
    deployed_at = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # User information
    deployed_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Relationships
    model_version = relationship("ModelVersion")
    deployer = relationship("User")
    
    def __repr__(self):
        return f"<AIModelDeployment(id={self.deployment_id}, model={self.model_id}, env={self.environment})>"

# Add to the models __init__.py file
ALL_TRAINING_MODELS = [
    TrainingDataset,
    TrainingJob,
    ModelVersion,
    PredictionLog,
    ModelEvaluation,
    TrainingDataSample,
    AIModelDeployment
]
