"""
AI & Core Schemas

Pydantic Schemas für AI-Integration und Kern-Funktionalitäten.
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date, time
from enum import Enum
import re

# =============================================================================
# User & Authentication Schemas
# =============================================================================

class UserRole(str, Enum):
    """User role enumeration"""
    PATIENT = "patient"
    THERAPIST = "therapist"
    ADMIN = "admin"

class UserRegistration(BaseModel):
    """User registration schema"""
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password (8-128 characters)")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    timezone: Optional[str] = Field("Europe/Berlin", description="User timezone")
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v

class TherapistRegistration(BaseModel):
    """Therapist registration schema"""
    email: EmailStr = Field(..., description="Professional email address")
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    license_number: str = Field(..., min_length=3, max_length=100, description="Professional license number")
    specializations: List[str] = Field(..., min_items=1, max_items=10, description="Areas of specialization")
    practice_address: Optional[str] = Field(None, max_length=500, description="Practice address")
    phone_number: Optional[str] = Field(None, description="Practice phone number")
    bio: Optional[str] = Field(None, max_length=2000, description="Professional bio")

class TherapistVerification(BaseModel):
    """Therapist verification schema"""
    therapist_id: str = Field(..., description="Therapist ID to verify")
    admin_notes: Optional[str] = Field(None, max_length=1000, description="Admin verification notes")

class UserLogin(BaseModel):
    """User login schema"""
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Password")

class PasswordChange(BaseModel):
    """Password change schema"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")

