"""
Content Models

Datenbank-Modelle für Benutzer-Inhalte: Mood, Dreams, Therapy Notes.
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, Integer, Float, Date
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from src.core.database import Base

# =============================================================================
# Mood Entry Models
# =============================================================================

class MoodLevel(enum.Enum):
    """Mood level enumeration (1-10 scale)"""
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

class MoodEntry(Base):
    """Mood tracking entries"""
    
    __tablename__ = "mood_entries"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Entry details
    entry_date = Column(Date, nullable=False, index=True)
    mood_score = Column(Integer, nullable=False)  # 1-10 scale
    stress_level = Column(Integer, nullable=False)  # 1-10 scale
    energy_level = Column(Integer, nullable=False)  # 1-10 scale
    
    # Sleep data
    sleep_hours = Column(Float, nullable=True)  # Hours of sleep
    sleep_quality = Column(Integer, nullable=True)  # 1-10 scale
    sleep_notes = Column(Text, nullable=True)
    
    # Physical health
    exercise_minutes = Column(Integer, nullable=True)
    exercise_type = Column(String(100), nullable=True)
    
    # Activities and context
    activities = Column(ARRAY(String), nullable=True)  # Activities done today
    location = Column(String(200), nullable=True)  # Where was the entry made
    weather = Column(String(50), nullable=True)  # Weather condition
    
    # Mental health specifics
    symptoms = Column(ARRAY(String), nullable=True)  # Anxiety, depression symptoms
    triggers = Column(ARRAY(String), nullable=True)  # What triggered mood changes
    coping_strategies = Column(ARRAY(String), nullable=True)  # What helped
    
    # Medication and treatment
    medication_taken = Column(Boolean, default=False)
    medication_names = Column(ARRAY(String), nullable=True)
    medication_effects = Column(Text, nullable=True)
    medication_notes = Column(Text, nullable=True)
    
    # Social and emotional context
    social_interactions = Column(Integer, nullable=True)  # Number of social interactions
    relationship_quality = Column(Integer, nullable=True)  # 1-10 scale
    work_stress = Column(Integer, nullable=True)  # 1-10 scale
    
    # Free text
    notes = Column(Text, nullable=True)
    gratitude = Column(Text, nullable=True)  # What are you grateful for?
    goals_achieved = Column(ARRAY(String), nullable=True)  # Goals completed today
    
    # AI-generated insights
    ai_mood_analysis = Column(JSON, nullable=True)  # AI analysis results
    ai_recommendations = Column(ARRAY(String), nullable=True)  # AI suggestions
    ai_sentiment_score = Column(Float, nullable=True)  # Sentiment analysis
    
    # Metadata
    entry_duration_seconds = Column(Integer, nullable=True)  # Time spent on entry
    is_private = Column(Boolean, default=True)  # Private vs shareable
    tags = Column(ARRAY(String), nullable=True)  # User-defined tags
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="mood_entries")
    
    def __repr__(self):
        return f"<MoodEntry(id={self.id}, user_id={self.user_id}, mood={self.mood_score}, date={self.entry_date})>"
    
    @property
    def mood_category(self) -> str:
        """Get mood category based on score"""
        if self.mood_score <= 3:
            return "low"
        elif self.mood_score <= 6:
            return "moderate"
        else:
            return "high"
    
    @property
    def stress_category(self) -> str:
        """Get stress category based on level"""
        if self.stress_level <= 3:
            return "low"
        elif self.stress_level <= 6:
            return "moderate"
        else:
            return "high"
    
    def calculate_wellness_score(self) -> float:
        """Calculate overall wellness score"""
        # Weighted average of mood, energy, sleep quality, and inverse stress
        mood_weight = 0.3
        energy_weight = 0.25
        sleep_weight = 0.25
        stress_weight = 0.2  # Inverted (10 - stress_level)
        
        sleep_score = self.sleep_quality if self.sleep_quality else 5
        stress_score = 11 - self.stress_level  # Invert stress (higher stress = lower wellness)
        
        wellness = (
            (self.mood_score * mood_weight) +
            (self.energy_level * energy_weight) +
            (sleep_score * sleep_weight) +
            (stress_score * stress_weight)
        )
        
        return round(wellness, 2)
    
    def to_dict(self, include_ai_data: bool = True) -> dict:
        """Convert to dictionary"""
        base_dict = {
            "id": str(self.id),
            "entry_date": self.entry_date.isoformat(),
            "mood_score": self.mood_score,
            "stress_level": self.stress_level,
            "energy_level": self.energy_level,
            "sleep_hours": self.sleep_hours,
            "sleep_quality": self.sleep_quality,
            "exercise_minutes": self.exercise_minutes,
            "activities": self.activities,
            "symptoms": self.symptoms,
            "triggers": self.triggers,
            "coping_strategies": self.coping_strategies,
            "notes": self.notes,
            "wellness_score": self.calculate_wellness_score(),
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        
        if include_ai_data:
            base_dict.update({
                "ai_mood_analysis": self.ai_mood_analysis,
                "ai_recommendations": self.ai_recommendations,
                "ai_sentiment_score": self.ai_sentiment_score
            })
        
        return base_dict

# =============================================================================
# Dream Entry Models
# =============================================================================

class DreamType(enum.Enum):
    """Dream type enumeration"""
    NORMAL = "normal"
    LUCID = "lucid"
    NIGHTMARE = "nightmare"
    RECURRING = "recurring"
    PROPHETIC = "prophetic"
    HEALING = "healing"
    ADVENTURE = "adventure"
    SYMBOLIC = "symbolic"

class DreamEntry(Base):
    """Dream journal entries"""
    
    __tablename__ = "dream_entries"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Dream details
    dream_date = Column(Date, nullable=False, index=True)
    dream_type = Column(String(20), nullable=False, default=DreamType.NORMAL.value)
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=False)
    
    # Dream characteristics
    vividness = Column(Integer, nullable=True)  # 1-10 how vivid
    emotional_intensity = Column(Integer, nullable=True)  # 1-10 emotional impact
    mood_during_dream = Column(ARRAY(String), nullable=True)  # Emotions felt in dream
    mood_after_waking = Column(Integer, nullable=False)  # 1-10 mood upon waking
    
    # Dream content
    people_in_dream = Column(ARRAY(String), nullable=True)  # People who appeared
    locations = Column(ARRAY(String), nullable=True)  # Dream locations
    objects = Column(ARRAY(String), nullable=True)  # Important objects
    colors = Column(ARRAY(String), nullable=True)  # Prominent colors
    symbols = Column(ARRAY(String), nullable=True)  # Symbolic elements
    
    # Emotions and feelings
    emotions_felt = Column(ARRAY(String), nullable=True)  # Emotions during dream
    physical_sensations = Column(ARRAY(String), nullable=True)  # Physical feelings
    
    # Sleep context
    sleep_quality = Column(Integer, nullable=True)  # 1-10 sleep quality
    time_to_sleep = Column(String(10), nullable=True)  # "22:30" format
    wake_up_time = Column(String(10), nullable=True)  # "07:15" format
    sleep_duration = Column(Float, nullable=True)  # Hours slept
    
    # Lucid dreaming
    became_lucid = Column(Boolean, default=False)
    lucidity_trigger = Column(String(200), nullable=True)  # What made you realize it was a dream
    lucid_actions = Column(ARRAY(String), nullable=True)  # What you did when lucid
    lucid_control_level = Column(Integer, nullable=True)  # 1-10 how much control
    
    # Personal interpretation
    personal_interpretation = Column(Text, nullable=True)
    life_connection = Column(Text, nullable=True)  # How it relates to real life
    recurring_elements = Column(ARRAY(String), nullable=True)  # Elements from other dreams
    
    # AI analysis
    ai_dream_analysis = Column(JSON, nullable=True)  # AI interpretation
    symbol_interpretations = Column(JSON, nullable=True)  # AI symbol meanings
    emotional_insights = Column(ARRAY(String), nullable=True)  # AI emotional analysis
    
    # Metadata
    dream_recall_clarity = Column(Integer, nullable=True)  # 1-10 how clearly remembered
    entry_delay_hours = Column(Integer, nullable=True)  # Hours between dream and entry
    is_private = Column(Boolean, default=True)
    tags = Column(ARRAY(String), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="dream_entries")
    
    def __repr__(self):
        return f"<DreamEntry(id={self.id}, user_id={self.user_id}, type={self.dream_type}, date={self.dream_date})>"
    
    @property
    def is_lucid(self) -> bool:
        """Check if dream was lucid"""
        return self.became_lucid or self.dream_type == DreamType.LUCID.value
    
    @property
    def is_nightmare(self) -> bool:
        """Check if dream was a nightmare"""
        return self.dream_type == DreamType.NIGHTMARE.value
    
    @property
    def emotional_impact_category(self) -> str:
        """Get emotional impact category"""
        if not self.emotional_intensity:
            return "unknown"
        elif self.emotional_intensity <= 3:
            return "low"
        elif self.emotional_intensity <= 6:
            return "moderate"
        else:
            return "high"
    
    def calculate_dream_quality_score(self) -> float:
        """Calculate overall dream experience quality"""
        factors = []
        
        if self.vividness:
            factors.append(self.vividness)
        if self.dream_recall_clarity:
            factors.append(self.dream_recall_clarity)
        if self.mood_after_waking:
            factors.append(self.mood_after_waking)
        if self.sleep_quality:
            factors.append(self.sleep_quality)
        
        return round(sum(factors) / len(factors), 2) if factors else 0
    
    def to_dict(self, include_ai_data: bool = True) -> dict:
        """Convert to dictionary"""
        base_dict = {
            "id": str(self.id),
            "dream_date": self.dream_date.isoformat(),
            "dream_type": self.dream_type,
            "title": self.title,
            "description": self.description,
            "vividness": self.vividness,
            "emotional_intensity": self.emotional_intensity,
            "mood_after_waking": self.mood_after_waking,
            "became_lucid": self.became_lucid,
            "people_in_dream": self.people_in_dream,
            "locations": self.locations,
            "symbols": self.symbols,
            "emotions_felt": self.emotions_felt,
            "personal_interpretation": self.personal_interpretation,
            "dream_quality_score": self.calculate_dream_quality_score(),
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        
        if include_ai_data:
            base_dict.update({
                "ai_dream_analysis": self.ai_dream_analysis,
                "symbol_interpretations": self.symbol_interpretations,
                "emotional_insights": self.emotional_insights
            })
        
        return base_dict

# =============================================================================
# Therapy Note Models
# =============================================================================

class TherapyNoteType(enum.Enum):
    """Therapy note type enumeration"""
    SESSION_NOTES = "session_notes"
    SELF_REFLECTION = "self_reflection"
    HOMEWORK = "homework"
    PROGRESS_UPDATE = "progress_update"
    CRISIS_NOTE = "crisis_note"
    MEDICATION_LOG = "medication_log"
    GOAL_SETTING = "goal_setting"
    BREAKTHROUGH = "breakthrough"

class TherapyTechnique(enum.Enum):
    """Therapy technique enumeration"""
    CBT = "cbt"  # Cognitive Behavioral Therapy
    DBT = "dbt"  # Dialectical Behavior Therapy
    MINDFULNESS = "mindfulness"
    EXPOSURE = "exposure"
    EMDR = "emdr"
    SOLUTION_FOCUSED = "solution_focused"
    PSYCHODYNAMIC = "psychodynamic"
    HUMANISTIC = "humanistic"
    ACCEPTANCE_COMMITMENT = "acceptance_commitment"
    INTERPERSONAL = "interpersonal"

class TherapyNote(Base):
    """Therapy and self-reflection notes"""
    
    __tablename__ = "therapy_notes"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Note details
    note_date = Column(Date, nullable=False, index=True)
    note_type = Column(String(30), nullable=False, default=TherapyNoteType.SELF_REFLECTION.value)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    
    # Session information (if applicable)
    session_number = Column(Integer, nullable=True)
    therapist_name = Column(String(200), nullable=True)  # If professional therapy
    session_duration = Column(Integer, nullable=True)  # Minutes
    session_format = Column(String(20), nullable=True)  # "in_person", "video", "phone"
    
    # Therapy techniques and methods
    techniques_used = Column(ARRAY(String), nullable=True)  # CBT, DBT, etc.
    homework_assigned = Column(ARRAY(String), nullable=True)
    homework_completed = Column(ARRAY(String), nullable=True)
    
    # Goals and progress
    goals_discussed = Column(ARRAY(String), nullable=True)
    goals_achieved = Column(ARRAY(String), nullable=True)
    progress_made = Column(Text, nullable=True)
    challenges_faced = Column(ARRAY(String), nullable=True)
    
    # Emotional state
    mood_before_session = Column(Integer, nullable=True)  # 1-10 scale
    mood_after_session = Column(Integer, nullable=True)  # 1-10 scale
    anxiety_level = Column(Integer, nullable=True)  # 1-10 scale
    key_emotions = Column(ARRAY(String), nullable=True)
    
    # Insights and breakthroughs
    key_insights = Column(Text, nullable=True)
    breakthrough_moments = Column(ARRAY(String), nullable=True)
    patterns_recognized = Column(ARRAY(String), nullable=True)
    
    # Action items and next steps
    action_items = Column(ARRAY(String), nullable=True)
    next_session_focus = Column(ARRAY(String), nullable=True)
    
    # Medication and treatment
    medications_discussed = Column(ARRAY(String), nullable=True)
    medication_changes = Column(Text, nullable=True)
    side_effects_noted = Column(ARRAY(String), nullable=True)
    
    # Crisis and safety
    safety_plan_updated = Column(Boolean, default=False)
    crisis_triggers_identified = Column(ARRAY(String), nullable=True)
    coping_strategies_practiced = Column(ARRAY(String), nullable=True)
    
    # AI analysis
    ai_insights = Column(JSON, nullable=True)  # AI-generated insights
    progress_analysis = Column(JSON, nullable=True)  # AI progress tracking
    suggested_techniques = Column(ARRAY(String), nullable=True)  # AI technique suggestions
    
    # Privacy and sharing
    is_private = Column(Boolean, default=True)
    share_with_therapist = Column(Boolean, default=False)  # If patient wants to share
    therapist_can_comment = Column(Boolean, default=False)
    
    # Metadata
    entry_duration_seconds = Column(Integer, nullable=True)
    structured_format = Column(JSON, nullable=True)  # For structured worksheets
    tags = Column(ARRAY(String), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="therapy_notes")
    
    def __repr__(self):
        return f"<TherapyNote(id={self.id}, user_id={self.user_id}, type={self.note_type}, date={self.note_date})>"
    
    @property
    def is_session_note(self) -> bool:
        """Check if this is a professional therapy session note"""
        return self.note_type == TherapyNoteType.SESSION_NOTES.value
    
    @property
    def is_self_reflection(self) -> bool:
        """Check if this is a self-reflection note"""
        return self.note_type == TherapyNoteType.SELF_REFLECTION.value
    
    @property
    def mood_improvement(self) -> int:
        """Calculate mood improvement during session"""
        if self.mood_before_session and self.mood_after_session:
            return self.mood_after_session - self.mood_before_session
        return 0
    
    @property
    def progress_category(self) -> str:
        """Categorize progress level"""
        mood_change = self.mood_improvement
        if mood_change >= 2:
            return "significant_progress"
        elif mood_change >= 1:
            return "moderate_progress"
        elif mood_change >= 0:
            return "stable"
        else:
            return "needs_attention"
    
    def calculate_session_effectiveness(self) -> float:
        """Calculate session effectiveness score"""
        factors = []
        
        # Mood improvement
        if self.mood_before_session and self.mood_after_session:
            mood_factor = (self.mood_after_session - self.mood_before_session + 10) / 2
            factors.append(mood_factor)
        
        # Goals achieved
        if self.goals_discussed and self.goals_achieved:
            goal_completion = len(self.goals_achieved) / len(self.goals_discussed)
            factors.append(goal_completion * 10)
        
        # Insights gained
        if self.key_insights:
            factors.append(8.0)  # High value for insights
        
        # Techniques used
        if self.techniques_used:
            factors.append(7.0)  # Value for structured approach
        
        return round(sum(factors) / len(factors), 2) if factors else 5.0
    
    def to_dict(self, include_ai_data: bool = True, include_private: bool = False) -> dict:
        """Convert to dictionary"""
        base_dict = {
            "id": str(self.id),
            "note_date": self.note_date.isoformat(),
            "note_type": self.note_type,
            "title": self.title,
            "content": self.content if include_private or not self.is_private else "[Private Content]",
            "techniques_used": self.techniques_used,
            "goals_discussed": self.goals_discussed,
            "progress_made": self.progress_made,
            "mood_before_session": self.mood_before_session,
            "mood_after_session": self.mood_after_session,
            "mood_improvement": self.mood_improvement,
            "key_insights": self.key_insights if include_private or not self.is_private else None,
            "session_effectiveness": self.calculate_session_effectiveness(),
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        
        if include_ai_data:
            base_dict.update({
                "ai_insights": self.ai_insights,
                "progress_analysis": self.progress_analysis,
                "suggested_techniques": self.suggested_techniques
            })
        
        return base_dict

# =============================================================================
# Indexes for Performance
# =============================================================================

from sqlalchemy import Index

# Mood entries indexes
Index('idx_mood_entries_user_date', MoodEntry.user_id, MoodEntry.entry_date)
Index('idx_mood_entries_date_score', MoodEntry.entry_date, MoodEntry.mood_score)
Index('idx_mood_entries_user_created', MoodEntry.user_id, MoodEntry.created_at)

# Dream entries indexes
Index('idx_dream_entries_user_date', DreamEntry.user_id, DreamEntry.dream_date)
Index('idx_dream_entries_type_date', DreamEntry.dream_type, DreamEntry.dream_date)
Index('idx_dream_entries_lucid', DreamEntry.became_lucid, DreamEntry.dream_date)

# Therapy notes indexes
Index('idx_therapy_notes_user_date', TherapyNote.user_id, TherapyNote.note_date)
Index('idx_therapy_notes_type_date', TherapyNote.note_type, TherapyNote.note_date)
Index('idx_therapy_notes_shareable', TherapyNote.share_with_therapist, TherapyNote.note_date)
