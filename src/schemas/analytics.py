"""
Analytics & Statistics Schemas

Pydantic Schemas für Analytics und Statistiken.
"""

from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AnalyticsRequest(BaseModel):
    """Analytics request schema"""

    start_date: Optional[date] = Field(None, description="Start date for analysis")
    end_date: Optional[date] = Field(None, description="End date for analysis")
    metric_types: Optional[List[str]] = Field(
        None, description="Types of metrics to include"
    )
    include_ai_insights: bool = Field(True, description="Include AI-generated insights")


class MoodAnalyticsResponse(BaseModel):
    """Mood analytics response schema"""

    period_summary: Dict[str, Any]
    trend_analysis: Dict[str, Any]
    pattern_insights: List[str]
    recommendations: List[str]
    mood_distribution: Dict[str, int]
    correlations: Dict[str, float]
    ai_insights: Optional[str] = None


class DreamAnalyticsResponse(BaseModel):
    """Dream analytics response schema"""

    dream_frequency: Dict[str, int]
    common_symbols: Dict[str, int]
    dream_types: Dict[str, int]
    lucid_dream_rate: float
    mood_correlation: float
    recurring_themes: List[str]
    ai_pattern_analysis: Optional[str] = None


class TherapyProgressResponse(BaseModel):
    """Therapy progress response schema"""

    progress_metrics: Dict[str, Any]
    goal_completion_rate: float
    mood_improvement_trend: str
    technique_effectiveness: Dict[str, float]
    session_insights: List[str]
    recommendations: List[str]
    ai_progress_analysis: Optional[str] = None