class UserProfileUpdate(BaseModel):
    """User profile update schema"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    timezone: Optional[str] = Field(None, description="User timezone")
    bio: Optional[str] = Field(None, max_length=2000)
    specializations: Optional[List[str]] = Field(None, max_items=10)
    practice_address: Optional[str] = Field(None, max_length=500)
    phone_number: Optional[str] = Field(None)

class UserProfileResponse(BaseModel):
    """User profile response schema"""
    id: str
    email: str
    first_name: str
    last_name: str
    role: UserRole
    is_verified: bool
    timezone: str
    created_at: datetime
    last_login: Optional[datetime]
    statistics: Optional[Dict[str, Any]] = None
    
    # Therapist-specific fields
    license_number: Optional[str] = None
    specializations: Optional[List[str]] = None
    practice_address: Optional[str] = None
    phone_number: Optional[str] = None
    bio: Optional[str] = None
    verification_status: Optional[str] = None

class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]
    message: Optional[str] = None
    next_steps: Optional[List[str]] = None

# =============================================================================
# Mood Entry Schemas
# =============================================================================

class MoodLevel(int, Enum):
    """Mood level enumeration"""
    VERY_LOW = 1
    LOW = 2
    BELOW_AVERAGE = 3
    SLIGHTLY_LOW = 4
    NEUTRAL = 5
    SLIGHTLY_HIGH = 6
    ABOVE_AVERAGE = 7
    HIGH = 8
    VERY_HIGH = 9
    EXCELLENT = 10

class MoodEntryCreate(BaseModel):
    """Create mood entry schema"""
    date: date = Field(default_factory=date.today, description="Entry date")
    mood_score: int = Field(..., ge=1, le=10, description="Mood score (1-10)")
    stress_level: int = Field(..., ge=1, le=10, description="Stress level (1-10)")
    energy_level: int = Field(..., ge=1, le=10, description="Energy level (1-10)")
    
    sleep_hours: Optional[float] = Field(None, ge=0, le=24, description="Hours of sleep")
    sleep_quality: Optional[int] = Field(None, ge=1, le=10, description="Sleep quality (1-10)")
    
    exercise_minutes: Optional[int] = Field(None, ge=0, le=1440, description="Exercise minutes")
    exercise_type: Optional[str] = Field(None, max_length=100)
    
    activities: Optional[List[str]] = Field(None, max_items=20, description="Activities done")
    symptoms: Optional[List[str]] = Field(None, max_items=15, description="Symptoms experienced")
    triggers: Optional[List[str]] = Field(None, max_items=10, description="Mood triggers")
    coping_strategies: Optional[List[str]] = Field(None, max_items=10, description="Coping strategies used")
    
    medication_taken: bool = Field(False, description="Was medication taken?")
    medication_names: Optional[List[str]] = Field(None, max_items=10)
    medication_effects: Optional[str] = Field(None, max_length=500, description="Medication effects")
    
    social_interactions: Optional[int] = Field(None, ge=0, le=50, description="Number of social interactions")
    work_stress: Optional[int] = Field(None, ge=1, le=10, description="Work stress level")
    
    notes: Optional[str] = Field(None, max_length=2000, description="Additional notes")
    gratitude: Optional[str] = Field(None, max_length=1000, description="Gratitude notes")
    goals_achieved: Optional[List[str]] = Field(None, max_items=10, description="Goals achieved today")
    
    is_private: bool = Field(True, description="Is entry private?")
    tags: Optional[List[str]] = Field(None, max_items=10, description="User tags")

class MoodEntryUpdate(BaseModel):
    """Update mood entry schema"""
    mood_score: Optional[int] = Field(None, ge=1, le=10)
    stress_level: Optional[int] = Field(None, ge=1, le=10)
    energy_level: Optional[int] = Field(None, ge=1, le=10)
    sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    sleep_quality: Optional[int] = Field(None, ge=1, le=10)
    exercise_minutes: Optional[int] = Field(None, ge=0, le=1440)
    notes: Optional[str] = Field(None, max_length=2000)
    tags: Optional[List[str]] = Field(None, max_items=10)

class MoodEntryResponse(BaseModel):
    """Mood entry response schema"""
    id: str
    entry_date: date
    mood_score: int
    stress_level: int
    energy_level: int
    sleep_hours: Optional[float]
    sleep_quality: Optional[int]
    exercise_minutes: Optional[int]
    activities: Optional[List[str]]
    symptoms: Optional[List[str]]
    triggers: Optional[List[str]]
    coping_strategies: Optional[List[str]]
    notes: Optional[str]
    wellness_score: float
    ai_recommendations: Optional[List[str]]
    ai_mood_analysis: Optional[Dict[str, Any]]
    created_at: datetime

# =============================================================================
# Dream Entry Schemas
# =============================================================================

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
    date: date = Field(default_factory=date.today, description="Dream date")
    dream_type: DreamType = Field(DreamType.NORMAL, description="Type of dream")
    title: Optional[str] = Field(None, max_length=200, description="Dream title")
    description: str = Field(..., min_length=10, max_length=5000, description="Dream description")
    
    vividness: Optional[int] = Field(None, ge=1, le=10, description="Dream vividness (1-10)")
    emotional_intensity: Optional[int] = Field(None, ge=1, le=10, description="Emotional intensity (1-10)")
    mood_during_dream: Optional[List[MoodLevel]] = Field(None, max_items=5, description="Emotions in dream")
    mood_after_waking: MoodLevel = Field(..., description="Mood after waking (1-10)")
    
    people_in_dream: Optional[List[str]] = Field(None, max_items=20, description="People in dream")
    locations: Optional[List[str]] = Field(None, max_items=10, description="Dream locations")
    objects: Optional[List[str]] = Field(None, max_items=15, description="Important objects")
    colors: Optional[List[str]] = Field(None, max_items=10, description="Prominent colors")
    symbols: Optional[List[str]] = Field(None, max_items=15, description="Dream symbols")
    emotions_felt: Optional[List[str]] = Field(None, max_items=10, description="Emotions felt")
    physical_sensations: Optional[List[str]] = Field(None, max_items=10, description="Physical sensations")
    
    sleep_quality: Optional[int] = Field(None, ge=1, le=10, description="Sleep quality")
    time_to_sleep: Optional[str] = Field(None, description="Time went to sleep (HH:MM)")
    wake_up_time: Optional[str] = Field(None, description="Wake up time (HH:MM)")
    sleep_duration: Optional[float] = Field(None, ge=0, le=24, description="Hours slept")
    
    became_lucid: bool = Field(False, description="Did you become lucid?")
    lucidity_trigger: Optional[str] = Field(None, max_length=200, description="What made you realize it was a dream")
    lucid_actions: Optional[List[str]] = Field(None, max_items=10, description="Actions taken when lucid")
    lucid_control_level: Optional[int] = Field(None, ge=1, le=10, description="Level of control when lucid")
    
    personal_interpretation: Optional[str] = Field(None, max_length=2000, description="Your interpretation")
    life_connection: Optional[str] = Field(None, max_length=1000, description="Connection to real life")
    recurring_elements: Optional[List[str]] = Field(None, max_items=10, description="Elements from other dreams")
    
    dream_recall_clarity: Optional[int] = Field(None, ge=1, le=10, description="How clearly remembered")
    entry_delay_hours: Optional[int] = Field(None, ge=0, le=168, description="Hours between dream and entry")
    
    is_private: bool = Field(True, description="Is entry private?")
    tags: Optional[List[str]] = Field(None, max_items=10, description="User tags")
    
    @validator('time_to_sleep', 'wake_up_time')
    def validate_time_format(cls, v):
        """Validate time format"""
        if v and not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', v):
            raise ValueError('Time must be in HH:MM format')
        return v

class DreamEntryUpdate(BaseModel):
    """Update dream entry schema"""
    dream_type: Optional[DreamType] = None
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=5000)
    vividness: Optional[int] = Field(None, ge=1, le=10)
    symbols: Optional[List[str]] = Field(None, max_items=15)
    emotions_felt: Optional[List[str]] = Field(None, max_items=10)
    personal_interpretation: Optional[str] = Field(None, max_length=2000)
    life_connection: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = Field(None, max_items=10)

class DreamEntryResponse(BaseModel):
    """Dream entry response schema"""
    id: str
    dream_date: date
    dream_type: DreamType
    title: Optional[str]
    description: str
    vividness: Optional[int]
    emotional_intensity: Optional[int]
    mood_after_waking: int
    became_lucid: bool
    people_in_dream: Optional[List[str]]
    locations: Optional[List[str]]
    symbols: Optional[List[str]]
    emotions_felt: Optional[List[str]]
    personal_interpretation: Optional[str]
    ai_dream_analysis: Optional[str]
    symbol_interpretations: Optional[Dict[str, str]]
    emotional_insights: Optional[List[str]]
    dream_quality_score: float
    created_at: datetime

# =============================================================================
# Therapy Note Schemas
# =============================================================================

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
    date: date = Field(default_factory=date.today, description="Note date")
    note_type: TherapyNoteType = Field(TherapyNoteType.SELF_REFLECTION, description="Type of note")
    title: str = Field(..., min_length=1, max_length=200, description="Note title")
    content: str = Field(..., min_length=10, max_length=10000, description="Note content")
    
    session_number: Optional[int] = Field(None, ge=1, description="Session number")
    therapist_name: Optional[str] = Field(None, max_length=200, description="Therapist name")
    session_duration: Optional[int] = Field(None, ge=1, le=480, description="Session duration in minutes")
    session_format: Optional[str] = Field(None, description="in_person, video, phone")
    
    techniques_used: Optional[List[TherapyTechnique]] = Field(None, max_items=10, description="Techniques used")
    homework_assigned: Optional[List[str]] = Field(None, max_items=10, description="Homework assigned")
    homework_completed: Optional[List[str]] = Field(None, max_items=10, description="Homework completed")
    
    goals_discussed: Optional[List[str]] = Field(None, max_items=10, description="Goals discussed")
    goals_achieved: Optional[List[str]] = Field(None, max_items=10, description="Goals achieved")
    progress_made: Optional[str] = Field(None, max_length=1000, description="Progress made")
    challenges_faced: Optional[List[str]] = Field(None, max_items=10, description="Challenges faced")
    
    mood_before_session: Optional[MoodLevel] = Field(None, description="Mood before session")
    mood_after_session: Optional[MoodLevel] = Field(None, description="Mood after session")
    anxiety_level: Optional[int] = Field(None, ge=1, le=10, description="Anxiety level")
    key_emotions: Optional[List[str]] = Field(None, max_items=10, description="Key emotions")
    
    key_insights: Optional[str] = Field(None, max_length=2000, description="Key insights")
    breakthrough_moments: Optional[List[str]] = Field(None, max_items=5, description="Breakthrough moments")
    patterns_recognized: Optional[List[str]] = Field(None, max_items=10, description="Patterns recognized")
    
    action_items: Optional[List[str]] = Field(None, max_items=10, description="Action items")
    next_session_focus: Optional[List[str]] = Field(None, max_items=5, description="Next session focus")
    
    medications_discussed: Optional[List[str]] = Field(None, max_items=10, description="Medications discussed")
    medication_changes: Optional[str] = Field(None, max_length=500, description="Medication changes")
    side_effects_noted: Optional[List[str]] = Field(None, max_items=10, description="Side effects noted")
    
    safety_plan_updated: bool = Field(False, description="Was safety plan updated?")
    crisis_triggers_identified: Optional[List[str]] = Field(None, max_items=10, description="Crisis triggers")
    coping_strategies_practiced: Optional[List[str]] = Field(None, max_items=10, description="Coping strategies")
    
    is_private: bool = Field(True, description="Is note private?")
    share_with_therapist: bool = Field(False, description="Share with therapist?")
    therapist_can_comment: bool = Field(False, description="Can therapist comment?")
    tags: Optional[List[str]] = Field(None, max_items=10, description="User tags")

class TherapyNoteUpdate(BaseModel):
    """Update therapy note schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=10, max_length=10000)
    techniques_used: Optional[List[TherapyTechnique]] = Field(None, max_items=10)
    goals_discussed: Optional[List[str]] = Field(None, max_items=10)
    progress_made: Optional[str] = Field(None, max_length=1000)
    key_insights: Optional[str] = Field(None, max_length=2000)
    action_items: Optional[List[str]] = Field(None, max_items=10)
    share_with_therapist: Optional[bool] = None
    tags: Optional[List[str]] = Field(None, max_items=10)

