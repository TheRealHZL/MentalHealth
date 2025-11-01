"""
Mood Entry Schemas

Pydantic Schemas für Mood Tracking.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from src.core.sanitization import sanitize_html, sanitize_text


class MoodEntryCreate(BaseModel):
    """Create mood entry schema"""

    entry_date: date = Field(
        default_factory=lambda: date.today(), description="Entry date"
    )
    mood_score: int = Field(..., ge=1, le=10, description="Mood score (1-10)")
    stress_level: int = Field(..., ge=1, le=10, description="Stress level (1-10)")
    energy_level: int = Field(..., ge=1, le=10, description="Energy level (1-10)")

    sleep_hours: Optional[float] = Field(
        None, ge=0, le=24, description="Hours of sleep"
    )
    sleep_quality: Optional[int] = Field(
        None, ge=1, le=10, description="Sleep quality (1-10)"
    )

    exercise_minutes: Optional[int] = Field(
        None, ge=0, le=1440, description="Exercise minutes"
    )
    exercise_type: Optional[str] = Field(None, max_length=100)

    activities: Optional[List[str]] = None
    symptoms: Optional[List[str]] = None
    triggers: Optional[List[str]] = None
    coping_strategies: Optional[List[str]] = None

    medication_taken: bool = Field(False, description="Was medication taken?")
    medication_names: Optional[List[str]] = None
    medication_effects: Optional[str] = Field(
        None, max_length=500, description="Medication effects"
    )

    social_interactions: Optional[int] = Field(
        None, ge=0, le=50, description="Number of social interactions"
    )
    work_stress: Optional[int] = Field(
        None, ge=1, le=10, description="Work stress level"
    )

    notes: Optional[str] = Field(None, max_length=2000, description="Additional notes")
    gratitude: Optional[str] = Field(
        None, max_length=1000, description="Gratitude notes"
    )
    goals_achieved: Optional[List[str]] = None

    is_private: bool = Field(True, description="Is entry private?")
    tags: Optional[List[str]] = None

    # Input Sanitization Validators (XSS Prevention)
    @field_validator("notes", "gratitude", "medication_effects", mode="before")
    @classmethod
    def sanitize_html_fields(cls, v):
        """Sanitize HTML in rich text fields"""
        if v is not None:
            return sanitize_html(v, strip=False)  # Allow safe HTML
        return v

    @field_validator("exercise_type", mode="before")
    @classmethod
    def sanitize_text_fields(cls, v):
        """Sanitize plain text fields (no HTML)"""
        if v is not None:
            return sanitize_text(v)
        return v

    @field_validator(
        "activities",
        "symptoms",
        "triggers",
        "coping_strategies",
        "medication_names",
        "goals_achieved",
        "tags",
        mode="before",
    )
    @classmethod
    def sanitize_list_fields(cls, v):
        """Sanitize list fields (each element)"""
        if v is not None and isinstance(v, list):
            return [
                sanitize_text(item) if isinstance(item, str) else item for item in v
            ]
        return v


class MoodEntryUpdate(BaseModel):
    """Update mood entry schema"""

    mood_score: Optional[int] = Field(None, ge=1, le=10)
    stress_level: Optional[int] = Field(None, ge=1, le=10)
    energy_level: Optional[int] = Field(None, ge=1, le=10)
    sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    sleep_quality: Optional[int] = Field(None, ge=1, le=10)
    exercise_minutes: Optional[int] = Field(None, ge=0, le=1440)
    notes: Optional[str] = Field(None, max_length=2000)
    tags: Optional[List[str]] = None

    # Input Sanitization Validators (XSS Prevention)
    @field_validator("notes", mode="before")
    @classmethod
    def sanitize_notes(cls, v):
        """Sanitize notes field"""
        if v is not None:
            return sanitize_html(v, strip=False)
        return v

    @field_validator("tags", mode="before")
    @classmethod
    def sanitize_tags(cls, v):
        """Sanitize tags list"""
        if v is not None and isinstance(v, list):
            return [
                sanitize_text(item) if isinstance(item, str) else item for item in v
            ]
        return v


class MoodEntryResponse(BaseModel):
    """Mood entry response schema"""

    id: str
    entry_date: date
    mood_score: int
    stress_level: int
    energy_level: int
    sleep_hours: Optional[float] = None
    sleep_quality: Optional[int] = None
    exercise_minutes: Optional[int] = None
    activities: Optional[List[str]] = None
    symptoms: Optional[List[str]] = None
    triggers: Optional[List[str]] = None
    coping_strategies: Optional[List[str]] = None
    notes: Optional[str] = None
    wellness_score: float
    ai_recommendations: Optional[List[str]] = None
    ai_mood_analysis: Optional[Dict[str, Any]] = None
    created_at: datetime
