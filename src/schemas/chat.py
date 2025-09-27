"""
Chat Schemas

Pydantic Schemas für AI Chat System und Conversation Management.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

# =============================================================================
# Chat Session Schemas
# =============================================================================

class SessionType(str, Enum):
    """Chat session type enumeration"""
    GENERAL_SUPPORT = "general_support"
    CRISIS_SUPPORT = "crisis_support"
    MOOD_TRACKING = "mood_tracking"
    ANXIETY_SUPPORT = "anxiety_support"
    DEPRESSION_SUPPORT = "depression_support"
    THERAPY_SESSION = "therapy_session"
    CHECK_IN = "check_in"
    GUIDED_REFLECTION = "guided_reflection"

class TherapeuticApproach(str, Enum):
    """Therapeutic approach enumeration"""
    PERSON_CENTERED = "person_centered"
    CBT = "cbt"
    DBT = "dbt"
    MINDFULNESS = "mindfulness"
    SOLUTION_FOCUSED = "solution_focused"
    NARRATIVE = "narrative"
    ACCEPTANCE_COMMITMENT = "acceptance_commitment"

class SessionStatus(str, Enum):
    """Session status enumeration"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    TERMINATED = "terminated"

class CrisisLevel(str, Enum):
    """Crisis level enumeration"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    SEVERE = "severe"

class ChatSessionCreate(BaseModel):
    """Create chat session schema"""
    session_type: SessionType = Field(SessionType.GENERAL_SUPPORT, description="Type of chat session")
    session_title: Optional[str] = Field(None, max_length=200, description="Optional session title")
    session_goals: Optional[List[str]] = Field(None, max_items=5, description="Session goals")
    therapeutic_approach: Optional[TherapeuticApproach] = Field(None, description="Preferred therapeutic approach")
    language: str = Field("de", description="Session language")
    initial_mood: Optional[int] = Field(None, ge=1, le=10, description="Initial mood (1-10)")
    context_data: Optional[Dict[str, Any]] = Field(None, description="Additional context from previous entries")
    
    @validator('session_goals')
    def validate_goals(cls, v):
        """Validate session goals"""
        if v:
            for goal in v:
                if len(goal.strip()) < 3:
                    raise ValueError('Goals must be at least 3 characters long')
        return v

class ChatSessionResponse(BaseModel):
    """Chat session response schema"""
    id: str
    session_type: SessionType
    status: SessionStatus
    started_at: datetime
    ended_at: Optional[datetime] = None
    initial_mood: Optional[int] = None
    final_mood: Optional[int] = None
    message_count: int
    ai_model_version: str
    session_goals: Optional[List[str]] = None
    session_summary: Optional[Dict[str, Any]] = None
    initial_ai_message: Optional[str] = None
    crisis_detected: bool = False
    crisis_level: Optional[CrisisLevel] = None

class ChatSessionSummary(BaseModel):
    """Chat session summary schema"""
    session_id: str
    duration_minutes: Optional[float]
    message_count: int
    mood_change: Optional[int] = None
    key_insights: List[str]
    goals_addressed: List[str]
    crisis_episodes: int
    therapeutic_effectiveness: float
    follow_up_recommendations: List[str]
    completed_at: datetime

# =============================================================================
# Chat Message Schemas
# =============================================================================

class MessageType(str, Enum):
    """Message type enumeration"""
    CHAT = "chat"
    GREETING = "greeting"
    RESPONSE = "response"
    SYSTEM = "system"
    CRISIS = "crisis"
    CHECK_IN = "check_in"

class SenderType(str, Enum):
    """Sender type enumeration"""
    USER = "user"
    AI = "ai"
    SYSTEM = "system"

class UrgencyLevel(str, Enum):
    """Message urgency level"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TherapeuticIntent(str, Enum):
    """AI therapeutic intent enumeration"""
    SUPPORT = "support"
    CLARIFY = "clarify"
    VALIDATE = "validate"
    CHALLENGE = "challenge"
    EDUCATE = "educate"
    CRISIS_INTERVENTION = "crisis_intervention"
    RAPPORT_BUILDING = "rapport_building"
    GOAL_SETTING = "goal_setting"
    REFLECTION = "reflection"
    CLOSURE = "closure"