class TherapyNoteResponse(BaseModel):
    """Therapy note response schema"""
    id: str
    note_date: date
    note_type: TherapyNoteType
    title: str
    content: str
    session_number: Optional[int]
    therapist_name: Optional[str]
    techniques_used: Optional[List[str]]
    goals_discussed: Optional[List[str]]
    progress_made: Optional[str]
    mood_before_session: Optional[int]
    mood_after_session: Optional[int]
    mood_improvement: int
    key_insights: Optional[str]
    action_items: Optional[List[str]]
    ai_insights: Optional[str]
    progress_analysis: Optional[Dict[str, Any]]
    suggested_next_steps: Optional[List[str]]
    session_effectiveness: float
    is_private: bool
    share_with_therapist: bool
    created_at: datetime

# =============================================================================
# Sharing Schemas
# =============================================================================

class SharePermission(str, Enum):
    """Share permission levels"""
    READ_ONLY = "read_only"
    READ_COMMENT = "read_comment"
    COLLABORATIVE = "collaborative"

class ShareKeyCreate(BaseModel):
    """Create share key schema"""
    therapist_email: EmailStr = Field(..., description="Therapist email address")
    permission_level: SharePermission = Field(SharePermission.READ_ONLY, description="Permission level")
    include_mood_entries: bool = Field(True, description="Include mood entries?")
    include_dream_entries: bool = Field(False, description="Include dream entries?")
    include_therapy_notes: bool = Field(True, description="Include therapy notes?")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")
    max_sessions: Optional[int] = Field(None, ge=1, le=1000, description="Maximum sessions")
    notes: Optional[str] = Field(None, max_length=1000, description="Notes about sharing")
    
    # Advanced options
    date_range_start: Optional[datetime] = Field(None, description="Only share data after this date")
    date_range_end: Optional[datetime] = Field(None, description="Only share data before this date")
    exclude_tags: Optional[List[str]] = Field(None, max_items=10, description="Exclude entries with these tags")
    emergency_contact: bool = Field(False, description="Is this therapist an emergency contact?")
    crisis_access: bool = Field(False, description="Can access during crisis situations?")

