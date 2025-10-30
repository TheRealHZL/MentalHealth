"""
AI Endpoints for MindBridge Custom AI

Alle AI-bezogenen API-Endpunkte für unsere eigene KI-Implementation.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import base64
import uuid

from src.core.security import get_current_user_id_optional, get_current_user_id
from src.core.rate_limiting import (
    limiter,
    AI_CHAT_LIMIT,
    AI_MOOD_ANALYSIS_LIMIT,
    GENERAL_API_LIMIT
)
from src.schemas.ai import (
    EmotionPredictionRequest, EmotionPredictionResponse,
    MoodPredictionRequest, MoodPredictionResponse,
    ChatRequest, ChatResponse,
    SentimentAnalysisRequest, SentimentAnalysisResponse,
    AIStatusResponse
)
from src.services.encryption_service import EncryptionService
from src.models.encrypted_models import EncryptedChatMessage
from src.core.database import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

logger = logging.getLogger(__name__)

router = APIRouter()


# ========================================
# Encrypted Chat Message Models
# ========================================

class EncryptedChatPayload(BaseModel):
    """Encrypted chat message payload from client"""
    ciphertext: str = Field(description="Base64-encoded encrypted data")
    nonce: str = Field(description="Base64-encoded nonce (12 bytes)")
    version: int = Field(default=1, description="Encryption version")


class EncryptedChatMessageCreate(BaseModel):
    """Create encrypted chat message"""
    encrypted_data: EncryptedChatPayload = Field(description="Encrypted chat data")
    session_id: Optional[str] = Field(None, description="Optional session ID for grouping")
    message_type: str = Field(default="chat", description="Message type")


class EncryptedChatMessageResponse(BaseModel):
    """Encrypted chat message response"""
    id: str = Field(description="Message ID")
    user_id: str = Field(description="User ID")
    session_id: Optional[str] = Field(None, description="Session ID")
    encrypted_data: EncryptedChatPayload = Field(description="Encrypted data")
    message_type: str = Field(description="Message type")
    created_at: datetime = Field(description="Creation timestamp")
    encryption_version: int = Field(description="Encryption version")


# ========================================
# Original AI Endpoints (Unencrypted)
# ========================================

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
@limiter.limit(AI_MOOD_ANALYSIS_LIMIT)  # 30 emotion predictions per minute
async def predict_emotion(
    req: Request,
    request: ChatRequest,  # Reuse chat request structure
    user_id: Optional[str] = Depends(get_current_user_id_optional)
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
                detail="AI Engine not ready. Models need to be trained first. Please use /api/v1/ai/training/start endpoint to train models."
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
@limiter.limit(AI_MOOD_ANALYSIS_LIMIT)  # 30 mood predictions per minute
async def predict_mood(
    req: Request,
    request: MoodPredictionRequest,
    user_id: Optional[str] = Depends(get_current_user_id_optional)
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
                detail="AI Engine not ready. Models need to be trained first. Please use /api/v1/ai/training/start endpoint to train models."
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
@limiter.limit(AI_CHAT_LIMIT)  # 20 AI chat requests per minute
async def chat_with_ai(
    req: Request,
    request: ChatRequest,
    user_id: Optional[str] = Depends(get_current_user_id_optional)
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
                detail="AI Engine not ready. Models need to be trained first. Please use /api/v1/ai/training/start endpoint to train models."
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
                detail="AI Engine not ready. Models need to be trained first. Please use /api/v1/ai/training/start endpoint to train models."
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
                detail="AI Engine not ready. Models need to be trained first. Please use /api/v1/ai/training/start endpoint to train models."
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
        
        # Feedback storage implementation
        # In production, this would save to a feedback database table
        # For now, log the feedback for monitoring and future model improvement
        logger.info(f"🔬 AI Feedback received from user {user_id}")
        logger.info(f"🔬 Model: {feedback_data.get('model_name')}, "
                   f"Prediction: {feedback_data.get('model_prediction')}, "
                   f"Score: {feedback_data.get('feedback_score')}")

        # Future enhancement: Save to database for model retraining
        # Example implementation:
        # from src.services.feedback_service import FeedbackService
        # feedback_service = FeedbackService(db)
        # feedback_id = await feedback_service.save_ai_feedback(
        #     user_id=user_id,
        #     feedback_data=feedback_record
        # )
        
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


# ========================================
# Encrypted Chat Message Endpoints (Zero-Knowledge)
# ========================================

@router.post("/chat/encrypted", response_model=EncryptedChatMessageResponse)
async def create_encrypted_chat_message(
    chat_data: EncryptedChatMessageCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
    _rate_limit = Depends(ai_rate_limit)
) -> Dict[str, Any]:
    """
    Store Encrypted Chat Message (Zero-Knowledge)

    Stores client-side encrypted AI chat messages. The server CANNOT read the conversation!

    **Zero-Knowledge:**
    - User messages encrypted in the browser
    - AI responses encrypted in the browser
    - Server stores encrypted blobs
    - Server NEVER sees conversation content
    - Perfect for sensitive therapeutic conversations
    """
    try:
        # Validate encrypted payload structure
        payload_dict = {
            "ciphertext": chat_data.encrypted_data.ciphertext,
            "nonce": chat_data.encrypted_data.nonce,
            "version": chat_data.encrypted_data.version
        }

        is_valid, error_msg = EncryptionService.validate_encrypted_payload(payload_dict)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid encrypted payload: {error_msg}"
            )

        # Decode base64 to binary for storage
        ciphertext_bytes = base64.b64decode(chat_data.encrypted_data.ciphertext)
        nonce_bytes = base64.b64decode(chat_data.encrypted_data.nonce)

        # Combine ciphertext + nonce for storage
        encrypted_data = ciphertext_bytes + nonce_bytes

        # Validate size
        is_size_valid, size_error = EncryptionService.validate_encrypted_data_size(encrypted_data)
        if not is_size_valid:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=size_error
            )

        # Parse session_id if provided
        session_uuid = None
        if chat_data.session_id:
            try:
                session_uuid = uuid.UUID(chat_data.session_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid session_id format"
                )

        # Create encrypted chat message
        message = EncryptedChatMessage(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            session_id=session_uuid,
            encrypted_data=encrypted_data,
            message_type=chat_data.message_type,
            encryption_version=chat_data.encrypted_data.version,
            is_deleted=False
        )

        db.add(message)
        await db.commit()
        await db.refresh(message)

        logger.info(f"Encrypted chat message created for user {user_id}")

        # Extract nonce for response (last 12 bytes)
        stored_ciphertext = message.encrypted_data[:-12]
        stored_nonce = message.encrypted_data[-12:]

        return {
            "id": str(message.id),
            "user_id": str(message.user_id),
            "session_id": str(message.session_id) if message.session_id else None,
            "encrypted_data": {
                "ciphertext": base64.b64encode(stored_ciphertext).decode('utf-8'),
                "nonce": base64.b64encode(stored_nonce).decode('utf-8'),
                "version": message.encryption_version
            },
            "message_type": message.message_type,
            "created_at": message.created_at,
            "encryption_version": message.encryption_version
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create encrypted chat message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verschlüsselte Chat-Nachricht konnte nicht erstellt werden"
        )


@router.get("/chat/encrypted", response_model=List[EncryptedChatMessageResponse])
async def get_encrypted_chat_messages(
    session_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
) -> List[Dict[str, Any]]:
    """
    Get Encrypted Chat Messages (Zero-Knowledge)

    Returns encrypted chat messages. Client must decrypt them.
    Optionally filter by session_id.
    """
    try:
        # Build query
        query = select(EncryptedChatMessage).where(
            and_(
                EncryptedChatMessage.user_id == uuid.UUID(user_id),
                EncryptedChatMessage.is_deleted == False
            )
        )

        # Filter by session if provided
        if session_id:
            try:
                session_uuid = uuid.UUID(session_id)
                query = query.where(EncryptedChatMessage.session_id == session_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid session_id format"
                )

        # Execute query
        result = await db.execute(
            query
            .order_by(EncryptedChatMessage.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        messages = result.scalars().all()

        # Format response
        response = []
        for message in messages:
            # Extract nonce (last 12 bytes)
            stored_ciphertext = message.encrypted_data[:-12]
            stored_nonce = message.encrypted_data[-12:]

            response.append({
                "id": str(message.id),
                "user_id": str(message.user_id),
                "session_id": str(message.session_id) if message.session_id else None,
                "encrypted_data": {
                    "ciphertext": base64.b64encode(stored_ciphertext).decode('utf-8'),
                    "nonce": base64.b64encode(stored_nonce).decode('utf-8'),
                    "version": message.encryption_version
                },
                "message_type": message.message_type,
                "created_at": message.created_at,
                "encryption_version": message.encryption_version
            })

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get encrypted chat messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verschlüsselte Chat-Nachrichten konnten nicht geladen werden"
        )


@router.delete("/chat/encrypted/{message_id}")
async def delete_encrypted_chat_message(
    message_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Delete Encrypted Chat Message (Soft Delete)

    Marks message as deleted (GDPR compliance).
    """
    try:
        result = await db.execute(
            select(EncryptedChatMessage)
            .where(
                and_(
                    EncryptedChatMessage.id == uuid.UUID(message_id),
                    EncryptedChatMessage.user_id == uuid.UUID(user_id),
                    EncryptedChatMessage.is_deleted == False
                )
            )
        )

        message = result.scalar_one_or_none()

        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Verschlüsselte Chat-Nachricht nicht gefunden"
            )

        # Soft delete
        message.is_deleted = True
        message.deleted_at = datetime.utcnow()

        await db.commit()

        logger.info(f"Encrypted chat message soft-deleted: {message_id}")

        return {
            "success": True,
            "message": "Verschlüsselte Chat-Nachricht erfolgreich gelöscht"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete encrypted chat message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verschlüsselte Chat-Nachricht konnte nicht gelöscht werden"
        )


