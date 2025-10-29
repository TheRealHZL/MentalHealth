"""
Training Configuration

Zentrale Konfiguration für Model Training
"""

from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path

@dataclass
class TrainingConfig:
    """Training Configuration"""
    
    # Model Settings
    model_type: str = "sentiment_analyzer"  # sentiment_analyzer, emotion_classifier, mood_predictor, chat_generator
    model_name: str = "model_v1"
    
    # Data Settings
    data_dir: str = "data/training"
    train_file: str = "train.json"
    val_file: str = "val.json"
    test_file: str = "test.json"
    
    # Training Hyperparameters
    batch_size: int = 32
    learning_rate: float = 0.001
    num_epochs: int = 10
    warmup_steps: int = 500
    gradient_accumulation_steps: int = 1
    max_grad_norm: float = 1.0
    
    # Optimizer Settings
    optimizer: str = "adamw"  # adam, adamw, sgd
    weight_decay: float = 0.01
    adam_epsilon: float = 1e-8
    adam_beta1: float = 0.9
    adam_beta2: float = 0.999
    
    # Scheduler Settings
    scheduler: str = "linear"  # linear, cosine, constant
    num_warmup_steps: int = 0
    
    # Model Architecture (Sentiment Analyzer)
    vocab_size: int = 10000
    embedding_dim: int = 128
    hidden_dim: int = 256
    num_layers: int = 2
    dropout: float = 0.3
    
    # Model Architecture (Emotion Classifier)
    num_emotions: int = 7
    
    # Model Architecture (Mood Predictor)
    sequence_length: int = 7
    num_metadata_features: int = 10
    
    # Model Architecture (Chat Generator)
    num_heads: int = 8
    ff_dim: int = 2048
    max_length: int = 512
    
    # Regularization
    dropout_rate: float = 0.3
    label_smoothing: float = 0.1
    
    # Early Stopping
    early_stopping_patience: int = 3
    early_stopping_metric: str = "val_loss"
    early_stopping_mode: str = "min"  # min or max
    
    # Checkpointing
    checkpoint_dir: str = "checkpoints"
    save_every_n_epochs: int = 1
    keep_last_n_checkpoints: int = 3
    
    # Logging
    log_dir: str = "logs"
    log_every_n_steps: int = 100
    evaluate_every_n_steps: int = 500
    
    # Hardware
    device: str = "cuda"  # cuda, cpu, mps
    num_workers: int = 4
    pin_memory: bool = True
    mixed_precision: bool = False  # Use AMP for faster training
    
    # Reproducibility
    seed: int = 42
    deterministic: bool = True
    
    # Distributed Training
    distributed: bool = False
    world_size: int = 1
    rank: int = 0
    
    # Weights & Biases
    use_wandb: bool = False
    wandb_project: str = "mindbridge-training"
    wandb_entity: Optional[str] = None
    
    def __post_init__(self):
        """Create necessary directories"""
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)
        Path(self.checkpoint_dir).mkdir(parents=True, exist_ok=True)
        Path(self.log_dir).mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def from_dict(cls, config_dict: dict) -> 'TrainingConfig':
        """Create config from dictionary"""
        return cls(**config_dict)
    
    def to_dict(self) -> dict:
        """Convert config to dictionary"""
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith('_')
        }

@dataclass
class SentimentTrainingConfig(TrainingConfig):
    """Sentiment Analyzer specific config"""
    model_type: str = "sentiment_analyzer"
    num_classes: int = 3  # negative, neutral, positive
    embedding_dim: int = 128
    hidden_dim: int = 256
    num_layers: int = 2

@dataclass
class EmotionTrainingConfig(TrainingConfig):
    """Emotion Classifier specific config"""
    model_type: str = "emotion_classifier"
    num_emotions: int = 7  # joy, sadness, anger, fear, surprise, disgust, neutral
    embedding_dim: int = 256
    hidden_dim: int = 512
    num_layers: int = 3

@dataclass
class MoodTrainingConfig(TrainingConfig):
    """Mood Predictor specific config"""
    model_type: str = "mood_predictor"
    sequence_length: int = 7
    embedding_dim: int = 128
    hidden_dim: int = 256
    num_layers: int = 3
    num_metadata_features: int = 10

@dataclass
class ChatTrainingConfig(TrainingConfig):
    """Chat Generator specific config"""
    model_type: str = "chat_generator"
    vocab_size: int = 30000
    embedding_dim: int = 512
    hidden_dim: int = 512
    num_layers: int = 6
    num_heads: int = 8
    ff_dim: int = 2048
    max_length: int = 512
    batch_size: int = 16  # Smaller batch for transformer
    gradient_accumulation_steps: int = 4