class ChatMessage(BaseModel):
    """Chat message input schema"""
    content: str = Field(..., min_length=1, max_length=5000, description="Message content")
    message_type: Optional[MessageType] = Field(MessageType.CHAT, description="Type of message")
    mood_indicator: Optional[int] = Field(None, ge=1, le=10, description="User's current mood")
    urgency_level: Optional[UrgencyLevel] = Field(None, description="Message urgency")
    emotional_state: Optional[List[str]] = Field(None, max_items=5, description="Current emotions")
    
    @validator('content')
    def validate_content(cls, v):
        """Validate message content"""
        content = v.strip()
        if len(content) < 1:
            raise ValueError('Message content cannot be empty')
        return content
    
    @validator('emotional_state')
    def validate_emotions(cls, v):
        """Validate emotional state"""
        if v:
            valid_emotions = [
                "happy", "sad", "angry", "anxious", "excited", "frustrated", "calm",
                "worried", "content", "overwhelmed", "hopeful", "defeated", "grateful",
                "lonely", "confident", "confused", "peaceful", "stressed", "motivated"
            ]
            for emotion in v:
                if emotion.lower() not in valid_emotions:
                    raise ValueError(f'Invalid emotion: {emotion}')
        return v

class ChatMessageResponse(BaseModel):
    """Chat message response schema"""
    id: str
    session_id: str
    sender_type: SenderType
    timestamp: datetime
    
    # User message fields
    user_message: Optional[str] = None
    mood_indicator: Optional[int] = None
    urgency_level: Optional[UrgencyLevel] = None
    
    # AI response fields
    ai_response: Optional[str] = None
    therapeutic_intent: Optional[TherapeuticIntent] = None
    ai_confidence: Optional[float] = None
    empathy_score: Optional[float] = None
    
    # Crisis detection
    crisis_detected: bool = False
    crisis_level: Optional[CrisisLevel] = None
    
    # Recommendations and suggestions
    follow_up_suggestions: Optional[List[str]] = None
    recommended_actions: Optional[List[str]] = None
    resource_suggestions: Optional[List[str]] = None

class StreamingChatResponse(BaseModel):
    """Streaming chat response schema"""
    chunk_id: str
    session_id: str
    chunk_type: str  # "text", "complete", "error"
    content: str
    is_final: bool = False
    crisis_detected: Optional[bool] = None
    timestamp: datetime

# =============================================================================
# Chat Analysis Schemas
# =============================================================================

class AnalysisType(str, Enum):
    """Analysis type enumeration"""
    SENTIMENT = "sentiment"
    TOPIC = "topic"
    PROGRESS = "progress"
    CRISIS = "crisis"
    EFFECTIVENESS = "effectiveness"
    COMPREHENSIVE = "comprehensive"

class ChatAnalysisRequest(BaseModel):
    """Chat analysis request schema"""
    analysis_type: AnalysisType = Field(AnalysisType.COMPREHENSIVE, description="Type of analysis")
    include_sentiment: bool = Field(True, description="Include sentiment analysis")
    include_topic_analysis: bool = Field(True, description="Include topic analysis")
    include_progress_tracking: bool = Field(True, description="Include progress tracking")
    include_crisis_assessment: bool = Field(True, description="Include crisis assessment")
    analysis_scope: str = Field("full_session", description="Scope of analysis")
    custom_date_range: Optional[Dict[str, datetime]] = Field(None, description="Custom date range")

class ChatAnalysisResponse(BaseModel):
    """Chat analysis response schema"""
    session_id: str
    analysis_type: AnalysisType
    overall_sentiment: Optional[float] = None  # -1 to 1
    mood_progression: List[Dict[str, Any]] = []
    key_topics: List[str] = []
    conversation_themes: List[str] = []
    therapeutic_insights: List[str] = []
    crisis_indicators: List[str] = []
    progress_indicators: Dict[str, Any] = {}
    recommendations: List[str] = []
    session_effectiveness: float
    confidence_score: float
    analyzed_at: datetime

# =============================================================================
# Crisis Detection Schemas
# =============================================================================

