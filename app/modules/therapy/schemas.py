"""
Therapy Note Schemas

Pydantic Schemas für Therapy Notes.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from src.core.sanitization import sanitize_html, sanitize_text


class TherapyNoteType(str, Enum):
    """Therapy note type enumeration"""

    SESSION_NOTES = "session_notes"
    SELF_REFLECTION = "self_reflection"
    HOMEWORK = "homework"
    PROGRESS_UPDATE = "progress_update"
    CRISIS_NOTE = "crisis_note"
    MEDICATION_LOG = "medication_log"
    GOAL_SETTING = "goal_setting"
    BREAKTHROUGH = "breakthrough"


class TherapyTechnique(str, Enum):
    """Therapy technique enumeration"""

    CBT = "cbt"
    DBT = "dbt"
    MINDFULNESS = "mindfulness"
    EXPOSURE = "exposure"
    EMDR = "emdr"
    SOLUTION_FOCUSED = "solution_focused"
    PSYCHODYNAMIC = "psychodynamic"
    HUMANISTIC = "humanistic"
    ACCEPTANCE_COMMITMENT = "acceptance_commitment"
    INTERPERSONAL = "interpersonal"


class TherapyNoteCreate(BaseModel):
    """Create therapy note schema"""

    note_date: date = Field(
        default_factory=lambda: date.today(), description="Note date"
    )
    note_type: TherapyNoteType = Field(
        TherapyNoteType.SELF_REFLECTION, description="Type of note"
    )
    title: str = Field(..., min_length=1, max_length=200, description="Note title")
    content: str = Field(
        ..., min_length=10, max_length=10000, description="Note content"
    )

    session_number: Optional[int] = Field(None, ge=1, description="Session number")
    therapist_name: Optional[str] = Field(
        None, max_length=200, description="Therapist name"
    )
    session_duration: Optional[int] = Field(
        None, ge=1, le=480, description="Session duration in minutes"
    )
    session_format: Optional[str] = Field(None, description="in_person, video, phone")

    techniques_used: Optional[List[TherapyTechnique]] = None
    homework_assigned: Optional[List[str]] = None
    homework_completed: Optional[List[str]] = None

    goals_discussed: Optional[List[str]] = None
    goals_achieved: Optional[List[str]] = None
    progress_made: Optional[str] = Field(
        None, max_length=1000, description="Progress made"
    )
    challenges_faced: Optional[List[str]] = None

    mood_before_session: Optional[int] = Field(
        None, ge=1, le=10, description="Mood before session"
    )
    mood_after_session: Optional[int] = Field(
        None, ge=1, le=10, description="Mood after session"
    )
    anxiety_level: Optional[int] = Field(None, ge=1, le=10, description="Anxiety level")
    key_emotions: Optional[List[str]] = None

    key_insights: Optional[str] = Field(
        None, max_length=2000, description="Key insights"
    )
    breakthrough_moments: Optional[List[str]] = None
    patterns_recognized: Optional[List[str]] = None

    action_items: Optional[List[str]] = None
    next_session_focus: Optional[List[str]] = None

    medications_discussed: Optional[List[str]] = None
    medication_changes: Optional[str] = Field(
        None, max_length=500, description="Medication changes"
    )
    side_effects_noted: Optional[List[str]] = None

    safety_plan_updated: bool = Field(False, description="Was safety plan updated?")
    crisis_triggers_identified: Optional[List[str]] = None
    coping_strategies_practiced: Optional[List[str]] = None

    is_private: bool = Field(True, description="Is note private?")
    share_with_therapist: bool = Field(False, description="Share with therapist?")
    therapist_can_comment: bool = Field(False, description="Can therapist comment?")
    tags: Optional[List[str]] = None

    # Input Sanitization Validators (XSS Prevention)
    @field_validator("title", "therapist_name", "session_format", mode="before")
    @classmethod
    def sanitize_short_fields(cls, v):
        """Sanitize short text fields (no HTML)"""
        if v is not None:
            return sanitize_text(v)
        return v

    @field_validator(
        "content", "progress_made", "key_insights", "medication_changes", mode="before"
    )
    @classmethod
    def sanitize_long_fields(cls, v):
        """Sanitize long text fields (allow safe HTML for formatting)"""
        if v is not None:
            return sanitize_html(v, strip=False)
        return v

    @field_validator(
        "homework_assigned",
        "homework_completed",
        "goals_discussed",
        "goals_achieved",
        "challenges_faced",
        "key_emotions",
        "breakthrough_moments",
        "patterns_recognized",
        "action_items",
        "next_session_focus",
        "medications_discussed",
        "side_effects_noted",
        "crisis_triggers_identified",
        "coping_strategies_practiced",
        "tags",
        mode="before",
    )
    @classmethod
    def sanitize_list_fields(cls, v):
        """Sanitize list fields"""
        if v is not None and isinstance(v, list):
            return [
                sanitize_text(item) if isinstance(item, str) else item for item in v
            ]
        return v


class TherapyNoteUpdate(BaseModel):
    """Update therapy note schema"""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=10, max_length=10000)
    techniques_used: Optional[List[TherapyTechnique]] = None
    goals_discussed: Optional[List[str]] = None
    progress_made: Optional[str] = Field(None, max_length=1000)
    key_insights: Optional[str] = Field(None, max_length=2000)
    action_items: Optional[List[str]] = None
    share_with_therapist: Optional[bool] = None
    tags: Optional[List[str]] = None

    # Input Sanitization Validators (XSS Prevention)
    @field_validator("title", mode="before")
    @classmethod
    def sanitize_title(cls, v):
        if v is not None:
            return sanitize_text(v)
        return v

    @field_validator("content", "progress_made", "key_insights", mode="before")
    @classmethod
    def sanitize_content(cls, v):
        if v is not None:
            return sanitize_html(v, strip=False)
        return v

    @field_validator("goals_discussed", "action_items", "tags", mode="before")
    @classmethod
    def sanitize_lists(cls, v):
        if v is not None and isinstance(v, list):
            return [
                sanitize_text(item) if isinstance(item, str) else item for item in v
            ]
        return v


class TherapyNoteResponse(BaseModel):
    """Therapy note response schema"""

    id: str
    note_date: date
    note_type: TherapyNoteType
    title: str
    content: str
    session_number: Optional[int] = None
    therapist_name: Optional[str] = None
    techniques_used: Optional[List[str]] = None
    goals_discussed: Optional[List[str]] = None
    progress_made: Optional[str] = None
    mood_before_session: Optional[int] = None
    mood_after_session: Optional[int] = None
    mood_improvement: int
    key_insights: Optional[str] = None
    action_items: Optional[List[str]] = None
    ai_insights: Optional[str] = None
    progress_analysis: Optional[Dict[str, Any]] = None
    suggested_next_steps: Optional[List[str]] = None
    session_effectiveness: float
    is_private: bool
    share_with_therapist: bool
    created_at: datetime
