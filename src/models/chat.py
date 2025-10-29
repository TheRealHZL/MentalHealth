"""
Chat Models

SQLAlchemy Models für Chat Sessions und AI-powered Conversations.
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from src.core.database import Base

class ChatSession(Base):
    """Chat session model for AI conversations"""
    __tablename__ = "chat_sessions"
    
    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    
    # Session configuration
    session_type = Column(String(30), nullable=False, default="general_support")  # general, crisis, therapy, mood
    session_title = Column(String(200), nullable=True)
    session_goals = Column(ARRAY(String), nullable=True)
    therapeutic_approach = Column(String(50), nullable=True)  # person_centered, cbt, dbt, etc.
    language = Column(String(5), nullable=False, default="de")
    
    # Status and lifecycle
    status = Column(String(20), nullable=False, default="active", index=True)  # active, paused, completed, terminated
    is_active = Column(Boolean, default=True, nullable=False)
    started_at = Column(DateTime, default=func.now(), nullable=False)
    ended_at = Column(DateTime, nullable=True)
    last_activity = Column(DateTime, default=func.now(), nullable=False)
    
    # Context and mood tracking
    initial_mood = Column(Integer, nullable=True)  # 1-10 scale
    final_mood = Column(Integer, nullable=True)  # 1-10 scale
    mood_progression = Column(JSON, nullable=True)  # Array of mood changes throughout session
    context_data = Column(JSON, nullable=True)  # Additional context from previous entries
    
    # AI model information
    ai_model_version = Column(String(50), nullable=False, default="chat_therapist_v1.0")
    ai_personality = Column(String(30), nullable=False, default="empathetic_therapist")
    session_settings = Column(JSON, nullable=True)  # AI behavior settings
    
    # Session statistics
    message_count = Column(Integer, default=0, nullable=False)
    user_message_count = Column(Integer, default=0, nullable=False)
    ai_message_count = Column(Integer, default=0, nullable=False)
    average_response_time_ms = Column(Float, nullable=True)
    session_duration_minutes = Column(Float, nullable=True)
    
    # Crisis and safety tracking
    crisis_detected = Column(Boolean, default=False, nullable=False)
    crisis_level = Column(String(20), nullable=True)  # none, low, medium, high, severe
    crisis_interventions = Column(JSON, nullable=True)  # Array of interventions triggered
    safety_alerts_triggered = Column(Integer, default=0, nullable=False)
    
    # Quality and effectiveness
    session_effectiveness_score = Column(Float, nullable=True)  # 0-1 score
    user_satisfaction_rating = Column(Integer, nullable=True)  # 1-5 stars
    therapeutic_goals_achieved = Column(ARRAY(String), nullable=True)
    
    # Privacy and sharing
    is_private = Column(Boolean, default=True, nullable=False)
    can_be_shared = Column(Boolean, default=False, nullable=False)
    anonymized_for_research = Column(Boolean, default=False, nullable=False)
    
    # Session summary and insights
    session_summary = Column(JSON, nullable=True)  # Generated summary
    key_insights = Column(ARRAY(String), nullable=True)
    recommended_follow_ups = Column(ARRAY(String), nullable=True)
    
    # User feedback
    user_feedback = Column(Text, nullable=True)
    feedback_received_at = Column(DateTime, nullable=True)
    would_recommend = Column(Boolean, nullable=True)
    
    # Technical metadata
    session_metadata = Column(JSON, nullable=True)
    device_info = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    analyses = relationship("ChatAnalysis", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ChatSession(id={self.id}, user={self.user_id}, type={self.session_type}, status={self.status})>"

class ChatMessage(Base):
    """Individual chat messages within sessions"""
    __tablename__ = "chat_messages"
    
    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('chat_sessions.id'), nullable=False, index=True)
    
    # Message content
    message_content = Column(Text, nullable=False)
    message_type = Column(String(30), nullable=False, default="chat")  # chat, greeting, response, system, crisis
    sender_type = Column(String(10), nullable=False, index=True)  # user, ai, system
    
    # Message context
    conversation_turn = Column(Integer, nullable=False)  # Sequential turn number
    parent_message_id = Column(UUID(as_uuid=True), ForeignKey('chat_messages.id'), nullable=True)
    is_edited = Column(Boolean, default=False, nullable=False)
    edit_count = Column(Integer, default=0, nullable=False)
    
    # User message specifics
    mood_indicator = Column(Integer, nullable=True)  # User's mood when sending (1-10)
    urgency_level = Column(String(20), nullable=True)  # low, medium, high, critical
    emotional_state = Column(ARRAY(String), nullable=True)  # Array of emotions
    user_intent = Column(String(50), nullable=True)  # question, vent, seek_advice, crisis, etc.
    
    # AI message specifics
    ai_model_version = Column(String(50), nullable=True)
    ai_confidence = Column(Float, nullable=True)  # 0-1 confidence score
    ai_processing_time_ms = Column(Float, nullable=True)
    therapeutic_intent = Column(String(50), nullable=True)  # support, clarify, validate, challenge, etc.
    empathy_score = Column(Float, nullable=True)  # AI empathy rating
    
    # Safety and crisis detection
    crisis_detected = Column(Boolean, default=False, nullable=False)
    crisis_level = Column(String(20), nullable=True)  # none, low, medium, high, severe
    crisis_keywords = Column(ARRAY(String), nullable=True)
    safety_warning_triggered = Column(Boolean, default=False, nullable=False)
    intervention_triggered = Column(String(50), nullable=True)
    
    # Message analysis
    sentiment_score = Column(Float, nullable=True)  # -1 to 1 (negative to positive)
    emotion_classification = Column(JSON, nullable=True)  # Dict of emotions and scores
    topic_tags = Column(ARRAY(String), nullable=True)
    ai_analysis = Column(JSON, nullable=True)  # Detailed AI analysis of message
    
    # Quality and feedback
    message_quality_score = Column(Float, nullable=True)  # AI message quality (0-1)
    user_reaction = Column(String(20), nullable=True)  # helpful, unhelpful, neutral
    user_feedback = Column(Text, nullable=True)
    feedback_timestamp = Column(DateTime, nullable=True)
    
    # Technical details
    character_count = Column(Integer, nullable=False, default=0)
    word_count = Column(Integer, nullable=False, default=0)
    response_time_ms = Column(Float, nullable=True)  # Time to generate response
    
    # Privacy and flagging
    is_flagged = Column(Boolean, default=False, nullable=False)
    flag_reason = Column(String(100), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    
    # Timestamps
    sent_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    parent_message = relationship("ChatMessage", remote_side=[id])
    child_messages = relationship("ChatMessage", back_populates="parent_message")
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, session={self.session_id}, sender={self.sender_type}, type={self.message_type})>"

class ChatAnalysis(Base):
    """Analysis results for chat sessions"""
    __tablename__ = "chat_analyses"
    
    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('chat_sessions.id'), nullable=False, index=True)
    analysis_id = Column(String(100), nullable=False, unique=True)
    
    # Analysis configuration
    analysis_type = Column(String(30), nullable=False)  # sentiment, topic, progress, crisis, effectiveness
    analysis_scope = Column(String(20), nullable=False, default="full_session")  # full_session, recent, custom_range
    analyzed_message_count = Column(Integer, nullable=False)
    
    # Analysis results
    analysis_results = Column(JSON, nullable=False)  # Main analysis data
    confidence_score = Column(Float, nullable=True)  # Overall confidence (0-1)
    
    # Sentiment analysis
    overall_sentiment = Column(Float, nullable=True)  # -1 to 1
    sentiment_progression = Column(JSON, nullable=True)  # Array of sentiment over time
    emotional_themes = Column(ARRAY(String), nullable=True)
    
    # Topic analysis
    main_topics = Column(ARRAY(String), nullable=True)
    topic_distribution = Column(JSON, nullable=True)  # Dict of topics and weights
    conversation_themes = Column(ARRAY(String), nullable=True)
    
    # Progress tracking
    therapeutic_progress = Column(JSON, nullable=True)
    goals_addressed = Column(ARRAY(String), nullable=True)
    coping_strategies_discussed = Column(ARRAY(String), nullable=True)
    insights_generated = Column(ARRAY(String), nullable=True)
    
    # Crisis and risk assessment
    crisis_indicators = Column(JSON, nullable=True)
    risk_factors = Column(ARRAY(String), nullable=True)
    protective_factors = Column(ARRAY(String), nullable=True)
    intervention_recommendations = Column(ARRAY(String), nullable=True)
    
    # Effectiveness metrics
    session_effectiveness = Column(Float, nullable=True)  # 0-1 score
    ai_performance_metrics = Column(JSON, nullable=True)
    user_engagement_score = Column(Float, nullable=True)
    therapeutic_alliance_score = Column(Float, nullable=True)
    
    # Recommendations
    immediate_recommendations = Column(ARRAY(String), nullable=True)
    follow_up_suggestions = Column(ARRAY(String), nullable=True)
    resource_recommendations = Column(JSON, nullable=True)
    
    # Quality assessment
    conversation_quality_score = Column(Float, nullable=True)
    ai_response_quality = Column(Float, nullable=True)
    user_satisfaction_predicted = Column(Float, nullable=True)
    
    # Analysis metadata
    ai_model_version = Column(String(50), nullable=False)
    analysis_duration_ms = Column(Float, nullable=True)
    analysis_complexity = Column(String(20), nullable=True)  # simple, medium, complex
    
    # Status and sharing
    analysis_status = Column(String(20), nullable=False, default="completed")
    is_shared_with_user = Column(Boolean, default=True, nullable=False)
    user_viewed = Column(Boolean, default=False, nullable=False)
    user_viewed_at = Column(DateTime, nullable=True)
    
    # Timestamps
    analyzed_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    session = relationship("ChatSession", back_populates="analyses")
    
    def __repr__(self):
        return f"<ChatAnalysis(id={self.analysis_id}, session={self.session_id}, type={self.analysis_type})>"

class ChatTemplate(Base):
    """Pre-defined chat templates and responses"""
    __tablename__ = "chat_templates"
    
    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_name = Column(String(100), nullable=False, unique=True)
    template_type = Column(String(30), nullable=False)  # greeting, crisis, closure, check_in
    
    # Template content
    template_text = Column(Text, nullable=False)
    variables = Column(ARRAY(String), nullable=True)  # Variables that can be substituted
    conditions = Column(JSON, nullable=True)  # Conditions for when to use template
    
    # Context and usage
    therapeutic_intent = Column(String(50), nullable=False)
    emotional_tone = Column(String(30), nullable=False, default="empathetic")
    crisis_level = Column(String(20), nullable=True)  # For crisis templates
    session_type = Column(String(30), nullable=True)  # When to use this template
    
    # Personalization
    personality_variants = Column(JSON, nullable=True)  # Different personality versions
    language_variants = Column(JSON, nullable=True)  # Different language versions
    cultural_adaptations = Column(JSON, nullable=True)  # Cultural adaptations
    
    # Usage tracking
    usage_count = Column(Integer, default=0, nullable=False)
    effectiveness_score = Column(Float, nullable=True)
    user_feedback_score = Column(Float, nullable=True)
    
    # Status and management
    is_active = Column(Boolean, default=True, nullable=False)
    is_approved = Column(Boolean, default=False, nullable=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    approval_notes = Column(Text, nullable=True)
    
    # Metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    tags = Column(ARRAY(String), nullable=True)
    message_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_used = Column(DateTime, nullable=True)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])
    
    def __repr__(self):
        return f"<ChatTemplate(name={self.template_name}, type={self.template_type}, intent={self.therapeutic_intent})>"

class ConversationFlow(Base):
    """Conversation flow patterns and logic"""
    __tablename__ = "conversation_flows"
    
    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flow_name = Column(String(100), nullable=False, unique=True)
    flow_type = Column(String(30), nullable=False)  # guided_therapy, crisis_intervention, check_in
    
    # Flow structure
    flow_steps = Column(JSON, nullable=False)  # Array of flow steps
    decision_trees = Column(JSON, nullable=True)  # Decision logic
    branching_conditions = Column(JSON, nullable=True)  # When to branch
    
    # Flow configuration
    session_types = Column(ARRAY(String), nullable=True)  # Compatible session types
    therapeutic_approaches = Column(ARRAY(String), nullable=True)  # Compatible approaches
    target_conditions = Column(ARRAY(String), nullable=True)  # Target mental health conditions
    
    # Flow characteristics
    estimated_duration_minutes = Column(Integer, nullable=True)
    difficulty_level = Column(String(20), nullable=True)  # beginner, intermediate, advanced
    requires_preparation = Column(Boolean, default=False, nullable=False)
    
    # Effectiveness and tracking
    completion_rate = Column(Float, nullable=True)  # 0-1
    effectiveness_score = Column(Float, nullable=True)  # 0-1
    user_satisfaction = Column(Float, nullable=True)  # 0-1
    usage_count = Column(Integer, default=0, nullable=False)
    
    # Status and management
    is_active = Column(Boolean, default=True, nullable=False)
    is_validated = Column(Boolean, default=False, nullable=False)
    validation_notes = Column(Text, nullable=True)
    
    # Metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(ARRAY(String), nullable=True)
    attachment_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_used = Column(DateTime, nullable=True)
    
    # Relationships
    creator = relationship("User", back_populates="conversation_flows")
    
    def __repr__(self):
        return f"<ConversationFlow(name={self.flow_name}, type={self.flow_type})>"

# Add to ALL_MODELS in models/__init__.py
ALL_CHAT_MODELS = [
    ChatSession,
    ChatMessage,
    ChatAnalysis,
    ChatTemplate,
    ConversationFlow
]
