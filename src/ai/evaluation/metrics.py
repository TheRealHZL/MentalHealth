"""
Evaluation Metrics

Datenstrukturen für Evaluation-Metriken
"""

from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class EvaluationMetrics:
    """Container für alle Evaluation-Metriken"""
    
    # Text Quality Metrics
    perplexity: float
    bleu_score: float
    rouge_scores: Dict[str, float]
    semantic_similarity: float
    
    # Safety Metrics
    safety_score: float
    toxicity_score: float
    harmful_content_rate: float
    
    # Empathy Metrics
    empathy_score: float
    emotional_awareness: float
    supportiveness: float
    
    # Response Quality
    relevance_score: float
    coherence_score: float
    helpfulness_score: float
    
    # Performance Metrics
    response_time: float
    tokens_per_second: float
    memory_usage: float
    
    # Conversation Flow
    conversation_continuity: float
    context_retention: float
    turn_taking_quality: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary"""
        return {
            'text_quality': {
                'perplexity': self.perplexity,
                'bleu_score': self.bleu_score,
                'rouge_scores': self.rouge_scores,
                'semantic_similarity': self.semantic_similarity
            },
            'safety': {
                'safety_score': self.safety_score,
                'toxicity_score': self.toxicity_score,
                'harmful_content_rate': self.harmful_content_rate
            },
            'empathy': {
                'empathy_score': self.empathy_score,
                'emotional_awareness': self.emotional_awareness,
                'supportiveness': self.supportiveness
            },
            'response_quality': {
                'relevance_score': self.relevance_score,
                'coherence_score': self.coherence_score,
                'helpfulness_score': self.helpfulness_score
            },
            'performance': {
                'response_time': self.response_time,
                'tokens_per_second': self.tokens_per_second,
                'memory_usage': self.memory_usage
            },
            'conversation_flow': {
                'conversation_continuity': self.conversation_continuity,
                'context_retention': self.context_retention,
                'turn_taking_quality': self.turn_taking_quality
            }
        }
    
    def get_overall_score(self) -> float:
        """Berechnet Overall Quality Score"""
        weights = {
            'safety': 0.3,
            'empathy': 0.25,
            'helpfulness': 0.2,
            'relevance': 0.15,
            'coherence': 0.1
        }
        
        score = (
            weights['safety'] * self.safety_score +
            weights['empathy'] * self.empathy_score +
            weights['helpfulness'] * self.helpfulness_score +
            weights['relevance'] * self.relevance_score +
            weights['coherence'] * self.coherence_score
        )
        
        return min(max(score, 0.0), 1.0)
