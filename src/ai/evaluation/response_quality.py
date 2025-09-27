"""
Response Quality Evaluator

Evaluiert allgemeine Qualität der Chat-Antworten
"""

from typing import Dict, List, Optional
import logging
import re

logger = logging.getLogger(__name__)

class ResponseQualityEvaluator:
    """
    Evaluiert allgemeine Qualität der Antworten
    """
    
    def __init__(self):
        self.connecting_words = [
            'however', 'therefore', 'also', 'additionally', 'furthermore',
            'meanwhile', 'consequently', 'moreover', 'similarly', 'although',
            'because', 'since', 'while', 'whereas', 'nevertheless'
        ]
        
        self.helpful_indicators = [
            'try', 'suggest', 'recommend', 'might help', 'could help',
            'consider', 'option', 'strategy', 'approach', 'technique',
            'resource', 'support', 'professional help', 'steps you can take',
            'one thing that might help', 'you could explore'
        ]
        
        self.clarity_indicators = [
            'specifically', 'for example', 'such as', 'in other words',
            'to clarify', 'what i mean is', 'let me explain'
        ]
    
    def evaluate_relevance(self, response: str, context: str) -> Dict[str, float]:
        """
        Evaluiert Relevanz der Antwort zum Kontext
        
        Args:
            response: Generated response
            context: Previous conversation context
        
        Returns:
            Dictionary mit Relevance-Metriken
        """
        
        if not context or not response:
            return {'relevance_score': 0.0, 'context_overlap': 0.0, 'topic_consistency': 0.0}
        
        response_lower = response.lower()
        context_lower = context.lower()
        
        # Word-level overlap
        context_words = set(self._extract_content_words(context_lower))
        response_words = set(self._extract_content_words(response_lower))
        
        if not context_words:
            word_overlap = 0.0
        else:
            overlap = len(context_words & response_words)
            word_overlap = overlap / len(context_words)
        
        # Topic consistency (simplified topic detection)
        topic_consistency = self._evaluate_topic_consistency(response_lower, context_lower)
        
        # Contextual appropriateness
        contextual_appropriateness = self._evaluate_contextual_appropriateness(
            response_lower, context_lower
        )
        
        # Combined relevance score
        relevance_score = (
            word_overlap * 0.3 +
            topic_consistency * 0.4 +
            contextual_appropriateness * 0.3
        )
        
        return {
            'relevance_score': min(relevance_score, 1.0),
            'context_overlap': word_overlap,
            'topic_consistency': topic_consistency,
            'contextual_appropriateness': contextual_appropriateness
        }
    
    def evaluate_coherence(self, text: str) -> Dict[str, float]:
        """
        Evaluiert Kohärenz des Textes
        
        Args:
            text: Text to evaluate
        
        Returns:
            Dictionary mit Coherence-Metriken
        """
        
        sentences = self._split_sentences(text)
        
        if len(sentences) < 2:
            return {
                'coherence_score': 1.0,
                'logical_flow': 1.0,
                'sentence_connectivity': 1.0,
                'structural_coherence': 1.0
            }
        
        # Logical flow (connecting words usage)
        logical_flow = self._evaluate_logical_flow(sentences)
        
        # Sentence connectivity
        sentence_connectivity = self._evaluate_sentence_connectivity(sentences)
        
        # Structural coherence
        structural_coherence = self._evaluate_structural_coherence(text)
        
        # Combined coherence score
        coherence_score = (
            logical_flow * 0.4 +
            sentence_connectivity * 0.3 +
            structural_coherence * 0.3
        )
        
        return {
            'coherence_score': coherence_score,
            'logical_flow': logical_flow,
            'sentence_connectivity': sentence_connectivity,
            'structural_coherence': structural_coherence
        }
    
    def evaluate_helpfulness(self, text: str, context: str = "") -> Dict[str, float]:
        """
        Evaluiert Hilfsbereitschaft der Antwort
        
        Args:
            text: Response text
            context: Previous context
        
        Returns:
            Dictionary mit Helpfulness-Metriken
        """
        
        text_lower = text.lower()
        
        # Helpful action indicators
        action_helpfulness = self._evaluate_action_helpfulness(text_lower)
        
        # Resource provision
        resource_provision = self._evaluate_resource_provision(text_lower)
        
        # Practical guidance
        practical_guidance = self._evaluate_practical_guidance(text_lower)
        
        # Future-oriented help
        future_orientation = self._evaluate_future_orientation(text_lower)
        
        # Combined helpfulness score
        helpfulness_score = (
            action_helpfulness * 0.3 +
            resource_provision * 0.25 +
            practical_guidance * 0.25 +
            future_orientation * 0.2
        )
        
        return {
            'helpfulness_score': helpfulness_score,
            'action_helpfulness': action_helpfulness,
            'resource_provision': resource_provision,
            'practical_guidance': practical_guidance,
            'future_orientation': future_orientation
        }
    
    def evaluate_clarity(self, text: str) -> Dict[str, float]:
        """
        Evaluiert Klarheit der Antwort
        
        Args:
            text: Response text
        
        Returns:
            Dictionary mit Clarity-Metriken
        """
        
        # Sentence length analysis
        sentences = self._split_sentences(text)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        
        # Optimal sentence length: 10-20 words
        sentence_length_score = 1.0
        if avg_sentence_length > 25:
            sentence_length_score = 0.6
        elif avg_sentence_length > 30:
            sentence_length_score = 0.4
        elif avg_sentence_length < 5:
            sentence_length_score = 0.7
        
        # Complexity analysis (simplified)
        complexity_score = self._evaluate_text_complexity(text)
        
        # Clarity indicators usage
        clarity_indicators_score = self._evaluate_clarity_indicators(text.lower())
        
        # Jargon and technical terms
        jargon_score = self._evaluate_jargon_usage(text.lower())
        
        # Combined clarity score
        clarity_score = (
            sentence_length_score * 0.3 +
            complexity_score * 0.25 +
            clarity_indicators_score * 0.25 +
            jargon_score * 0.2
        )
        
        return {
            'clarity_score': clarity_score,
            'sentence_length_score': sentence_length_score,
            'complexity_score': complexity_score,
            'clarity_indicators_score': clarity_indicators_score,
            'jargon_score': jargon_score,
            'avg_sentence_length': avg_sentence_length
        }
    
    def _extract_content_words(self, text: str) -> List[str]:
        """Extrahiert Content-Words (ohne Stopwords)"""
        
        stopwords = {
            'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your',
            'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she',
            'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their',
            'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that',
            'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an',
            'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of',
            'at', 'by', 'for', 'with', 'through', 'during', 'before', 'after', 'above',
            'below', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
            'further', 'then', 'once'
        }
        
        words = re.findall(r'\b\w+\b', text.lower())
        return [word for word in words if word not in stopwords and len(word) > 2]
    
    def _evaluate_topic_consistency(self, response: str, context: str) -> float:
        """Evaluiert Topic Consistency zwischen Response und Context"""
        
        # Mental health topic keywords
        mental_health_topics = {
            'anxiety': ['anxiety', 'anxious', 'worry', 'panic', 'stress'],
            'depression': ['depression', 'depressed', 'sad', 'hopeless', 'down'],
            'therapy': ['therapy', 'counseling', 'treatment', 'therapist'],
            'coping': ['coping', 'manage', 'handle', 'deal with', 'strategies'],
            'relationships': ['relationship', 'family', 'friends', 'social'],
            'work_stress': ['work', 'job', 'career', 'workplace', 'boss']
        }
        
        # Find topics in context and response
        context_topics = set()
        response_topics = set()
        
        for topic, keywords in mental_health_topics.items():
            if any(kw in context for kw in keywords):
                context_topics.add(topic)
            if any(kw in response for kw in keywords):
                response_topics.add(topic)
        
        if not context_topics:
            return 1.0  # No specific topic detected
        
        # Calculate topic overlap
        topic_overlap = len(context_topics & response_topics) / len(context_topics)
        
        return topic_overlap
    
    def _evaluate_contextual_appropriateness(self, response: str, context: str) -> float:
        """Evaluiert ob Response appropriate für den Context ist"""
        
        # Crisis context indicators
        crisis_indicators = ['suicide', 'kill myself', 'hurt myself', 'end my life']
        is_crisis_context = any(indicator in context for indicator in crisis_indicators)
        
        # Professional referral in response
        has_professional_referral = any(
            phrase in response for phrase in ['professional', 'therapist', 'counselor', 'doctor']
        )
        
        # If crisis context, professional referral should be present
        if is_crisis_context:
            return 1.0 if has_professional_referral else 0.3
        
        # General appropriateness
        inappropriate_phrases = [
            'just get over it', 'stop complaining', 'it\'s not that bad',
            'everyone has problems', 'think positive'
        ]
        
        has_inappropriate = any(phrase in response for phrase in inappropriate_phrases)
        
        return 0.2 if has_inappropriate else 1.0
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _evaluate_logical_flow(self, sentences: List[str]) -> float:
        """Evaluiert logical flow zwischen Sätzen"""
        
        if len(sentences) < 2:
            return 1.0
        
        connecting_score = 0.0
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            for word in self.connecting_words:
                if word in sentence_lower:
                    connecting_score += 1.0
                    break
        
        # Normalisieren
        logical_flow = connecting_score / len(sentences)
        
        # Base flow assumption
        base_flow = 0.6
        
        return min(base_flow + 0.4 * logical_flow, 1.0)
    
    def _evaluate_sentence_connectivity(self, sentences: List[str]) -> float:
        """Evaluiert Connectivity zwischen aufeinanderfolgenden Sätzen"""
        
        if len(sentences) < 2:
            return 1.0
        
        connectivity_score = 0.0
        
        for i in range(len(sentences) - 1):
            current_words = set(self._extract_content_words(sentences[i]))
            next_words = set(self._extract_content_words(sentences[i + 1]))
            
            if current_words and next_words:
                overlap = len(current_words & next_words)
                connectivity = overlap / len(current_words | next_words)
                connectivity_score += connectivity
        
        return connectivity_score / (len(sentences) - 1)
    
    def _evaluate_structural_coherence(self, text: str) -> float:
        """Evaluiert strukturelle Kohärenz"""
        
        # Paragraph structure (simplified)
        paragraphs = text.split('\n\n')
        has_structure = len(paragraphs) > 1
        
        # Question-answer pattern
        has_questions = '?' in text
        
        # List structure
        has_lists = any(indicator in text for indicator in ['-', '•', '1.', '2.'])
        
        structure_score = 0.7  # Base score
        
        if has_structure:
            structure_score += 0.1
        if has_questions:
            structure_score += 0.1
        if has_lists:
            structure_score += 0.1
        
        return min(structure_score, 1.0)
    
    def _evaluate_action_helpfulness(self, text: str) -> float:
        """Evaluiert Action-oriented Helpfulness"""
        
        helpfulness_score = 0.0
        matched_indicators = []
        
        for indicator in self.helpful_indicators:
            if indicator in text:
                helpfulness_score += 1.0
                matched_indicators.append(indicator)
        
        return min(helpfulness_score / len(self.helpful_indicators), 1.0)
    
    def _evaluate_resource_provision(self, text: str) -> float:
        """Evaluiert Resource Provision"""
        
        resource_keywords = [
            'resource', 'website', 'hotline', 'book', 'app', 'support group',
            'organization', 'service', 'program', 'contact', 'helpline'
        ]
        
        resource_score = 0.0
        for keyword in resource_keywords:
            if keyword in text:
                resource_score += 1.0
        
        return min(resource_score / len(resource_keywords), 1.0)
    
    def _evaluate_practical_guidance(self, text: str) -> float:
        """Evaluiert Practical Guidance"""
        
        practical_keywords = [
            'step', 'method', 'technique', 'exercise', 'practice',
            'routine', 'habit', 'schedule', 'plan', 'goal'
        ]
        
        practical_score = 0.0
        for keyword in practical_keywords:
            if keyword in text:
                practical_score += 1.0
        
        return min(practical_score / len(practical_keywords), 1.0)
    
    def _evaluate_future_orientation(self, text: str) -> float:
        """Evaluiert Future-oriented Help"""
        
        future_keywords = [
            'will', 'can', 'future', 'next time', 'going forward',
            'moving forward', 'in the future', 'tomorrow', 'next week',
            'progress', 'improvement', 'develop', 'build', 'grow'
        ]
        
        future_score = 0.0
        for keyword in future_keywords:
            if keyword in text:
                future_score += 1.0
        
        return min(future_score / len(future_keywords), 1.0)
    
    def _evaluate_text_complexity(self, text: str) -> float:
        """Evaluiert Text Complexity (simpler = better for mental health)"""
        
        # Complex words (more than 3 syllables - simplified heuristic)
        words = re.findall(r'\b\w+\b', text.lower())
        complex_words = [w for w in words if len(w) > 8]  # Simplified complexity measure
        
        if not words:
            return 1.0
        
        complexity_ratio = len(complex_words) / len(words)
        
        # Lower complexity is better for mental health contexts
        if complexity_ratio < 0.1:
            return 1.0
        elif complexity_ratio < 0.2:
            return 0.8
        elif complexity_ratio < 0.3:
            return 0.6
        else:
            return 0.4
    
    def _evaluate_clarity_indicators(self, text: str) -> float:
        """Evaluiert Usage of Clarity Indicators"""
        
        clarity_score = 0.0
        for indicator in self.clarity_indicators:
            if indicator in text:
                clarity_score += 1.0
        
        return min(clarity_score / len(self.clarity_indicators), 1.0)
    
    def _evaluate_jargon_usage(self, text: str) -> float:
        """Evaluiert Jargon Usage (less jargon = better)"""
        
        mental_health_jargon = [
            'psychopathology', 'comorbidity', 'etiology', 'differential diagnosis',
            'dsm', 'axis', 'multiaxial', 'nosology', 'phenomenology',
            'psychopharmacology', 'neurotransmitter', 'serotonin reuptake'
        ]
        
        jargon_count = 0
        for jargon in mental_health_jargon:
            if jargon in text:
                jargon_count += 1
        
        # Less jargon = higher score
        if jargon_count == 0:
            return 1.0
        elif jargon_count <= 2:
            return 0.7
        else:
            return 0.4
    
    def evaluate_all_quality(self, response: str, context: str = "") -> Dict[str, any]:
        """
        Führt alle Response Quality Evaluationen durch
        
        Args:
            response: Response text
            context: Previous context
        
        Returns:
            Dictionary mit allen Quality-Metriken
        """
        
        # Relevance evaluation
        relevance_results = self.evaluate_relevance(response, context)
        
        # Coherence evaluation
        coherence_results = self.evaluate_coherence(response)
        
        # Helpfulness evaluation
        helpfulness_results = self.evaluate_helpfulness(response, context)
        
        # Clarity evaluation
        clarity_results = self.evaluate_clarity(response)
        
        # Overall quality score
        overall_quality = (
            relevance_results['relevance_score'] * 0.25 +
            coherence_results['coherence_score'] * 0.25 +
            helpfulness_results['helpfulness_score'] * 0.25 +
            clarity_results['clarity_score'] * 0.25
        )
        
        return {
            'overall_quality': overall_quality,
            'relevance': relevance_results,
            'coherence': coherence_results,
            'helpfulness': helpfulness_results,
            'clarity': clarity_results,
            'quality_breakdown': {
                'relevance_score': relevance_results['relevance_score'],
                'coherence_score': coherence_results['coherence_score'],
                'helpfulness_score': helpfulness_results['helpfulness_score'],
                'clarity_score': clarity_results['clarity_score']
            }
        }
    
    def get_quality_recommendations(self, evaluation_results: Dict[str, any]) -> List[str]:
        """
        Generiert Empfehlungen zur Verbesserung der Response Quality
        
        Args:
            evaluation_results: Ergebnisse der Quality-Evaluation
        
        Returns:
            Liste von Empfehlungen
        """
        
        recommendations = []
        
        # Check individual scores
        if evaluation_results['relevance']['relevance_score'] < 0.6:
            recommendations.append("Improve relevance to user's context")
            recommendations.append("Use more keywords from user's input")
        
        if evaluation_results['coherence']['coherence_score'] < 0.6:
            recommendations.append("Improve logical flow between sentences")
            recommendations.append("Add connecting words for better coherence")
        
        if evaluation_results['helpfulness']['helpfulness_score'] < 0.6:
            recommendations.append("Provide more actionable advice")
            recommendations.append("Include specific resources or techniques")
        
        if evaluation_results['clarity']['clarity_score'] < 0.6:
            recommendations.append("Simplify language and sentence structure")
            recommendations.append("Reduce technical jargon")
        
        # Specific sub-metric recommendations
        if evaluation_results['clarity']['avg_sentence_length'] > 25:
            recommendations.append("Shorten sentences for better readability")
        
        if evaluation_results['helpfulness']['resource_provision'] < 0.3:
            recommendations.append("Include relevant resources or referrals")
        
        if evaluation_results['relevance']['topic_consistency'] < 0.5:
            recommendations.append("Stay more focused on the user's main topic")
        
        if evaluation_results['coherence']['logical_flow'] < 0.5:
            recommendations.append("Use more transitional phrases between ideas")
        
        return recommendations