class TherapistAccessRequest(BaseModel):
    """Therapist access request schema"""
    share_key: str = Field(..., min_length=10, description="Share key from patient")
    message: Optional[str] = Field(None, max_length=500, description="Message to patient")

class ShareKeyResponse(BaseModel):
    """Share key response schema"""
    id: str
    share_key: str
    therapist_email: str
    permission_level: SharePermission
    status: str
    created_at: datetime
    expires_at: Optional[datetime]
    max_sessions: Optional[int]
    access_count: int
    last_accessed: Optional[datetime]
    data_permissions: Dict[str, bool]
    limits: Dict[str, Any]
    instructions: Dict[str, List[str]]

class PatientOverview(BaseModel):
    """Patient overview for therapists"""
    patient_id: str
    patient_name: str
    permission_level: str
    shared_since: datetime
    last_accessed: Optional[datetime]
    access_count: int
    data_access: Dict[str, bool]
    summary_stats: Dict[str, Any]
    expires_at: Optional[datetime]

# =============================================================================
# Common Response Schemas
# =============================================================================

class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    """Generic error response"""
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None
    code: Optional[str] = None

class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    sort_by: str = Field("created_at", description="Sort by field")
    sort_order: str = Field("desc", regex="^(asc|desc)$", description="Sort order")