class CrisisDetectionResponse(BaseModel):
    """Crisis detection response schema"""
    session_id: str
    crisis_detected: bool
    crisis_level: CrisisLevel
    confidence_score: float
    risk_factors: List[str]
    protective_factors: Optional[List[str]] = None
    immediate_recommendations: List[str]
    professional_help_suggested: bool = False
    emergency_resources: Optional[List[Dict[str, str]]] = None
    assessment_timestamp: datetime
    intervention_triggered: Optional[str] = None

class EmergencyResource(BaseModel):
    """Emergency resource schema"""
    name: str
    type: str  # hotline, emergency, professional
    phone: Optional[str] = None
    website: Optional[str] = None
    description: str
    availability: str  # 24/7, business_hours, etc.
    language: str = "de"

# =============================================================================
# Chat Templates Schemas
# =============================================================================

class TemplateType(str, Enum):
    """Chat template type enumeration"""
    GREETING = "greeting"
    CRISIS = "crisis"
    CLOSURE = "closure"
    CHECK_IN = "check_in"
    VALIDATION = "validation"
    CLARIFICATION = "clarification"
    ENCOURAGEMENT = "encouragement"
    RESOURCE_SHARING = "resource_sharing"

class ChatTemplateCreate(BaseModel):
    """Create chat template schema"""
    template_name: str = Field(..., min_length=3, max_length=100)
    template_type: TemplateType
    template_text: str = Field(..., min_length=10, max_length=2000)
    therapeutic_intent: TherapeuticIntent
    variables: Optional[List[str]] = Field(None, max_items=10)
    conditions: Optional[Dict[str, Any]] = Field(None)
    emotional_tone: str = Field("empathetic")
    session_type: Optional[SessionType] = None
    crisis_level: Optional[CrisisLevel] = None

class ChatTemplateResponse(BaseModel):
    """Chat template response schema"""
    id: str
    template_name: str
    template_type: TemplateType
    template_text: str
    therapeutic_intent: TherapeuticIntent
    variables: Optional[List[str]]
    usage_count: int
    effectiveness_score: Optional[float]
    is_active: bool
    created_at: datetime

# =============================================================================
# Conversation Flow Schemas
# =============================================================================

class FlowType(str, Enum):
    """Conversation flow type enumeration"""
    GUIDED_THERAPY = "guided_therapy"
    CRISIS_INTERVENTION = "crisis_intervention"
    MOOD_CHECK_IN = "mood_check_in"
    ANXIETY_SUPPORT = "anxiety_support"
    DEPRESSION_SUPPORT = "depression_support"
    COPING_SKILLS = "coping_skills"
    GOAL_SETTING = "goal_setting"
    REFLECTION = "reflection"

class ConversationFlowCreate(BaseModel):
    """Create conversation flow schema"""
    flow_name: str = Field(..., min_length=3, max_length=100)
    flow_type: FlowType
    description: str = Field(..., min_length=10, max_length=1000)
    flow_steps: List[Dict[str, Any]] = Field(..., min_items=1, max_items=20)
    decision_trees: Optional[Dict[str, Any]] = Field(None)
    session_types: Optional[List[SessionType]] = Field(None)
    therapeutic_approaches: Optional[List[TherapeuticApproach]] = Field(None)
    estimated_duration_minutes: Optional[int] = Field(None, ge=5, le=120)

class ConversationFlowResponse(BaseModel):
    """Conversation flow response schema"""
    id: str
    flow_name: str
    flow_type: FlowType
    description: str
    estimated_duration_minutes: Optional[int]
    completion_rate: Optional[float]
    effectiveness_score: Optional[float]
    usage_count: int
    is_active: bool
    created_at: datetime

# =============================================================================
# Chat Training Data Schemas
# =============================================================================

