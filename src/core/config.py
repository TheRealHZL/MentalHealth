"""
Application Configuration

Zentrale Konfiguration für die MindBridge AI Platform.
"""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "MindBridge AI Platform"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")

    # Security
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_HOURS: int = Field(default=24, env="ACCESS_TOKEN_EXPIRE_HOURS")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")

    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    DATABASE_ECHO: bool = Field(default=False, env="DATABASE_ECHO")

    # CORS and Security
    ALLOWED_HOSTS: str = Field(default="*", env="ALLOWED_HOSTS")
    CORS_ORIGINS: str = Field(default="*", env="CORS_ORIGINS")
    HTTPS_ONLY: bool = Field(default=False, env="HTTPS_ONLY")

    # AI Configuration
    AI_ENGINE_ENABLED: bool = Field(default=True, env="AI_ENGINE_ENABLED")
    AI_ENGINE_URL: Optional[str] = Field(default=None, env="AI_ENGINE_URL")
    AI_ENGINE_API_KEY: Optional[str] = Field(default=None, env="AI_ENGINE_API_KEY")

    # AI Model Configuration
    AI_DEVICE: str = Field(default="cpu", env="AI_DEVICE")
    AI_TEMPERATURE: float = Field(default=0.7, env="AI_TEMPERATURE")
    AI_TOP_P: float = Field(default=0.9, env="AI_TOP_P")
    AI_TOP_K: int = Field(default=50, env="AI_TOP_K")
    AI_MAX_LENGTH: int = Field(default=512, env="AI_MAX_LENGTH")
    MAX_RESPONSE_LENGTH: int = Field(default=300, env="MAX_RESPONSE_LENGTH")

    # Model Paths
    TOKENIZER_PATH: str = Field(
        default="data/models/tokenizer.pkl", env="TOKENIZER_PATH"
    )
    EMOTION_MODEL_PATH: str = Field(
        default="data/models/emotion_classifier.pt", env="EMOTION_MODEL_PATH"
    )
    MOOD_MODEL_PATH: str = Field(
        default="data/models/mood_predictor.pt", env="MOOD_MODEL_PATH"
    )
    CHAT_MODEL_PATH: str = Field(
        default="data/models/chat_generator.pt", env="CHAT_MODEL_PATH"
    )

    # Model Architecture Parameters
    VOCAB_SIZE: int = Field(default=10000, env="VOCAB_SIZE")
    EMBEDDING_DIM: int = Field(default=128, env="EMBEDDING_DIM")
    HIDDEN_DIM: int = Field(default=256, env="HIDDEN_DIM")
    NUM_LAYERS: int = Field(default=2, env="NUM_LAYERS")
    NUM_HEADS: int = Field(default=8, env="NUM_HEADS")
    FF_DIM: int = Field(default=512, env="FF_DIM")
    DROPOUT_RATE: float = Field(default=0.1, env="DROPOUT_RATE")

    # Email Configuration
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USERNAME: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    SMTP_USE_TLS: bool = Field(default=True, env="SMTP_USE_TLS")
    FROM_EMAIL: str = Field(default="noreply@mindbridge.app", env="FROM_EMAIL")

    # File Storage
    UPLOAD_DIR: str = Field(default="data/uploads", env="UPLOAD_DIR")
    MAX_UPLOAD_SIZE: int = Field(
        default=10 * 1024 * 1024, env="MAX_UPLOAD_SIZE"
    )  # 10MB
    ALLOWED_FILE_TYPES: str = Field(
        default="pdf,jpg,jpeg,png", env="ALLOWED_FILE_TYPES"
    )

    # Redis Configuration
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    DEFAULT_RATE_LIMIT: int = Field(default=100, env="DEFAULT_RATE_LIMIT")  # per hour
    AUTH_RATE_LIMIT: int = Field(default=5, env="AUTH_RATE_LIMIT")  # per 15 minutes

    # Monitoring and Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    ANALYTICS_ENABLED: bool = Field(default=True, env="ANALYTICS_ENABLED")

    # Feature Flags
    THERAPIST_VERIFICATION_REQUIRED: bool = Field(
        default=True, env="THERAPIST_VERIFICATION_REQUIRED"
    )
    EMAIL_VERIFICATION_REQUIRED: bool = Field(
        default=False, env="EMAIL_VERIFICATION_REQUIRED"
    )
    SHARING_ENABLED: bool = Field(default=True, env="SHARING_ENABLED")

    # Business Logic
    MAX_MOOD_ENTRIES_PER_DAY: int = Field(default=10, env="MAX_MOOD_ENTRIES_PER_DAY")
    MAX_DREAM_ENTRIES_PER_DAY: int = Field(default=5, env="MAX_DREAM_ENTRIES_PER_DAY")
    MAX_THERAPY_NOTES_PER_DAY: int = Field(default=20, env="MAX_THERAPY_NOTES_PER_DAY")
    DEFAULT_SHARE_KEY_EXPIRY_DAYS: int = Field(
        default=90, env="DEFAULT_SHARE_KEY_EXPIRY_DAYS"
    )

    # External Services
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def get_database_url(self) -> str:
        """Get database URL with proper formatting"""
        return self.DATABASE_URL

    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT.lower() == "production"

    def is_development(self) -> bool:
        """Check if running in development"""
        return self.ENVIRONMENT.lower() == "development"

    def get_cors_origins(self) -> List[str]:
        """Get CORS origins"""
        if self.is_development():
            return ["*"]
        return self.CORS_ORIGINS

    def get_allowed_hosts(self) -> List[str]:
        """Get allowed hosts"""
        if self.is_development():
            return ["*"]
        # Parse comma-separated string to list
        if isinstance(self.ALLOWED_HOSTS, str):
            return [h.strip() for h in self.ALLOWED_HOSTS.split(",")]
        return self.ALLOWED_HOSTS


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Environment-specific configurations
class DevelopmentSettings(Settings):
    """Development environment settings"""

    DEBUG: bool = True
    DATABASE_ECHO: bool = True
    CORS_ORIGINS: str = "*"
    ALLOWED_HOSTS: str = "*"
    HTTPS_ONLY: bool = False


