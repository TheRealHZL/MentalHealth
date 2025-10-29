"""
Analytics Endpoints

AI-powered insights, trends, and pattern recognition.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime, timedelta

from src.core.database import get_async_session
from src.core.security import get_current_user_id, require_patient_or_therapist
from src.services.analytics_service import AnalyticsService
from src.services.mood_analytics_service import MoodAnalyticsService

router = APIRouter()


@router.get("/overview")
async def get_analytics_overview(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get comprehensive analytics overview for current user
    
    Returns insights, trends, patterns, and recommendations.
    """
    analytics_service = AnalyticsService(db)
    
    try:
        overview = await analytics_service.get_user_analytics_overview(current_user_id)
        
        return {
            "success": True,
            "data": overview,
            "message": "Analytics overview retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve analytics: {str(e)}"
        )


@router.get("/mood/trends")
async def get_mood_trends(
    days: int = Query(30, ge=7, le=365, description="Number of days to analyze"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get mood trends over specified time period
    
    Analyzes mood patterns, changes, and correlations.
    """
    mood_analytics = MoodAnalyticsService(db)
    
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        trends = await mood_analytics.get_mood_trends(
            user_id=current_user_id,
            start_date=start_date
        )
        
        return {
            "success": True,
            "data": trends,
            "period": f"Last {days} days",
            "message": "Mood trends retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve mood trends: {str(e)}"
        )


@router.get("/mood/patterns")
async def get_mood_patterns(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Identify mood patterns and correlations
    
    Uses AI to detect patterns in mood changes, triggers, and activities.
    """
    mood_analytics = MoodAnalyticsService(db)
    
    try:
        patterns = await mood_analytics.detect_patterns(current_user_id)
        
        return {
            "success": True,
            "data": patterns,
            "message": "Mood patterns identified successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect patterns: {str(e)}"
        )


@router.get("/dreams/insights")
async def get_dream_insights(
    days: int = Query(30, ge=7, le=365, description="Number of days to analyze"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get AI-powered dream insights and symbol analysis
    
    Analyzes recurring themes, symbols, and emotional patterns in dreams.
    """
    analytics_service = AnalyticsService(db)
    
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        insights = await analytics_service.get_dream_insights(
            user_id=current_user_id,
            start_date=start_date
        )
        
        return {
            "success": True,
            "data": insights,
            "period": f"Last {days} days",
            "message": "Dream insights retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dream insights: {str(e)}"
        )


@router.get("/recommendations")
async def get_personalized_recommendations(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get AI-powered personalized recommendations
    
    Based on mood patterns, activities, and historical data.
    """
    analytics_service = AnalyticsService(db)
    
    try:
        recommendations = await analytics_service.get_recommendations(current_user_id)
        
        return {
            "success": True,
            "data": recommendations,
            "message": "Personalized recommendations generated successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}"
        )


@router.get("/wellness-score")
async def get_wellness_score(
    days: int = Query(30, ge=7, le=90, description="Number of days to calculate score"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Calculate overall wellness score
    
    Composite score based on mood, sleep, activities, and consistency.
    """
    analytics_service = AnalyticsService(db)
    
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        score = await analytics_service.calculate_wellness_score(
            user_id=current_user_id,
            start_date=start_date
        )
        
        return {
            "success": True,
            "data": score,
            "period": f"Last {days} days",
            "message": "Wellness score calculated successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate wellness score: {str(e)}"
        )


@router.get("/activity-correlation")
async def get_activity_correlation(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Analyze correlation between activities and mood
    
    Identifies which activities have positive or negative impact on mood.
    """
    mood_analytics = MoodAnalyticsService(db)
    
    try:
        correlations = await mood_analytics.analyze_activity_correlations(current_user_id)
        
        return {
            "success": True,
            "data": correlations,
            "message": "Activity correlations analyzed successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze correlations: {str(e)}"
        )


@router.get("/risk-assessment")
async def get_risk_assessment(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
):
    """
    AI-powered mental health risk assessment
    
    ⚠️ **Important**: This is NOT a substitute for professional medical advice.
    Always consult healthcare professionals for concerns.
    """
    analytics_service = AnalyticsService(db)
    
    try:
        assessment = await analytics_service.assess_risk_indicators(current_user_id)
        
        return {
            "success": True,
            "data": assessment,
            "disclaimer": "This assessment is for informational purposes only and does not replace professional medical advice.",
            "message": "Risk assessment completed successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete risk assessment: {str(e)}"
        )


@router.get("/export")
async def export_analytics_report(
    format: str = Query("json", regex="^(json|csv|pdf)$"),
    days: int = Query(30, ge=7, le=365),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Export comprehensive analytics report
    
    Available formats: JSON, CSV, PDF
    """
    analytics_service = AnalyticsService(db)
    
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        report = await analytics_service.export_analytics_report(
            user_id=current_user_id,
            start_date=start_date,
            format=format
        )
        
        return {
            "success": True,
            "data": report,
            "format": format,
            "period": f"Last {days} days",
            "message": f"Analytics report exported as {format.upper()}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export report: {str(e)}"
        )


# Therapist-specific analytics endpoints
@router.get("/patient/{patient_id}/overview")
async def get_patient_analytics_overview(
    patient_id: str,
    current_user_id: str = Depends(require_patient_or_therapist),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get analytics overview for specific patient (therapist access only)
    
    Requires valid data sharing permission.
    """
    analytics_service = AnalyticsService(db)
    
    try:
        # Verify therapist has access
        has_access = await analytics_service.verify_therapist_access(
            therapist_id=current_user_id,
            patient_id=patient_id
        )
        
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No access to this patient's data"
            )
        
        overview = await analytics_service.get_user_analytics_overview(patient_id)
        
        return {
            "success": True,
            "data": overview,
            "patient_id": patient_id,
            "message": "Patient analytics retrieved successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve patient analytics: {str(e)}"
        )


@router.get("/compare")
async def compare_time_periods(
    period1_start: datetime = Query(..., description="Start of first period"),
    period1_end: datetime = Query(..., description="End of first period"),
    period2_start: datetime = Query(..., description="Start of second period"),
    period2_end: datetime = Query(..., description="End of second period"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Compare analytics between two time periods
    
    Useful for tracking progress and identifying changes over time.
    """
    analytics_service = AnalyticsService(db)
    
    try:
        comparison = await analytics_service.compare_periods(
            user_id=current_user_id,
            period1=(period1_start, period1_end),
            period2=(period2_start, period2_end)
        )
        
        return {
            "success": True,
            "data": comparison,
            "periods": {
                "period1": f"{period1_start.date()} to {period1_end.date()}",
                "period2": f"{period2_start.date()} to {period2_end.date()}"
            },
            "message": "Period comparison completed successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare periods: {str(e)}"
        )
