"""
Empathy Evaluator

Evaluiert empathische Qualitäten von Chat-Antworten
"""

from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class EmpathyEvaluator:
    """
    Evaluiert empathische Qualitäten von Antworten
    """
    
    def __init__(self):
        self.empathy_indicators = {
            'emotional_validation': [
                'understand', 'feel', 'difficult', 'hard', 'challenging',
                'valid', 'normal', 'okay to feel', 'makes sense',
                'can imagine', 'sounds tough'
            ],
            'active_listening': [
                'hear you', 'sounds like', 'it seems', 'i can see',
                'what you\'re saying', 'from what you\'ve told me',
                'what i\'m hearing', 'it appears that'
            ],
            'support_offering': [
                'here for you', 'support you', 'help you', 'not alone',
                'we can work through', 'together', 'i\'m here',
                'you have support'
            ],
            'gentle_guidance': [
                'might consider', 'could try', 'perhaps', 'maybe',
                'one option', 'when you\'re ready', 'if you feel comfortable',
                'at your own pace'
            ],
            'professional_referral': [
                'professional', 'counselor', 'therapist', 'doctor',
                'mental health', 'seek help', 'professional help',
                'trained professional'
            ],
            'hope_instilling': [
                'things can get better', 'hope', 'positive change',
                'healing', 'recovery', 'brighter future',
                'overcome', 'strength'
            ]
        }
        
        self.emotion_recognition_keywords = [
            'sad', 'happy', 'angry', 'frustrated', 'anxious', 'worried',
            'excited', 'disappointed', 'hopeful', 'afraid', 'lonely',
            'overwhelmed', 'stressed', 'confused', 'hurt', 'grateful'
        ]
        
        self.empathy_detractors = [
            'just get over it', 'move on', 'stop complaining', 'not a big deal',
            'everyone has problems', 'you\'re overreacting', 'calm down',
            'it could be worse', 'think positive', 'just be happy'
        ]
    
    def evaluate_empathy(self, text: str, context: str = "") -> Dict[str, float]:
        """
        Evaluiert empathische Qualitäten einer Antwort
        
        Args:
            text: Generated response
            context: Previous conversation context
        
        Returns:
            Dictionary mit Empathy-Metriken
        """
        text_lower = text.lower()
        
        # Score für jede Empathy-Kategorie
        category_scores = {}
        matched_indicators = {}
        
        for category, indicators in self.empathy_indicators.items():
            score = 0.0
            matched = []
            
            for indicator in indicators:
                if indicator in text_lower:
                    score += 1.0
                    matched.append(indicator)
            
            # Normalisieren
            category_scores[category] = min(score / len(indicators), 1.0)
            matched_indicators[category] = matched
        
        # Gesamter Empathy Score
        empathy_score = sum(category_scores.values()) / len(category_scores)
        
        # Emotional Awareness (basierend auf Emotion-Keywords)
        emotion_awareness = self._evaluate_emotion_awareness(text_lower, context.lower())
        
        # Supportiveness (gewichtete Kombination)
        supportiveness = (
            category_scores.get('support_offering', 0.0) * 0.4 +
            category_scores.get('emotional_validation', 0.0) * 0.3 +
            category_scores.get('hope_instilling', 0.0) * 0.3
        )
        
        # Empathy Detractors Check
        detractor_penalty = self._check_empathy_detractors(text_lower)
        
        # Response appropriateness (Länge und Struktur)
        word_count = len(text.split())
        appropriate_length = self._evaluate_response_length(word_count)
        
        # Adjusted scores with penalties
        adjusted_empathy = max(0.0, empathy_score - detractor_penalty)
        adjusted_supportiveness = max(0.0, supportiveness - detractor_penalty)
        
        return {
            'empathy_score': adjusted_empathy,
            'emotional_awareness': emotion_awareness,
            'supportiveness': adjusted_supportiveness,
            'category_scores': category_scores,
            'matched_indicators': matched_indicators,
            'appropriate_length': appropriate_length,
            'word_count': word_count,
            'detractor_penalty': detractor_penalty,
            'overall_empathy_quality': self._calculate_overall_empathy(
                adjusted_empathy, emotion_awareness, adjusted_supportiveness, appropriate_length
            )
        }
    
    def _evaluate_emotion_awareness(self, text_lower: str, context_lower: str) -> float:
        """
        Evaluiert Emotional Awareness der Antwort
        
        Args:
            text_lower: Antwort-Text (lowercase)
            context_lower: Kontext (lowercase)
        
        Returns:
            Emotion awareness score (0-1)
        """
        
        # Erkannte Emotionen im Text
        recognized_emotions = []
        for emotion in self.emotion_recognition_keywords:
            if emotion in text_lower:
                recognized_emotions.append(emotion)
        
        # Basis-Score für erkannte Emotionen
        emotion_recognition_score = min(
            len(recognized_emotions) / len(self.emotion_recognition_keywords), 1.0
        )
        
        # Bonus für Kontext-relevante Emotionen
        context_emotion_bonus = 0.0
        if context_lower:
            context_emotions = [e for e in self.emotion_recognition_keywords if e in context_lower]
            response_emotions = recognized_emotions
            
            # Overlap zwischen Kontext- und Response-Emotionen
            emotion_overlap = len(set(context_emotions) & set(response_emotions))
            if context_emotions:
                context_emotion_bonus = emotion_overlap / len(context_emotions) * 0.3
        
        # Emotionale Tiefe (komplexere Emotionswörter)
        complex_emotions = [
            'overwhelmed', 'conflicted', 'ambivalent', 'vulnerable', 
            'resilient', 'validated', 'empowered', 'processing'
        ]
        
        complex_emotion_score = 0.0
        for emotion in complex_emotions:
            if emotion in text_lower:
                complex_emotion_score += 0.1
        
        complex_emotion_score = min(complex_emotion_score, 0.3)
        
        total_awareness = min(
            emotion_recognition_score + context_emotion_bonus + complex_emotion_score, 1.0
        )
        
        return total_awareness
    
    def _check_empathy_detractors(self, text_lower: str) -> float:
        """
        Überprüft auf empathy-schädliche Phrasen
        
        Args:
            text_lower: Text (lowercase)
        
        Returns:
            Penalty score (0-1, höher = mehr Penalty)
        """
        
        penalty = 0.0
        matched_detractors = []
        
        for detractor in self.empathy_detractors:
            if detractor in text_lower:
                penalty += 0.2  # Each detractor adds significant penalty
                matched_detractors.append(detractor)
        
        # Additional patterns that reduce empathy
        dismissive_patterns = [
            'just', 'simply', 'only', 'all you need to do',
            'it\'s easy', 'just do', 'stop being'
        ]
        
        for pattern in dismissive_patterns:
            if pattern in text_lower:
                penalty += 0.1
        
        return min(penalty, 1.0)
    
    def _evaluate_response_length(self, word_count: int) -> float:
        """
        Evaluiert Angemessenheit der Response-Länge
        
        Args:
            word_count: Anzahl Wörter
        
        Returns:
            Appropriateness score (0-1)
        """
        
        # Optimal range: 15-80 words for empathetic responses
        if 15 <= word_count <= 80:
            return 1.0
        elif 10 <= word_count < 15 or 80 < word_count <= 120:
            return 0.8
        elif 5 <= word_count < 10 or 120 < word_count <= 200:
            return 0.6
        elif word_count < 5:
            return 0.2  # Too short for empathy
        else:
            return 0.4  # Too long, potentially overwhelming
    
    def _calculate_overall_empathy(
        self, 
        empathy_score: float, 
        emotion_awareness: float, 
        supportiveness: float, 
        appropriate_length: float
    ) -> float:
        """
        Berechnet Overall Empathy Quality Score
        
        Args:
            empathy_score: Basis Empathy Score
            emotion_awareness: Emotional Awareness Score
            supportiveness: Supportiveness Score
            appropriate_length: Length Appropriateness Score
        
        Returns:
            Overall empathy quality (0-1)
        """
        
        weights = {
            'empathy': 0.4,
            'emotion_awareness': 0.25,
            'supportiveness': 0.25,
            'length': 0.1
        }
        
        overall = (
            weights['empathy'] * empathy_score +
            weights['emotion_awareness'] * emotion_awareness +
            weights['supportiveness'] * supportiveness +
            weights['length'] * appropriate_length
        )
        
        return min(max(overall, 0.0), 1.0)
    
    def evaluate_empathy_progression(self, conversation_history: List[str]) -> Dict[str, float]:
        """
        Evaluiert Empathy-Entwicklung über Conversation hinweg
        
        Args:
            conversation_history: Liste von Bot-Responses in chronologischer Reihenfolge
        
        Returns:
            Dictionary mit Progression-Metriken
        """
        
        if len(conversation_history) < 2:
            return {'progression_score': 1.0, 'consistency_score': 1.0}
        
        empathy_scores = []
        supportiveness_scores = []
        
        for response in conversation_history:
            metrics = self.evaluate_empathy(response)
            empathy_scores.append(metrics['empathy_score'])
            supportiveness_scores.append(metrics['supportiveness'])
        
        # Progression: Verbesserung über Zeit
        empathy_trend = self._calculate_trend(empathy_scores)
        support_trend = self._calculate_trend(supportiveness_scores)
        
        # Consistency: Stabilität der Empathy
        empathy_consistency = 1.0 - (max(empathy_scores) - min(empathy_scores))
        support_consistency = 1.0 - (max(supportiveness_scores) - min(supportiveness_scores))
        
        progression_score = (empathy_trend + support_trend) / 2
        consistency_score = (empathy_consistency + support_consistency) / 2
        
        return {
            'progression_score': max(0.0, min(progression_score, 1.0)),
            'consistency_score': max(0.0, min(consistency_score, 1.0)),
            'empathy_trend': empathy_trend,
            'support_trend': support_trend,
            'avg_empathy': sum(empathy_scores) / len(empathy_scores),
            'avg_supportiveness': sum(supportiveness_scores) / len(supportiveness_scores)
        }
    
    def _calculate_trend(self, scores: List[float]) -> float:
        """
        Berechnet Trend in Score-Liste
        
        Args:
            scores: Liste von Scores
        
        Returns:
            Trend score (-1 to 1, positive = improving)
        """
        
        if len(scores) < 2:
            return 0.0
        
        # Simple linear trend
        n = len(scores)
        x = list(range(n))
        
        # Linear regression slope
        x_mean = sum(x) / n
        y_mean = sum(scores) / n
        
        numerator = sum((x[i] - x_mean) * (scores[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        slope = numerator / denominator
        
        # Normalize slope to [-1, 1] range
        # Assuming max reasonable slope is 0.5 (improving by 0.5 per turn)
        normalized_slope = max(-1.0, min(slope / 0.5, 1.0))
        
        return normalized_slope
    
    def get_empathy_recommendations(self, evaluation_results: Dict[str, float]) -> List[str]:
        """
        Generiert Empfehlungen zur Verbesserung der Empathy
        
        Args:
            evaluation_results: Ergebnisse der Empathy-Evaluation
        
        Returns:
            Liste von Empfehlungen
        """
        
        recommendations = []
        
        # Low overall empathy
        if evaluation_results['empathy_score'] < 0.5:
            recommendations.append("Increase use of validating language")
            recommendations.append("Add more emotional acknowledgment")
        
        # Low emotional awareness
        if evaluation_results['emotional_awareness'] < 0.4:
            recommendations.append("Recognize and name emotions explicitly")
            recommendations.append("Reflect back emotional content from user")
        
        # Low supportiveness
        if evaluation_results['supportiveness'] < 0.5:
            recommendations.append("Offer more concrete support")
            recommendations.append("Use encouraging and hope-instilling language")
        
        # Inappropriate length
        if evaluation_results['appropriate_length'] < 0.7:
            if evaluation_results['word_count'] < 10:
                recommendations.append("Expand response length for better empathy")
            else:
                recommendations.append("Make response more concise and focused")
        
        # High detractor penalty
        if evaluation_results['detractor_penalty'] > 0.3:
            recommendations.append("Remove dismissive or minimizing language")
            recommendations.append("Avoid solution-focused responses without validation")
        
        # Missing key empathy components
        category_scores = evaluation_results['category_scores']
        
        if category_scores.get('emotional_validation', 0) < 0.3:
            recommendations.append("Add emotional validation phrases")
        
        if category_scores.get('active_listening', 0) < 0.3:
            recommendations.append("Include active listening reflections")
        
        if category_scores.get('professional_referral', 0) < 0.2:
            recommendations.append("Consider professional referral when appropriate")
        
        return recommendations
