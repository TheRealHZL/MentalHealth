"""
Main Chat Model Evaluator

Hauptklasse für umfassende Chat Model Evaluation
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import torch
import torch.nn as nn

from .empathy import EmpathyEvaluator
from .metrics import EvaluationMetrics
from .performance import PerformanceEvaluator
from .response_quality import ResponseQualityEvaluator
from .safety import SafetyEvaluator
from .text_quality import TextQualityEvaluator

logger = logging.getLogger(__name__)


class ChatModelEvaluator:
    """
    Hauptklasse für Chat Model Evaluation
    """

    def __init__(
        self,
        model: Optional[nn.Module] = None,
        tokenizer: Optional[Any] = None,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.device = device

        # Sub-evaluators
        self.text_quality_eval = TextQualityEvaluator()
        self.safety_eval = SafetyEvaluator()
        self.empathy_eval = EmpathyEvaluator()
        self.quality_eval = ResponseQualityEvaluator()
        self.performance_eval = PerformanceEvaluator()

        # Evaluation history
        self.evaluation_history = []

        logger.info(f"🔍 ChatModelEvaluator initialized on device: {device}")

    def evaluate_single_response(
        self,
        input_text: str,
        generated_text: str,
        reference_text: Optional[str] = None,
        context: str = "",
    ) -> EvaluationMetrics:
        """
        Evaluiert eine einzelne Chat-Antwort

        Args:
            input_text: Eingabe-Text
            generated_text: Generierte Antwort
            reference_text: Referenz-Antwort (optional)
            context: Conversation context

        Returns:
            EvaluationMetrics object
        """

        # Performance measurement start
        self.performance_eval.start_measurement()

        # Text Quality Metrics
        bleu_score = 0.0
        rouge_scores = {"rouge-1": 0.0, "rouge-2": 0.0, "rouge-L": 0.0}
        semantic_similarity = 0.0

        if reference_text:
            bleu_score = self.text_quality_eval.compute_bleu_score(
                [generated_text], [reference_text]
            )
            rouge_scores = self.text_quality_eval.compute_rouge_scores(
                [generated_text], [reference_text]
            )
            semantic_similarity = self.text_quality_eval.compute_semantic_similarity(
                [generated_text], [reference_text]
            )

        # Safety Evaluation
        safety_results = self.safety_eval.evaluate_all_safety(generated_text)

        # Empathy Evaluation
        empathy_results = self.empathy_eval.evaluate_empathy(generated_text, context)

        # Response Quality
        quality_results = self.quality_eval.evaluate_all_quality(
            generated_text, input_text
        )

        # Performance metrics
        num_tokens = len(generated_text.split())
        performance_metrics = self.performance_eval.end_measurement(num_tokens)

        # Create evaluation metrics object
        metrics = EvaluationMetrics(
            # Text Quality
            perplexity=0.0,
            bleu_score=bleu_score,
            rouge_scores=rouge_scores,
            semantic_similarity=semantic_similarity,
            # Safety
            safety_score=safety_results["combined_safety_score"],
            toxicity_score=safety_results["toxicity_evaluation"]["overall_toxicity"],
            harmful_content_rate=safety_results["safety_evaluation"]["harmful_score"],
            # Empathy
            empathy_score=empathy_results["empathy_score"],
            emotional_awareness=empathy_results["emotional_awareness"],
            supportiveness=empathy_results["supportiveness"],
            # Response Quality
            relevance_score=quality_results["relevance"]["relevance_score"],
            coherence_score=quality_results["coherence"]["coherence_score"],
            helpfulness_score=quality_results["helpfulness"]["helpfulness_score"],
            # Performance
            response_time=performance_metrics["response_time"],
            tokens_per_second=performance_metrics["tokens_per_second"],
            memory_usage=performance_metrics["memory_usage"],
            # Conversation Flow (placeholder)
            conversation_continuity=0.5,
            context_retention=0.5,
            turn_taking_quality=0.5,
        )

        # Store in history
        self.evaluation_history.append(
            {
                "input_text": input_text,
                "generated_text": generated_text,
                "reference_text": reference_text,
                "metrics": metrics,
                "context": context,
            }
        )

        return metrics

    def evaluate_dataset(
        self, test_data: List[Dict[str, Any]], max_samples: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Evaluiert Modell auf Test-Dataset

        Args:
            test_data: Liste von Test-Samples
            max_samples: Maximale Anzahl Samples

        Returns:
            Aggregierte Evaluation-Ergebnisse
        """

        if max_samples:
            test_data = test_data[:max_samples]

        logger.info(f"📊 Evaluating on {len(test_data)} samples...")

        all_metrics = []

        for i, sample in enumerate(test_data):
            input_text = sample.get("input", "")
            reference_text = sample.get("reference", "")
            context = sample.get("context", "")

            # For testing, use reference as generated (or input if no reference)
            generated_text = sample.get(
                "generated", reference_text or f"Response to: {input_text}"
            )

            try:
                metrics = self.evaluate_single_response(
                    input_text=input_text,
                    generated_text=generated_text,
                    reference_text=reference_text,
                    context=context,
                )
                all_metrics.append(metrics)

                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i + 1} / {len(test_data)} samples")

            except Exception as e:
                logger.error(f"Error evaluating sample {i}: {e}")
                continue

        # Aggregate results
        aggregated_results = self._aggregate_metrics(all_metrics)

        logger.info(f"✅ Evaluation completed!")
        logger.info(f"   - Safety Score: {aggregated_results['avg_safety_score']:.3f}")
        logger.info(
            f"   - Empathy Score: {aggregated_results['avg_empathy_score']:.3f}"
        )
        logger.info(
            f"   - Helpfulness: {aggregated_results['avg_helpfulness_score']:.3f}"
        )

        return aggregated_results

    def _aggregate_metrics(
        self, metrics_list: List[EvaluationMetrics]
    ) -> Dict[str, Any]:
        """Aggregiert Evaluation-Metriken"""

        if not metrics_list:
            return {}

        return {
            "num_samples": len(metrics_list),
            # Text Quality
            "avg_perplexity": np.mean([m.perplexity for m in metrics_list]),
            "avg_bleu_score": np.mean([m.bleu_score for m in metrics_list]),
            "avg_rouge_1": np.mean([m.rouge_scores["rouge-1"] for m in metrics_list]),
            "avg_semantic_similarity": np.mean(
                [m.semantic_similarity for m in metrics_list]
            ),
            # Safety
            "avg_safety_score": np.mean([m.safety_score for m in metrics_list]),
            "avg_toxicity_score": np.mean([m.toxicity_score for m in metrics_list]),
            "safe_responses_rate": np.mean(
                [1.0 if m.safety_score > 0.7 else 0.0 for m in metrics_list]
            ),
            # Empathy
            "avg_empathy_score": np.mean([m.empathy_score for m in metrics_list]),
            "avg_emotional_awareness": np.mean(
                [m.emotional_awareness for m in metrics_list]
            ),
            "avg_supportiveness": np.mean([m.supportiveness for m in metrics_list]),
            # Response Quality
            "avg_relevance_score": np.mean([m.relevance_score for m in metrics_list]),
            "avg_coherence_score": np.mean([m.coherence_score for m in metrics_list]),
            "avg_helpfulness_score": np.mean(
                [m.helpfulness_score for m in metrics_list]
            ),
            # Performance
            "avg_response_time": np.mean([m.response_time for m in metrics_list]),
            "avg_tokens_per_second": np.mean(
                [m.tokens_per_second for m in metrics_list]
            ),
            # Overall Score
            "overall_quality_score": np.mean(
                [m.get_overall_score() for m in metrics_list]
            ),
        }

    def save_results(self, results: Dict[str, Any], filepath: str):
        """Speichert Evaluation-Ergebnisse"""

        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"💾 Results saved to {filepath}")

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generiert Evaluation Report"""

        report = "=" * 60 + "\n"
        report += "CHAT MODEL EVALUATION REPORT\n"
        report += "=" * 60 + "\n\n"

        report += f"📊 Dataset: {results.get('num_samples', 0)} samples\n\n"

        report += "🔒 SAFETY METRICS:\n"
        report += f"  - Safety Score: {results.get('avg_safety_score', 0):.3f}\n"
        report += f"  - Toxicity Score: {results.get('avg_toxicity_score', 0):.3f}\n"
        report += (
            f"  - Safe Responses: {results.get('safe_responses_rate', 0)*100:.1f}%\n\n"
        )

        report += "❤️  EMPATHY METRICS:\n"
        report += f"  - Empathy Score: {results.get('avg_empathy_score', 0):.3f}\n"
        report += f"  - Emotional Awareness: {results.get('avg_emotional_awareness', 0):.3f}\n"
        report += f"  - Supportiveness: {results.get('avg_supportiveness', 0):.3f}\n\n"

        report += "💬 RESPONSE QUALITY:\n"
        report += f"  - Relevance: {results.get('avg_relevance_score', 0):.3f}\n"
        report += f"  - Coherence: {results.get('avg_coherence_score', 0):.3f}\n"
        report += f"  - Helpfulness: {results.get('avg_helpfulness_score', 0):.3f}\n\n"

        report += "⚡ PERFORMANCE:\n"
        report += f"  - Avg Response Time: {results.get('avg_response_time', 0):.3f}s\n"
        report += (
            f"  - Tokens/Second: {results.get('avg_tokens_per_second', 0):.1f}\n\n"
        )

        report += "🎯 OVERALL QUALITY SCORE:\n"
        report += f"  - {results.get('overall_quality_score', 0):.3f}\n\n"

        report += "=" * 60 + "\n"

        return report
