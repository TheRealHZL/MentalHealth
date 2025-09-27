"""
AI Endpoints for MindBridge Custom AI

Alle AI-bezogenen API-Endpunkte für unsere eigene KI-Implementation.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Dict, Any, Optional, List
import logging

from src.core.security import get_current_user_id_optional, create_rate_limit_dependency
from src.schemas.ai import (
    EmotionPredictionRequest, EmotionPredictionResponse,
    MoodPredictionRequest, MoodPredictionResponse,
    ChatRequest, ChatResponse,
    SentimentAnalysisRequest, SentimentAnalysisResponse,
    AIStatusResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Rate limiting for AI endpoints
ai_rate_limit = create_rate_limit_dependency(limit=100, window_minutes=60)

@router.get("/status", response_model=AIStatusResponse)
async def get_ai_status(request: Request) -> Dict[str, Any]:
    """
    Get AI Engine Status
    
    Returns status of all AI models and performance metrics.
    """
    try:
        ai_engine = request.app.state.ai_engine
        
        if not ai_engine:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI Engine not available"
            )
        
        status_info = await ai_engine.get_status()
        
        return {
            "success": True,
            "data": status_info,
            "timestamp": status_info.get("timestamp")
        }
        
    except Exception as e:
        logger.error(f"AI status check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get AI status"
        )

@router.post("/emotion/predict", response_model=EmotionPredictionResponse)
async def predict_emotion(
    request: ChatRequest,  # Reuse chat request structure
    req: Request,
    user_id: Optional[str] = Depends(get_current_user_id_optional),
    _rate_limit = Depends(ai_rate_limit)
) -> Dict[str, Any]:
    """
    Predict Emotion from Text
    
    Analyzes text and returns detected emotion with confidence scores.
    """
    try:
        ai_engine = req.app.state.ai_engine
        
        if not ai_engine or not ai_engine.is_ready():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI Engine not ready"
            )
        
        # Predict emotion
        result = await ai_engine.predict_emotion(
            text=request.message,
            context=request.context
        )
        
        return {
            "success": True,
            "data": {
                "emotion": result["emotion"],
                "confidence": result["confidence"],
                "probabilities": result.get("probabilities", {}),
                "latency_ms": result.get("latency_ms", 0)
            },
            "user_id": user_id,
            "timestamp": None  # Will be set by response model
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Emotion prediction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Emotion prediction failed"
        )

@router.post("/mood/predict", response_model=MoodPredictionResponse)
async def predict_mood(
    request: MoodPredictionRequest,
    req: Request,
    user_id: Optional[str] = Depends(get_current_user_id_optional),
    _rate_limit = Depends(ai_rate_limit)
) -> Dict[str, Any]:
    """
    Predict Mood Score
    
    Analyzes text and optional metadata to predict mood on 1-10 scale.
    """
    try:
        ai_engine = req.app.state.ai_engine
        
        if not ai_engine or not ai_engine.is_ready():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI Engine not ready"
            )
        
        # Predict mood
        result = await ai_engine.predict_mood(
            text=request.text,
            history=request.history,
            metadata=request.metadata
        )
        
        return {
            "success": True,
            "data": {
                "mood_score": result["mood_score"],
                "confidence": result["confidence"],
                "trend": result["trend"],
                "scale_info": result.get("scale", "1-10 scale"),
                "latency_ms": result.get("latency_ms", 0)
            },
            "user_id": user_id,
            "timestamp": None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mood prediction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Mood prediction failed"
        )

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    req: Request,
    user_id: Optional[str] = Depends(get_current_user_id_optional),
    _rate_limit = Depends(ai_rate_limit)
) -> Dict[str, Any]:
    """
    Chat with AI Assistant
    
    Generates empathetic response using custom chat model.
    """
    try:
        ai_engine = req.app.state.ai_engine
        
        if not ai_engine or not ai_engine.is_ready():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI Engine not ready"
            )
        
        # Generate chat response
        result = await ai_engine.generate_chat_response(
            user_message=request.message,
            conversation_history=request.conversation_history,
            user_context=request.context
        )
        
        return {
            "success": True,
            "data": {
                "response": result["response"],
                "confidence": result["confidence"],
                "safety_checked": result.get("safety_checked", True),
                "empathy_score": result.get("empathy_score"),
                "latency_ms": result.get("latency_ms", 0)
            },
            "user_id": user_id,
            "timestamp": None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Chat generation failed"
        )

@router.post("/sentiment/analyze", response_model=SentimentAnalysisResponse)
async def analyze_sentiment(
    request: SentimentAnalysisRequest,
    req: Request,
    user_id: Optional[str] = Depends(get_current_user_id_optional),
    _rate_limit = Depends(ai_rate_limit)
) -> Dict[str, Any]:
    """
    Analyze Text Sentiment
    
    Fast sentiment analysis using custom CNN model.
    """
    try:
        ai_engine = req.app.state.ai_engine
        
        if not ai_engine or not ai_engine.is_ready():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI Engine not ready"
            )
        
        # Analyze sentiment
        result = await ai_engine.analyze_sentiment(request.text)
        
        return {
            "success": True,
            "data": {
                "sentiment": result["sentiment"],
                "confidence": result["confidence"],
                "score": result["score"],
                "intensity": result.get("intensity"),
                "latency_ms": result.get("latency_ms", 0)
            },
            "user_id": user_id,
            "timestamp": None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sentiment analysis failed"
        )

@router.post("/analyze/comprehensive")
async def comprehensive_analysis(
    request: ChatRequest,
    req: Request,
    user_id: Optional[str] = Depends(get_current_user_id_optional),
    _rate_limit = Depends(ai_rate_limit)
) -> Dict[str, Any]:
    """
    Comprehensive AI Analysis
    
    Runs all AI models on the input text for complete analysis.
    """
    try:
        ai_engine = req.app.state.ai_engine
        
        if not ai_engine or not ai_engine.is_ready():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI Engine not ready"
            )
        
        # Run all analyses in parallel
        import asyncio
        
        emotion_task = ai_engine.predict_emotion(request.message, request.context)
        mood_task = ai_engine.predict_mood(request.message, request.conversation_history)
        sentiment_task = ai_engine.analyze_sentiment(request.message)
        
        emotion_result, mood_result, sentiment_result = await asyncio.gather(
            emotion_task, mood_task, sentiment_task
        )
        
        # Generate response based on analysis
        chat_result = await ai_engine.generate_chat_response(
            user_message=request.message,
            conversation_history=request.conversation_history,
            user_context={
                **request.context,
                "emotion": emotion_result["emotion"],
                "mood_score": mood_result["mood_score"],
                "sentiment": sentiment_result["sentiment"]
            }
        )
        
        return {
            "success": True,
            "data": {
                "emotion_analysis": emotion_result,
                "mood_analysis": mood_result,
                "sentiment_analysis": sentiment_result,
                "ai_response": chat_result,
                "summary": {
                    "overall_sentiment": sentiment_result["sentiment"],
                    "dominant_emotion": emotion_result["emotion"],
                    "mood_level": mood_result["mood_score"],
                    "confidence_average": (
                        emotion_result["confidence"] + 
                        mood_result["confidence"] + 
                        sentiment_result["confidence"]
                    ) / 3
                }
            },
            "user_id": user_id,
            "analysis_timestamp": None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Comprehensive analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Comprehensive analysis failed"
        )

@router.get("/models/info")
async def get_models_info(
    req: Request,
    user_id: Optional[str] = Depends(get_current_user_id_optional)
) -> Dict[str, Any]:
    """
    Get AI Models Information
    
    Returns detailed information about all loaded AI models.
    """
    try:
        ai_engine = req.app.state.ai_engine
        
        if not ai_engine:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI Engine not available"
            )
        
        models_info = {}
        
        # Get info for each model
        for model_name, model in ai_engine.models.items():
            if hasattr(model, 'get_model_info'):
                models_info[model_name] = model.get_model_info()
        
        # Add tokenizer info
        if ai_engine.tokenizer and hasattr(ai_engine.tokenizer, 'get_vocab_info'):
            models_info['tokenizer'] = ai_engine.tokenizer.get_vocab_info()
        
        return {
            "success": True,
            "data": {
                "models": models_info,
                "total_models": len(ai_engine.models),
                "engine_status": ai_engine.is_ready(),
                "device": str(ai_engine.device) if hasattr(ai_engine, 'device') else "unknown"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get models info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get models information"
        )

@router.post("/feedback/model")
async def submit_model_feedback(
    feedback_data: Dict[str, Any],
    req: Request,
    user_id: str = Depends(get_current_user_id_optional)
) -> Dict[str, Any]:
    """
    Submit Feedback for AI Models
    
    Allows users to provide feedback on AI predictions for model improvement.
    """
    try:
        # Store feedback for future model training
        # This would typically go to a database
        
        feedback_entry = {
            "user_id": user_id,
            "model_type": feedback_data.get("model_type"),
            "input_text": feedback_data.get("input_text"),
            "model_prediction": feedback_data.get("model_prediction"),
            "user_feedback": feedback_data.get("user_feedback"),
            "correct_label": feedback_data.get("correct_label"),
            "feedback_score": feedback_data.get("feedback_score"),  # 1-5 rating
            "timestamp": None  # Will be set by database
        }
        
        # TODO: Save to database via feedback service
        logger.info(f"Received AI model feedback from user {user_id}")
        
        return {
            "success": True,
            "message": "Feedback received successfully",
            "data": {
                "feedback_id": "temp_id",  # Would be actual ID from database
                "status": "processed"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to submit model feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback"
        )
