"""
Dream Entry Schemas

Pydantic Schemas für Dream Journal.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum
import re
from src.core.sanitization import sanitize_html, sanitize_text


class DreamType(str, Enum):
    """Dream type enumeration"""
    NORMAL = "normal"
    LUCID = "lucid"
    NIGHTMARE = "nightmare"
    RECURRING = "recurring"
    PROPHETIC = "prophetic"
    HEALING = "healing"
    SYMBOLIC = "symbolic"


class DreamEntryCreate(BaseModel):
    """Create dream entry schema"""
    dream_date: date = Field(default_factory=lambda: date.today(), description="Dream date")
    dream_type: DreamType = Field(DreamType.NORMAL, description="Type of dream")
    title: Optional[str] = Field(None, max_length=200, description="Dream title")
    description: str = Field(..., min_length=10, max_length=5000, description="Dream description")
    
    vividness: Optional[int] = Field(None, ge=1, le=10, description="Dream vividness (1-10)")
    emotional_intensity: Optional[int] = Field(None, ge=1, le=10, description="Emotional intensity (1-10)")
    mood_during_dream: Optional[List[int]] = None
    mood_after_waking: int = Field(..., ge=1, le=10, description="Mood after waking (1-10)")
    
    people_in_dream: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    objects: Optional[List[str]] = None
    colors: Optional[List[str]] = None
    symbols: Optional[List[str]] = None
    emotions_felt: Optional[List[str]] = None
    physical_sensations: Optional[List[str]] = None
    
    sleep_quality: Optional[int] = Field(None, ge=1, le=10, description="Sleep quality")
    time_to_sleep: Optional[str] = Field(None, description="Time went to sleep (HH:MM)")
    wake_up_time: Optional[str] = Field(None, description="Wake up time (HH:MM)")
    sleep_duration: Optional[float] = Field(None, ge=0, le=24, description="Hours slept")
    
    became_lucid: bool = Field(False, description="Did you become lucid?")
    lucidity_trigger: Optional[str] = Field(None, max_length=200, description="What made you realize it was a dream")
    lucid_actions: Optional[List[str]] = None
    lucid_control_level: Optional[int] = Field(None, ge=1, le=10, description="Level of control when lucid")
    
    personal_interpretation: Optional[str] = Field(None, max_length=2000, description="Your interpretation")
    life_connection: Optional[str] = Field(None, max_length=1000, description="Connection to real life")
    recurring_elements: Optional[List[str]] = None
    
    dream_recall_clarity: Optional[int] = Field(None, ge=1, le=10, description="How clearly remembered")
    entry_delay_hours: Optional[int] = Field(None, ge=0, le=168, description="Hours between dream and entry")
    
    is_private: bool = Field(True, description="Is entry private?")
    tags: Optional[List[str]] = None
    
    @field_validator('time_to_sleep', 'wake_up_time')
    @classmethod
    def validate_time_format(cls, v):
        """Validate time format"""
        if v and not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', v):
            raise ValueError('Time must be in HH:MM format')
        return v

    # Input Sanitization Validators (XSS Prevention)
    @field_validator('title', 'lucidity_trigger', mode='before')
    @classmethod
    def sanitize_short_text(cls, v):
        """Sanitize short text fields (no HTML)"""
        if v is not None:
            return sanitize_text(v)
        return v

    @field_validator('description', 'personal_interpretation', 'life_connection', mode='before')
    @classmethod
    def sanitize_long_text(cls, v):
        """Sanitize long text fields (allow safe HTML)"""
        if v is not None:
            return sanitize_html(v, strip=False)
        return v

    @field_validator('people_in_dream', 'locations', 'objects', 'colors', 'symbols',
                     'emotions_felt', 'physical_sensations', 'lucid_actions',
                     'recurring_elements', 'tags', mode='before')
    @classmethod
    def sanitize_dream_lists(cls, v):
        """Sanitize list fields"""
        if v is not None and isinstance(v, list):
            return [sanitize_text(item) if isinstance(item, str) else item for item in v]
        return v


class DreamEntryUpdate(BaseModel):
    """Update dream entry schema"""
    dream_type: Optional[DreamType] = None
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=5000)
    vividness: Optional[int] = Field(None, ge=1, le=10)
    symbols: Optional[List[str]] = None
    emotions_felt: Optional[List[str]] = None
    personal_interpretation: Optional[str] = Field(None, max_length=2000)
    life_connection: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = None

    # Input Sanitization Validators (XSS Prevention)
    @field_validator('title', mode='before')
    @classmethod
    def sanitize_title(cls, v):
        if v is not None:
            return sanitize_text(v)
        return v

    @field_validator('description', 'personal_interpretation', 'life_connection', mode='before')
    @classmethod
    def sanitize_text_fields(cls, v):
        if v is not None:
            return sanitize_html(v, strip=False)
        return v

    @field_validator('symbols', 'emotions_felt', 'tags', mode='before')
    @classmethod
    def sanitize_lists(cls, v):
        if v is not None and isinstance(v, list):
            return [sanitize_text(item) if isinstance(item, str) else item for item in v]
        return v


class DreamEntryResponse(BaseModel):
    """Dream entry response schema"""
    id: str
    dream_date: date
    dream_type: DreamType
    title: Optional[str] = None
    description: str
    vividness: Optional[int] = None
    emotional_intensity: Optional[int] = None
    mood_after_waking: int
    became_lucid: bool
    people_in_dream: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    symbols: Optional[List[str]] = None
    emotions_felt: Optional[List[str]] = None
    personal_interpretation: Optional[str] = None
    ai_dream_analysis: Optional[str] = None
    symbol_interpretations: Optional[Dict[str, str]] = None
    emotional_insights: Optional[List[str]] = None
    dream_quality_score: float
    created_at: datetime