class ProductionSettings(Settings):
    """Production environment settings"""

    DEBUG: bool = False
    DATABASE_ECHO: bool = False
    HTTPS_ONLY: bool = True
    RATE_LIMIT_ENABLED: bool = True


class TestSettings(Settings):
    """Test environment settings"""

    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./test.db"
    RATE_LIMIT_ENABLED: bool = False
    EMAIL_VERIFICATION_REQUIRED: bool = False


def get_environment_settings(environment: str) -> Settings:
    """Get settings for specific environment"""

    environments = {
        "development": DevelopmentSettings,
        "production": ProductionSettings,
        "test": TestSettings,
    }

    settings_class = environments.get(environment.lower(), Settings)
    return settings_class()


# Configuration validation
def validate_configuration(settings: Settings):
    """Validate configuration settings"""

    errors = []

    # Required settings
    if not settings.SECRET_KEY:
        errors.append("SECRET_KEY is required")

    if not settings.DATABASE_URL:
        errors.append("DATABASE_URL is required")

    # Security validations
    if settings.is_production():
        if settings.SECRET_KEY == "development-secret-key":
            errors.append("Must use secure SECRET_KEY in production")

        if not settings.HTTPS_ONLY:
            errors.append("HTTPS_ONLY must be True in production")

        if "*" in settings.ALLOWED_HOSTS:
            errors.append("Must specify explicit ALLOWED_HOSTS in production")

    # AI configuration
    # if settings.AI_ENGINE_ENABLED and not settings.AI_ENGINE_URL:
    # errors.append("AI_ENGINE_URL required when AI_ENGINE_ENABLED is True")

    # Email configuration
    if settings.EMAIL_VERIFICATION_REQUIRED:
        if not all(
            [settings.SMTP_HOST, settings.SMTP_USERNAME, settings.SMTP_PASSWORD]
        ):
            errors.append(
                "SMTP configuration required when EMAIL_VERIFICATION_REQUIRED is True"
            )

    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")

    return True


# Export commonly used settings
settings = get_settings()

# Validate configuration on import
import logging
logger = logging.getLogger(__name__)

try:
    validate_configuration(settings)
except ValueError as e:
    logger.warning(f"Configuration warning: {e}")