@router.delete("/chat/encrypted/session/{session_id}")
async def delete_encrypted_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Delete All Messages in Encrypted Session (Soft Delete)

    Deletes all messages in a specific session (GDPR compliance).
    """
    try:
        # Parse session_id
        try:
            session_uuid = uuid.UUID(session_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid session_id format"
            )

        # Get all messages in session
        result = await db.execute(
            select(EncryptedChatMessage)
            .where(
                and_(
                    EncryptedChatMessage.session_id == session_uuid,
                    EncryptedChatMessage.user_id == uuid.UUID(user_id),
                    EncryptedChatMessage.is_deleted == False
                )
            )
        )

        messages = result.scalars().all()

        if not messages:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Keine Nachrichten in dieser Session gefunden"
            )

        # Soft delete all messages
        deleted_count = 0
        for message in messages:
            message.is_deleted = True
            message.deleted_at = datetime.utcnow()
            deleted_count += 1

        await db.commit()

        logger.info(f"Encrypted session deleted: {session_id} ({deleted_count} messages)")

        return {
            "success": True,
            "message": f"{deleted_count} verschlüsselte Nachrichten erfolgreich gelöscht",
            "deleted_count": deleted_count
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete encrypted session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verschlüsselte Session konnte nicht gelöscht werden"
        )