class ChatTrainingPair(BaseModel):
    """Chat training data pair schema"""
    user_input: str = Field(..., min_length=1, max_length=5000)
    ai_response: str = Field(..., min_length=1, max_length=5000)
    context: Optional[Dict[str, Any]] = Field(None, description="Conversation context")
    therapeutic_intent: Optional[TherapeuticIntent] = Field(None)
    emotional_tone: Optional[str] = Field(None)
    crisis_level: Optional[CrisisLevel] = Field(None)
    safety_rating: int = Field(..., ge=1, le=5, description="Safety rating (1=unsafe, 5=very safe)")
    empathy_rating: int = Field(..., ge=1, le=5, description="Empathy rating (1=low, 5=very empathetic)")
    therapeutic_quality: int = Field(..., ge=1, le=5, description="Therapeutic quality (1=poor, 5=excellent)")
    
    class Config:
        schema_extra = {
            "example": {
                "user_input": "Ich fühle mich heute sehr niedergeschlagen und weiß nicht warum. Alles scheint hoffnungslos.",
                "ai_response": "Es tut mir leid zu hören, dass du dich so fühlst. Niedergeschlagenheit kann sehr belastend sein, besonders wenn man den Grund nicht versteht. Das ist ein mutiger Schritt, dass du darüber sprichst. Manchmal können unsere Gefühle von vielen Faktoren beeinflusst werden - Stress, Schlafmangel, oder auch einfach natürliche emotionale Schwankungen. Magst du mir erzählen, wie dein Tag bisher verlaufen ist?",
                "therapeutic_intent": "validation",
                "emotional_tone": "empathetic",
                "crisis_level": "low",
                "safety_rating": 5,
                "empathy_rating": 5,
                "therapeutic_quality": 5,
                "context": {
                    "session_type": "depression_support",
                    "user_mood": 3,
                    "conversation_turn": 1
                }
            }
        }

class ChatTrainingDataCreate(BaseModel):
    """Create chat training dataset schema"""
    dataset_name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=10, max_length=1000)
    training_pairs: List[ChatTrainingPair] = Field(..., min_items=1, max_items=10000)
    dataset_type: str = Field("chat_conversation", description="Type of training data")
    therapeutic_focus: Optional[List[str]] = Field(None, description="Therapeutic focus areas")
    language: str = Field("de", description="Language of the dataset")
    quality_threshold: float = Field(4.0, ge=1.0, le=5.0, description="Minimum quality threshold")
    
    @validator('training_pairs')
    def validate_training_pairs(cls, v):
        """Validate training pairs quality"""
        if not v:
            raise ValueError('At least one training pair is required')
        
        low_quality_count = 0
        for pair in v:
            # Check overall quality
            avg_quality = (pair.safety_rating + pair.empathy_rating + pair.therapeutic_quality) / 3
            if avg_quality < 3.0:
                low_quality_count += 1
        
        if low_quality_count > len(v) * 0.1:  # More than 10% low quality
            raise ValueError('Too many low quality training pairs. Please review and improve the data.')
        
        return v

class ChatTrainingDataResponse(BaseModel):
    """Chat training data response schema"""
    dataset_id: str
    dataset_name: str
    description: str
    total_pairs: int
    high_quality_pairs: int
    average_safety_rating: float
    average_empathy_rating: float
    average_therapeutic_quality: float
    therapeutic_focus: Optional[List[str]]
    language: str
    created_at: datetime
    processing_status: str

# =============================================================================
# Chat Model Training Schemas
# =============================================================================

class ChatModelTrainingRequest(BaseModel):
    """Chat model training request schema"""
    model_name: str = Field(..., min_length=3, max_length=100)
    base_model: str = Field("chat_therapist_base", description="Base model to fine-tune")
    training_datasets: List[str] = Field(..., min_items=1, description="Training dataset IDs")
    
    # Training configuration
    training_config: Optional[Dict[str, Any]] = Field(
        default={
            "epochs": 3,
            "batch_size": 4,
            "learning_rate": 5e-5,
            "warmup_steps": 100,
            "max_sequence_length": 512,
            "gradient_accumulation_steps": 4
        },
        description="Training configuration"
    )
    
    # Model-specific settings
    safety_weight: float = Field(0.2, ge=0.0, le=1.0, description="Weight for safety loss")
    empathy_weight: float = Field(0.1, ge=0.0, le=1.0, description="Weight for empathy loss")
    therapeutic_weight: float = Field(0.1, ge=0.0, le=1.0, description="Weight for therapeutic quality loss")
    
    # Validation settings
    validation_split: float = Field(0.1, ge=0.05, le=0.3, description="Validation split ratio")
    early_stopping: bool = Field(True, description="Enable early stopping")
    save_best_model: bool = Field(True, description="Save best performing model")

class ChatModelTrainingResponse(BaseModel):
    """Chat model training response schema"""
    training_job_id: str
    model_name: str
    status: str
    training_datasets: List[str]
    estimated_duration_hours: Optional[float]
    started_at: Optional[datetime]
    progress_percentage: float = 0.0
    current_epoch: Optional[int] = None
    current_metrics: Optional[Dict[str, float]] = None

