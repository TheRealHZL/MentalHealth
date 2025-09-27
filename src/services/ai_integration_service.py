"""
AI Integration Service - Custom AI Analysis

Nutzt unsere eigenen AI-Modelle für echte Analysen statt vorgefertigter Texte.
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from src.models import MoodEntry, DreamEntry, TherapyNote

logger = logging.getLogger(__name__)

class AIIntegrationService:
    """Integration mit unserer Custom AI Engine"""
    
    def __init__(self, ai_engine):
        self.ai_engine = ai_engine
    
    async def analyze_mood_entry(self, mood_entry: MoodEntry) -> Dict[str, Any]:
        """Echte AI-Analyse des Mood Entries mit unseren Modellen"""
        
        # Text für AI-Analyse zusammenstellen
        analysis_text = self._build_mood_analysis_text(mood_entry)
        
        try:
            # Emotion Detection
            emotion_result = await self.ai_engine.predict_emotion(
                text=analysis_text,
                context={
                    "mood_score": mood_entry.mood_score,
                    "stress_level": mood_entry.stress_level,
                    "sleep_quality": mood_entry.sleep_quality
                }
            )
            
            # Sentiment Analysis
            sentiment_result = await self.ai_engine.analyze_sentiment(analysis_text)
            
            # Mood Prediction für Trend
            mood_prediction = await self.ai_engine.predict_mood(
                text=analysis_text,
                metadata={
                    "sleep_hours": mood_entry.sleep_hours,
                    "exercise_minutes": mood_entry.exercise_minutes,
                    "stress_level": mood_entry.stress_level
                }
            )
            
            # AI-generierte Insights
            insights_prompt = self._build_insights_prompt(mood_entry, emotion_result, sentiment_result)
            insights_response = await self.ai_engine.generate_chat_response(
                user_message=insights_prompt,
                user_context={
                    "mode": "analysis",
                    "emotion": emotion_result["emotion"],
                    "sentiment": sentiment_result["sentiment"]
                }
            )
            
            return {
                "ai_generated": True,
                "emotion_analysis": emotion_result,
                "sentiment_analysis": sentiment_result,
                "mood_prediction": mood_prediction,
                "ai_insights": insights_response["response"],
                "confidence_score": (
                    emotion_result["confidence"] + 
                    sentiment_result["confidence"] + 
                    mood_prediction["confidence"]
                ) / 3,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return {
                "ai_generated": False,
                "error": "AI-Analyse temporär nicht verfügbar",
                "fallback_analysis": self._get_basic_analysis(mood_entry)
            }
    
    async def analyze_dream_entry(self, dream_entry: DreamEntry) -> Dict[str, Any]:
        """AI-Analyse des Traumeintrags"""
        
        dream_text = f"{dream_entry.title or ''} {dream_entry.description}"
        
        try:
            # Emotion in Dream
            dream_emotion = await self.ai_engine.predict_emotion(
                text=dream_text,
                context={"type": "dream_content"}
            )
            
            # Sentiment of Dream
            dream_sentiment = await self.ai_engine.analyze_sentiment(dream_text)
            
            # AI Dream Interpretation
            interpretation_prompt = self._build_dream_interpretation_prompt(dream_entry)
            interpretation_response = await self.ai_engine.generate_chat_response(
                user_message=interpretation_prompt,
                user_context={
                    "mode": "dream_analysis",
                    "dream_type": dream_entry.dream_type.value,
                    "mood_after": dream_entry.mood_after_waking
                }
            )
            
            # Symbol Analysis (if symbols present)
            symbol_analysis = {}
            if dream_entry.symbols:
                for symbol in dream_entry.symbols[:3]:  # Limit to 3 symbols
                    symbol_prompt = f"Was könnte das Symbol '{symbol}' in einem Traum bedeuten? Kurze psychologische Interpretation."
                    symbol_response = await self.ai_engine.generate_chat_response(
                        user_message=symbol_prompt,
                        user_context={"mode": "symbol_analysis"}
                    )
                    symbol_analysis[symbol] = symbol_response["response"]
            
            return {
                "ai_generated": True,
                "dream_emotion": dream_emotion,
                "dream_sentiment": dream_sentiment,
                "ai_interpretation": interpretation_response["response"],
                "symbol_meanings": symbol_analysis,
                "psychological_insights": await self._generate_dream_insights(dream_entry, dream_emotion),
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Dream AI analysis failed: {e}")
            return {"ai_generated": False, "error": "AI-Traumanalyse nicht verfügbar"}
    
    async def analyze_therapy_note(self, therapy_note: TherapyNote) -> Dict[str, Any]:
        """AI-Analyse der Therapie-Notiz"""
        
        note_text = f"{therapy_note.title} {therapy_note.content}"
        
        try:
            # Emotional State Analysis
            note_emotion = await self.ai_engine.predict_emotion(
                text=note_text,
                context={"type": "therapy_note"}
            )
            
            # Progress Analysis
            progress_prompt = self._build_progress_analysis_prompt(therapy_note)
            progress_response = await self.ai_engine.generate_chat_response(
                user_message=progress_prompt,
                user_context={
                    "mode": "therapy_analysis",
                    "note_type": therapy_note.note_type.value
                }
            )
            
            # Goal Achievement Assessment
            if therapy_note.goals_discussed:
                goal_assessment = await self._analyze_goal_progress(therapy_note)
            else:
                goal_assessment = None
            
            return {
                "ai_generated": True,
                "emotional_analysis": note_emotion,
                "progress_insights": progress_response["response"],
                "goal_assessment": goal_assessment,
                "suggested_next_steps": await self._suggest_therapy_next_steps(therapy_note),
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Therapy note AI analysis failed: {e}")
            return {"ai_generated": False, "error": "AI-Therapieanalyse nicht verfügbar"}
    
    async def generate_personalized_insights(
        self, 
        user_id: str, 
        recent_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generiert personalisierte Insights basierend auf allen Daten"""
        
        try:
            # Comprehensive analysis prompt
            insights_prompt = self._build_comprehensive_insights_prompt(recent_data)
            
            # AI-generierte Insights
            insights_response = await self.ai_engine.generate_chat_response(
                user_message=insights_prompt,
                user_context={
                    "mode": "comprehensive_analysis",
                    "user_id": user_id,
                    "data_timeframe": "recent"
                }
            )
            
            # Mood prediction für nächste Tage
            mood_forecast = await self.ai_engine.predict_mood(
                text=insights_prompt,
                metadata=recent_data.get("metadata", {})
            )
            
            return {
                "ai_generated": True,
                "personalized_insights": insights_response["response"],
                "mood_forecast": mood_forecast,
                "ai_recommendations": await self._generate_ai_recommendations(recent_data),
                "confidence": insights_response.get("confidence", 0.8),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Personalized insights generation failed: {e}")
            return {"ai_generated": False, "error": "Personalisierte Insights nicht verfügbar"}
    
    # =============================================================================
    # Prompt Building Methods
    # =============================================================================
    
    def _build_mood_analysis_text(self, mood_entry: MoodEntry) -> str:
        """Erstellt Text für Mood-Analyse"""
        
        parts = [f"Stimmung: {mood_entry.mood_score}/10"]
        
        if mood_entry.notes:
            parts.append(f"Notizen: {mood_entry.notes}")
        
        if mood_entry.activities:
            parts.append(f"Aktivitäten: {', '.join(mood_entry.activities)}")
        
        if mood_entry.symptoms:
            parts.append(f"Symptome: {', '.join(mood_entry.symptoms)}")
        
        if mood_entry.triggers:
            parts.append(f"Auslöser: {', '.join(mood_entry.triggers)}")
        
        parts.append(f"Stress: {mood_entry.stress_level}/10")
        parts.append(f"Energie: {mood_entry.energy_level}/10") 
        parts.append(f"Schlaf: {mood_entry.sleep_hours}h, Qualität: {mood_entry.sleep_quality}/10")
        
        return " | ".join(parts)
    
    def _build_insights_prompt(
        self, 
        mood_entry: MoodEntry, 
        emotion_result: Dict, 
        sentiment_result: Dict
    ) -> str:
        """Erstellt Prompt für AI-Insights"""
        
        return f"""Analysiere diesen Stimmungseintrag und gib kurze, hilfreiche Insights:

Stimmung: {mood_entry.mood_score}/10
Emotion: {emotion_result['emotion']} (Vertrauen: {emotion_result['confidence']:.1f})
Sentiment: {sentiment_result['sentiment']}
Stress: {mood_entry.stress_level}/10
Schlaf: {mood_entry.sleep_hours}h
Notizen: {mood_entry.notes or 'Keine'}

Gib 2-3 kurze, empathische Insights und einen praktischen Tipp. Sei unterstützend und ermutigend."""
    
    def _build_dream_interpretation_prompt(self, dream_entry: DreamEntry) -> str:
        """Erstellt Prompt für Traumdeutung"""
        
        return f"""Interpretiere diesen Traum aus psychologischer Sicht:

Titel: {dream_entry.title or 'Kein Titel'}
Beschreibung: {dream_entry.description}
Traumart: {dream_entry.dream_type.value}
Stimmung nach dem Aufwachen: {dream_entry.mood_after_waking}/10
Personen: {', '.join(dream_entry.people_in_dream) if dream_entry.people_in_dream else 'Keine'}
Orte: {', '.join(dream_entry.locations) if dream_entry.locations else 'Keine'}
Symbole: {', '.join(dream_entry.symbols) if dream_entry.symbols else 'Keine'}

Gib eine einfühlsame, psychologisch fundierte Interpretation. Sei vorsichtig und ermutigend."""
    
    def _build_progress_analysis_prompt(self, therapy_note: TherapyNote) -> str:
        """Erstellt Prompt für Fortschrittsanalyse"""
        
        return f"""Analysiere diese Therapie-Notiz auf Fortschritte und Erkenntnisse:

Typ: {therapy_note.note_type.value}
Titel: {therapy_note.title}
Inhalt: {therapy_note.content}
Techniken: {', '.join(therapy_note.techniques_used) if therapy_note.techniques_used else 'Keine'}
Ziele: {', '.join(therapy_note.goals_discussed) if therapy_note.goals_discussed else 'Keine'}
Herausforderungen: {', '.join(therapy_note.challenges_faced) if therapy_note.challenges_faced else 'Keine'}
Erkenntnisse: {therapy_note.key_insights or 'Keine'}

Erkenne Fortschritte, Muster und gib ermutigende Rückmeldung."""
    
    def _build_comprehensive_insights_prompt(self, recent_data: Dict[str, Any]) -> str:
        """Erstellt umfassenden Insights-Prompt"""
        
        mood_summary = recent_data.get("mood_summary", "Keine Stimmungsdaten")
        dream_summary = recent_data.get("dream_summary", "Keine Traumdaten") 
        therapy_summary = recent_data.get("therapy_summary", "Keine Therapiedaten")
        
        return f"""Erstelle personalisierte Insights basierend auf den letzten Einträgen:

STIMMUNGSDATEN:
{mood_summary}

TRAUMDATEN:
{dream_summary}

THERAPIEDATEN:
{therapy_summary}

Identifiziere Muster, Fortschritte und Bereiche für Verbesserung. Gib konkrete, umsetzbare Empfehlungen für die mentale Gesundheit."""
    
    # =============================================================================
    # Helper Methods
    # =============================================================================
    
    def _get_basic_analysis(self, mood_entry: MoodEntry) -> Dict[str, Any]:
        """Fallback-Analyse wenn AI nicht verfügbar"""
        
        return {
            "mood_category": "niedrig" if mood_entry.mood_score <= 4 else "hoch" if mood_entry.mood_score >= 7 else "moderat",
            "stress_assessment": "hoch" if mood_entry.stress_level >= 7 else "niedrig" if mood_entry.stress_level <= 3 else "moderat",
            "basic_recommendation": "Achte heute besonders auf Selbstfürsorge." if mood_entry.mood_score <= 4 else "Nutze diese positive Energie!"
        }
    
    async def _generate_dream_insights(self, dream_entry: DreamEntry, emotion_result: Dict) -> List[str]:
        """Generiert psychologische Dream-Insights"""
        
        insights = []
        
        if dream_entry.dream_type.value == "nightmare":
            nightmare_prompt = f"Was kann ein Albtraum mit der Emotion '{emotion_result['emotion']}' bedeuten? Kurzer psychologischer Einblick."
            response = await self.ai_engine.generate_chat_response(
                user_message=nightmare_prompt,
                user_context={"mode": "psychological_insight"}
            )
            insights.append(response["response"])
        
        return insights
    
    async def _analyze_goal_progress(self, therapy_note: TherapyNote) -> Dict[str, Any]:
        """Analysiert Zielerreichung"""
        
        if not therapy_note.goals_discussed:
            return None
        
        progress_prompt = f"Bewerte den Fortschritt bei diesen Therapiezielen: {', '.join(therapy_note.goals_discussed)}. Basierend auf: {therapy_note.progress_made or 'Keine Angaben'}"
        
        response = await self.ai_engine.generate_chat_response(
            user_message=progress_prompt,
            user_context={"mode": "goal_assessment"}
        )
        
        return {
            "assessment": response["response"],
            "confidence": response.get("confidence", 0.7)
        }
    
    async def _suggest_therapy_next_steps(self, therapy_note: TherapyNote) -> List[str]:
        """Schlägt nächste Therapieschritte vor"""
        
        prompt = f"Schlage 2-3 nächste Schritte vor basierend auf dieser Therapie-Sitzung: {therapy_note.content[:200]}..."
        
        response = await self.ai_engine.generate_chat_response(
            user_message=prompt,
            user_context={"mode": "therapy_planning"}
        )
        
        # Parse response in Liste (vereinfacht)
        return [step.strip() for step in response["response"].split('\n') if step.strip()][:3]
    
    async def _generate_ai_recommendations(self, recent_data: Dict[str, Any]) -> List[str]:
        """Generiert AI-basierte Empfehlungen"""
        
        recommendations_prompt = f"Gib 3 konkrete Empfehlungen für die mentale Gesundheit basierend auf: {str(recent_data)[:300]}"
        
        response = await self.ai_engine.generate_chat_response(
            user_message=recommendations_prompt,
            user_context={"mode": "recommendations"}
        )
        
        # Parse recommendations
        return [rec.strip() for rec in response["response"].split('\n') if rec.strip()][:3]
