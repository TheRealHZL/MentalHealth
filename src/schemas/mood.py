"""
Mood Entry Schemas

Pydantic Schemas für Mood Tracking.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date


class MoodEntryCreate(BaseModel):
    """Create mood entry schema"""
    entry_date: date = Field(default_factory=lambda: date.today(), description="Entry date")
    mood_score: int = Field(..., ge=1, le=10, description="Mood score (1-10)")
    stress_level: int = Field(..., ge=1, le=10, description="Stress level (1-10)")
    energy_level: int = Field(..., ge=1, le=10, description="Energy level (1-10)")
    
    sleep_hours: Optional[float] = Field(None, ge=0, le=24, description="Hours of sleep")
    sleep_quality: Optional[int] = Field(None, ge=1, le=10, description="Sleep quality (1-10)")
    
    exercise_minutes: Optional[int] = Field(None, ge=0, le=1440, description="Exercise minutes")
    exercise_type: Optional[str] = Field(None, max_length=100)
    
    activities: Optional[List[str]] = None
    symptoms: Optional[List[str]] = None
    triggers: Optional[List[str]] = None
    coping_strategies: Optional[List[str]] = None
    
    medication_taken: bool = Field(False, description="Was medication taken?")
    medication_names: Optional[List[str]] = None
    medication_effects: Optional[str] = Field(None, max_length=500, description="Medication effects")
    
    social_interactions: Optional[int] = Field(None, ge=0, le=50, description="Number of social interactions")
    work_stress: Optional[int] = Field(None, ge=1, le=10, description="Work stress level")
    
    notes: Optional[str] = Field(None, max_length=2000, description="Additional notes")
    gratitude: Optional[str] = Field(None, max_length=1000, description="Gratitude notes")
    goals_achieved: Optional[List[str]] = None
    
    is_private: bool = Field(True, description="Is entry private?")
    tags: Optional[List[str]] = None


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