class ChatModelEvaluationRequest(BaseModel):
    """Chat model evaluation request schema"""
    model_id: str = Field(..., description="Model ID to evaluate")
    test_conversations: List[Dict[str, Any]] = Field(..., min_items=1, max_items=1000)
    evaluation_metrics: List[str] = Field(
        default=["safety", "empathy", "therapeutic_quality", "coherence", "relevance"],
        description="Metrics to evaluate"
    )
    human_evaluation: bool = Field(False, description="Include human evaluation")

class ChatModelEvaluationResponse(BaseModel):
    """Chat model evaluation response schema"""
    model_id: str
    evaluation_id: str
    overall_score: float
    safety_score: float
    empathy_score: float
    therapeutic_quality_score: float
    coherence_score: float
    relevance_score: float
    detailed_metrics: Dict[str, Any]
    sample_conversations: List[Dict[str, Any]]
    recommendations: List[str]
    evaluated_at: datetime

# =============================================================================
# Chat Analytics Schemas
# =============================================================================

class ChatAnalyticsRequest(BaseModel):
    """Chat analytics request schema"""
    start_date: Optional[datetime] = Field(None, description="Start date for analytics")
    end_date: Optional[datetime] = Field(None, description="End date for analytics")
    session_types: Optional[List[SessionType]] = Field(None, description="Filter by session types")
    include_model_performance: bool = Field(True, description="Include model performance metrics")
    include_user_satisfaction: bool = Field(True, description="Include user satisfaction data")
    include_crisis_analytics: bool = Field(True, description="Include crisis detection analytics")

class ChatAnalyticsResponse(BaseModel):
    """Chat analytics response schema"""
    total_sessions: int
    total_messages: int
    average_session_duration: float
    session_completion_rate: float
    crisis_detection_rate: float
    user_satisfaction_average: float
    model_performance_metrics: Dict[str, float]
    popular_session_types: List[Dict[str, Any]]
    therapeutic_effectiveness: Dict[str, float]
    improvement_suggestions: List[str]
    generated_at: datetime

# =============================================================================
# Export and Sharing Schemas
# =============================================================================

class ChatDataExportRequest(BaseModel):
    """Chat data export request schema"""
    session_ids: Optional[List[str]] = Field(None, description="Specific session IDs to export")
    include_ai_responses: bool = Field(True, description="Include AI responses")
    include_analysis: bool = Field(True, description="Include session analysis")
    anonymize_data: bool = Field(True, description="Anonymize personal data")
    export_format: str = Field("json", regex="^(json|csv|pdf)$", description="Export format")
    date_range_start: Optional[datetime] = Field(None, description="Start date for export")
    date_range_end: Optional[datetime] = Field(None, description="End date for export")

class ChatDataExportResponse(BaseModel):
    """Chat data export response schema"""
    export_id: str
    export_status: str
    file_url: Optional[str] = None
    file_size_mb: Optional[float] = None
    sessions_exported: int
    messages_exported: int
    export_format: str
    anonymized: bool
    expires_at: datetime
    created_at: datetime

# =============================================================================
# Settings and Preferences Schemas
# =============================================================================

class ChatPreferences(BaseModel):
    """User chat preferences schema"""
    preferred_therapeutic_approach: Optional[TherapeuticApproach] = None
    communication_style: str = Field("balanced", regex="^(formal|casual|balanced)$")
    crisis_detection_sensitivity: str = Field("medium", regex="^(low|medium|high)$")
    response_length_preference: str = Field("medium", regex="^(short|medium|long)$")
    topics_to_avoid: Optional[List[str]] = Field(None, max_items=10)
    emergency_contacts: Optional[List[Dict[str, str]]] = Field(None, max_items=5)
    notification_preferences: Dict[str, bool] = Field(default_factory=dict)

class ChatSettingsUpdate(BaseModel):
    """Update chat settings schema"""
    preferences: Optional[ChatPreferences] = None
    auto_save_conversations: bool = Field(True)
    share_data_for_research: bool = Field(False)
    enable_crisis_detection: bool = Field(True)
    session_timeout_minutes: int = Field(30, ge=5, le=180)
