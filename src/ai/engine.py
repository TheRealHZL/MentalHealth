"""
Custom AI Engine for MindBridge

Hauptklasse für die eigene KI-Implementierung ohne externe ML-Frameworks.
Verwaltet alle AI-Modelle und Inference-Pipelines.
"""

import asyncio
import logging
import torch
import torch.nn as nn
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import json
import time
from datetime import datetime

from src.core.config import get_settings

logger = logging.getLogger(__name__)

class AIEngine:
    """
    Zentrale AI Engine für MindBridge
    
    Verwaltet alle Custom AI Modelle:
    - Emotion Classifier
    - Mood Predictor 
    - Chat Generator
    - Sentiment Analyzer
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.device = torch.device(self.settings.AI_DEVICE)
        self.models: Dict[str, nn.Module] = {}
        self.tokenizer = None
        self.is_initialized = False
        self.model_stats = {}
        
        logger.info(f"🧠 AI Engine initialized on device: {self.device}")
    
    async def initialize(self):
        """
        Initialisiert alle AI-Modelle
        """
        try:
            logger.info("🚀 Loading Custom AI Models...")
            
            # Load Custom Tokenizer
            await self._load_tokenizer()
            
            # Load AI Models
            await self._load_emotion_classifier()
            await self._load_mood_predictor()
            await self._load_chat_generator()
            await self._load_sentiment_analyzer()
            
            # Initialize model statistics
            self._init_model_stats()
            
            self.is_initialized = True
            logger.info("✅ All AI Models loaded successfully!")
            
        except Exception as e:
            logger.error(f"❌ AI Engine initialization failed: {e}")
            raise
    
    async def _load_tokenizer(self):
        """Lädt den Custom Tokenizer"""
        from src.ai.preprocessing.tokenizer import MindBridgeTokenizer
        
        tokenizer_path = Path(self.settings.TOKENIZER_PATH)
        
        if tokenizer_path.exists():
            self.tokenizer = MindBridgeTokenizer.load(tokenizer_path)
            logger.info("✅ Custom Tokenizer loaded")
        else:
            # Create new tokenizer if not exists
            self.tokenizer = MindBridgeTokenizer(
                vocab_size=self.settings.VOCAB_SIZE
            )
            # Train on sample data
            await self.tokenizer.train_from_samples()
            self.tokenizer.save(tokenizer_path)
            logger.info("✅ New Custom Tokenizer created and saved")
    
    async def _load_emotion_classifier(self):
        """Lädt das Emotion Classification Model"""
        from src.ai.models.emotion_classifier import EmotionClassifier
        
        model_path = Path(self.settings.EMOTION_MODEL_PATH)
        
        # Model Architecture
        self.models['emotion'] = EmotionClassifier(
            vocab_size=self.settings.VOCAB_SIZE,
            embedding_dim=self.settings.EMBEDDING_DIM,
            hidden_dim=self.settings.HIDDEN_DIM,
            num_classes=7,  # 7 basic emotions
            dropout_rate=self.settings.DROPOUT_RATE
        ).to(self.device)
        
        # Load weights if available
        if model_path.exists():
            checkpoint = torch.load(model_path, map_location=self.device)
            self.models['emotion'].load_state_dict(checkpoint['model_state_dict'])
            logger.info("✅ Emotion Classifier loaded from checkpoint")
        else:
            logger.info("⚠️ Emotion Classifier initialized with random weights")
        
        self.models['emotion'].eval()
    
    async def _load_mood_predictor(self):
        """Lädt das Mood Prediction Model"""
        from src.ai.models.mood_predictor import MoodPredictor
        
        model_path = Path(self.settings.MOOD_MODEL_PATH)
        
        # Model Architecture  
        self.models['mood'] = MoodPredictor(
            vocab_size=self.settings.VOCAB_SIZE,
            embedding_dim=self.settings.EMBEDDING_DIM,
            hidden_dim=self.settings.HIDDEN_DIM,
            num_layers=3,  # LSTM layers
            dropout_rate=self.settings.DROPOUT_RATE
        ).to(self.device)
        
        # Load weights if available
        if model_path.exists():
            checkpoint = torch.load(model_path, map_location=self.device)
            self.models['mood'].load_state_dict(checkpoint['model_state_dict'])
            logger.info("✅ Mood Predictor loaded from checkpoint")
        else:
            logger.info("⚠️ Mood Predictor initialized with random weights")
        
        self.models['mood'].eval()
    
    async def _load_chat_generator(self):
        """Lädt das Chat Generation Model"""
        from src.ai.models.chat_generator import ChatGenerator
        
        model_path = Path(self.settings.CHAT_MODEL_PATH)
        
        # Model Architecture
        self.models['chat'] = ChatGenerator(
            vocab_size=self.settings.VOCAB_SIZE,
            embedding_dim=self.settings.EMBEDDING_DIM,
            hidden_dim=self.settings.HIDDEN_DIM,
            num_layers=self.settings.NUM_LAYERS,
            num_heads=self.settings.NUM_HEADS,
            ff_dim=self.settings.FF_DIM,
            dropout_rate=self.settings.DROPOUT_RATE,
            max_length=self.settings.AI_MAX_LENGTH
        ).to(self.device)
        
        # Load weights if available
        if model_path.exists():
            checkpoint = torch.load(model_path, map_location=self.device)
            self.models['chat'].load_state_dict(checkpoint['model_state_dict'])
            logger.info("✅ Chat Generator loaded from checkpoint")
        else:
            logger.info("⚠️ Chat Generator initialized with random weights")
        
        self.models['chat'].eval()
    
    async def _load_sentiment_analyzer(self):
        """Lädt das Sentiment Analysis Model"""
        from src.ai.models.sentiment_analyzer import SentimentAnalyzer
        
        # Model Architecture
        self.models['sentiment'] = SentimentAnalyzer(
            vocab_size=self.settings.VOCAB_SIZE,
            embedding_dim=self.settings.EMBEDDING_DIM,
            num_filters=100,
            filter_sizes=[3, 4, 5],
            dropout_rate=self.settings.DROPOUT_RATE
        ).to(self.device)
        
        logger.info("✅ Sentiment Analyzer initialized")
        self.models['sentiment'].eval()
    
    def _init_model_stats(self):
        """Initialisiert Model-Statistiken"""
        self.model_stats = {
            'emotion': {'predictions': 0, 'avg_confidence': 0.0, 'avg_latency': 0.0},
            'mood': {'predictions': 0, 'avg_confidence': 0.0, 'avg_latency': 0.0},
            'chat': {'generations': 0, 'avg_length': 0.0, 'avg_latency': 0.0},
            'sentiment': {'analyses': 0, 'avg_confidence': 0.0, 'avg_latency': 0.0}
        }
    
    # Public Inference Methods
    
    async def predict_emotion(
        self, 
        text: str, 
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Vorhersage der Emotion in einem Text
        
        Args:
            text: Input text
            context: Additional context information
        
        Returns:
            Dict mit emotion, confidence, probabilities
        """
        start_time = time.time()
        
        try:
            # Preprocess text
            tokens = self.tokenizer.encode(text)
            input_tensor = torch.tensor([tokens], device=self.device)
            
            # Inference
            with torch.no_grad():
                logits = self.models['emotion'](input_tensor)
                probabilities = torch.softmax(logits, dim=-1)
                confidence, predicted_class = torch.max(probabilities, dim=-1)
            
            # Map to emotion labels
            emotion_labels = [
                'joy', 'sadness', 'anger', 'fear', 
                'surprise', 'disgust', 'neutral'
            ]
            
            emotion = emotion_labels[predicted_class.item()]
            confidence_score = confidence.item()
            
            # Update statistics
            latency = time.time() - start_time
            self._update_stats('emotion', confidence_score, latency)
            
            return {
                'emotion': emotion,
                'confidence': confidence_score,
                'probabilities': {
                    label: prob.item() 
                    for label, prob in zip(emotion_labels, probabilities[0])
                },
                'latency_ms': latency * 1000
            }
            
        except Exception as e:
            logger.error(f"Emotion prediction failed: {e}")
            return {
                'emotion': 'neutral',
                'confidence': 0.0,
                'error': str(e)
            }
    
    async def predict_mood(
        self, 
        text: str, 
        history: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Vorhersage der Stimmung basierend auf Text und Historie
        
        Args:
            text: Current text input
            history: Previous texts for context
            metadata: Additional metadata (sleep, stress, etc.)
        
        Returns:
            Dict mit mood_score, trend, confidence
        """
        start_time = time.time()
        
        try:
            # Prepare input sequence
            input_texts = (history or []) + [text]
            token_sequences = [self.tokenizer.encode(t) for t in input_texts[-5:]]  # Last 5 texts
            
            # Pad sequences
            max_len = max(len(seq) for seq in token_sequences)
            padded_sequences = [
                seq + [0] * (max_len - len(seq)) 
                for seq in token_sequences
            ]
            
            input_tensor = torch.tensor(padded_sequences, device=self.device)
            
            # Inference
            with torch.no_grad():
                mood_score = self.models['mood'](input_tensor)
                confidence = torch.sigmoid(mood_score).item()
            
            # Normalize to 1-10 scale
            mood_value = confidence * 9 + 1  # Scale to 1-10
            
            # Calculate trend if history available
            trend = 'stable'
            if history and len(history) > 1:
                # Simple trend calculation
                prev_prediction = await self._get_historical_mood(history[-1])
                if mood_value > prev_prediction + 0.5:
                    trend = 'improving'
                elif mood_value < prev_prediction - 0.5:
                    trend = 'declining'
            
            # Update statistics
            latency = time.time() - start_time
            self._update_stats('mood', confidence, latency)
            
            return {
                'mood_score': round(mood_value, 1),
                'confidence': confidence,
                'trend': trend,
                'scale': '1-10 (1=very negative, 10=very positive)',
                'latency_ms': latency * 1000
            }
            
        except Exception as e:
            logger.error(f"Mood prediction failed: {e}")
            return {
                'mood_score': 5.0,
                'confidence': 0.0,
                'trend': 'unknown',
                'error': str(e)
            }
    
    async def generate_chat_response(
        self, 
        user_message: str,
        conversation_history: Optional[List[Dict]] = None,
        user_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Generiert empathische Chat-Antwort
        
        Args:
            user_message: User's message
            conversation_history: Previous conversation
            user_context: User context (mood, emotions, etc.)
        
        Returns:
            Dict mit response, confidence, safety_checked
        """
        start_time = time.time()
        
        try:
            # Build context prompt
            context_prompt = self._build_chat_context(
                user_message, conversation_history, user_context
            )
            
            # Tokenize input
            input_tokens = self.tokenizer.encode(context_prompt)
            input_tensor = torch.tensor([input_tokens], device=self.device)
            
            # Generate response
            with torch.no_grad():
                generated_tokens = self.models['chat'].generate(
                    input_tensor,
                    max_length=self.settings.MAX_RESPONSE_LENGTH,
                    temperature=self.settings.AI_TEMPERATURE,
                    top_p=self.settings.AI_TOP_P,
                    top_k=self.settings.AI_TOP_K
                )
            
            # Decode response
            response_tokens = generated_tokens[0][len(input_tokens):]
            response_text = self.tokenizer.decode(response_tokens)
            
            # Safety check
            is_safe, safety_score = await self._safety_check(response_text)
            
            if not is_safe:
                response_text = self._get_fallback_response(user_message)
                safety_score = 1.0
            
            # Add disclaimer
            response_text += "\n\n*Hinweis: Ich bin eine KI und ersetze keine professionelle medizinische oder psychologische Beratung.*"
            
            # Update statistics
            latency = time.time() - start_time
            self._update_stats('chat', safety_score, latency, len(response_text))
            
            return {
                'response': response_text,
                'confidence': safety_score,
                'safety_checked': True,
                'length': len(response_text),
                'latency_ms': latency * 1000
            }
            
        except Exception as e:
            logger.error(f"Chat generation failed: {e}")
            return {
                'response': self._get_fallback_response(user_message),
                'confidence': 0.0,
                'safety_checked': True,
                'error': str(e)
            }
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Sentiment-Analyse eines Textes
        
        Args:
            text: Text to analyze
        
        Returns:
            Dict mit sentiment, confidence, score
        """
        start_time = time.time()
        
        try:
            # Tokenize
            tokens = self.tokenizer.encode(text)
            input_tensor = torch.tensor([tokens], device=self.device)
            
            # Inference
            with torch.no_grad():
                logits = self.models['sentiment'](input_tensor)
                confidence = torch.sigmoid(logits).item()
            
            # Map to sentiment
            if confidence > 0.6:
                sentiment = 'positive'
            elif confidence < 0.4:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            
            # Update statistics
            latency = time.time() - start_time
            self._update_stats('sentiment', confidence, latency)
            
            return {
                'sentiment': sentiment,
                'confidence': confidence,
                'score': confidence,  # 0-1 scale
                'latency_ms': latency * 1000
            }
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {
                'sentiment': 'neutral',
                'confidence': 0.0,
                'error': str(e)
            }
    
    # Helper Methods
    
    def _build_chat_context(
        self, 
        user_message: str, 
        history: Optional[List[Dict]] = None,
        context: Optional[Dict] = None
    ) -> str:
        """Builds context prompt for chat generation"""
        
        system_prompt = """Du bist ein einfühlsamer Mental Health Assistant. 
        Antworte empathisch, unterstützend und respektvoll. 
        Gib praktische Tipps, aber weise darauf hin, dass du keine medizinische Fachkraft bist."""
        
        context_parts = [system_prompt]
        
        # Add conversation history
        if history:
            for msg in history[-3:]:  # Last 3 messages
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                context_parts.append(f"{role}: {content}")
        
        # Add user context
        if context:
            mood = context.get('mood_score')
            emotion = context.get('emotion')
            if mood:
                context_parts.append(f"User's current mood: {mood}/10")
            if emotion:
                context_parts.append(f"User's emotion: {emotion}")
        
        # Add current message
        context_parts.append(f"user: {user_message}")
        context_parts.append("assistant:")
        
        return "\n".join(context_parts)
    
    async def _safety_check(self, text: str) -> Tuple[bool, float]:
        """Checks if generated text is safe"""
        
        # Simple safety check - can be enhanced
        unsafe_patterns = [
            'suicide', 'self-harm', 'kill yourself', 'end it all',
            'hurt yourself', 'medication', 'diagnose', 'prescription'
        ]
        
        text_lower = text.lower()
        
        for pattern in unsafe_patterns:
            if pattern in text_lower:
                return False, 0.0
        
        return True, 1.0
    
    def _get_fallback_response(self, user_message: str) -> str:
        """Returns a safe fallback response"""
        
        fallback_responses = [
            "Ich verstehe, dass du durchmachst eine schwierige Zeit. Es ist wichtig, dass du mit jemandem sprichst.",
            "Deine Gefühle sind völlig verständlich. Hast du schon einmal daran gedacht, professionelle Hilfe zu suchen?",
            "Es tut mir leid zu hören, dass es dir nicht gut geht. Du bist nicht allein mit deinen Gefühlen.",
            "Ich bin hier um zuzuhören, aber für ernsthafte Probleme empfehle ich dir, mit einem Therapeuten zu sprechen."
        ]
        
        import random
        return random.choice(fallback_responses)
    
    async def _get_historical_mood(self, text: str) -> float:
        """Simple historical mood calculation"""
        # Simplified - in real implementation, this would use database
        return 5.0
    
    def _update_stats(self, model_name: str, confidence: float, latency: float, length: int = 0):
        """Updates model statistics"""
        stats = self.model_stats[model_name]
        
        # Update counters
        if model_name == 'chat':
            stats['generations'] += 1
            stats['avg_length'] = (stats['avg_length'] + length) / 2
        else:
            stats['predictions'] += 1
            stats['avg_confidence'] = (stats['avg_confidence'] + confidence) / 2
        
        stats['avg_latency'] = (stats['avg_latency'] + latency) / 2
    
    # Status and Health Check Methods
    
    def is_ready(self) -> bool:
        """Check if AI Engine is ready"""
        return self.is_initialized and all(
            model is not None for model in self.models.values()
        )
    
    async def get_status(self) -> Dict[str, Any]:
        """Get AI Engine status"""
        return {
            'initialized': self.is_initialized,
            'device': str(self.device),
            'models_loaded': list(self.models.keys()),
            'tokenizer_loaded': self.tokenizer is not None,
            'memory_usage': self._get_memory_usage(),
            'model_stats': self.model_stats,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage information"""
        if torch.cuda.is_available() and self.device.type == 'cuda':
            return {
                'gpu_memory_allocated': torch.cuda.memory_allocated() / 1024**3,  # GB
                'gpu_memory_reserved': torch.cuda.memory_reserved() / 1024**3,  # GB
                'gpu_memory_total': torch.cuda.get_device_properties(0).total_memory / 1024**3  # GB
            }
        else:
            import psutil
            return {
                'ram_usage_gb': psutil.virtual_memory().used / 1024**3,
                'ram_total_gb': psutil.virtual_memory().total / 1024**3
            }
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("🧹 Cleaning up AI Engine...")
        
        # Clear models from memory
        for model_name, model in self.models.items():
            if model is not None:
                del model
                logger.info(f"✅ {model_name} model cleared")
        
        self.models.clear()
        
        # Clear CUDA cache if using GPU
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        logger.info("✅ AI Engine cleanup completed")