class PaginatedResponse(BaseModel):
    """Paginated response"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

# =============================================================================
# Analytics & Statistics Schemas
# =============================================================================

class AnalyticsRequest(BaseModel):
    """Analytics request schema"""
    start_date: Optional[date] = Field(None, description="Start date for analysis")
    end_date: Optional[date] = Field(None, description="End date for analysis")
    metric_types: Optional[List[str]] = Field(None, description="Types of metrics to include")
    include_ai_insights: bool = Field(True, description="Include AI-generated insights")

class MoodAnalyticsResponse(BaseModel):
    """Mood analytics response schema"""
    period_summary: Dict[str, Any]
    trend_analysis: Dict[str, Any]
    pattern_insights: List[str]
    recommendations: List[str]
    mood_distribution: Dict[str, int]
    correlations: Dict[str, float]
    ai_insights: Optional[str]

class DreamAnalyticsResponse(BaseModel):
    """Dream analytics response schema"""
    dream_frequency: Dict[str, int]
    common_symbols: Dict[str, int]
    dream_types: Dict[str, int]
    lucid_dream_rate: float
    mood_correlation: float
    recurring_themes: List[str]
    ai_pattern_analysis: Optional[str]

class TherapyProgressResponse(BaseModel):
    """Therapy progress response schema"""
    progress_metrics: Dict[str, Any]
    goal_completion_rate: float
    mood_improvement_trend: str
    technique_effectiveness: Dict[str, float]
    session_insights: List[str]
    recommendations: List[str]
    ai_progress_analysis: Optional[str]

# =============================================================================
# Export Schemas
# =============================================================================

class DataExportRequest(BaseModel):
    """Data export request schema"""
    include_mood_entries: bool = Field(True, description="Include mood entries")
    include_dream_entries: bool = Field(True, description="Include dream entries")
    include_therapy_notes: bool = Field(True, description="Include therapy notes")
    include_sharing_data: bool = Field(True, description="Include sharing data")
    include_ai_data: bool = Field(True, description="Include AI-generated data")
    date_range_start: Optional[date] = Field(None, description="Export data from this date")
    date_range_end: Optional[date] = Field(None, description="Export data until this date")
    format: str = Field("json", regex="^(json|csv)$", description="Export format")

class DataExportResponse(BaseModel):
    """Data export response schema"""
    export_id: str
    generated_at: datetime
    user_id: str
    export_type: str
    data_format: str
    gdpr_compliant: bool
    user_profile: Dict[str, Any]
    content_data: Dict[str, Any]
    sharing_data: Dict[str, Any]
    activity_data: Dict[str, Any]
    data_summary: Dict[str, Any]
    legal_information: Dict[str, Any]
