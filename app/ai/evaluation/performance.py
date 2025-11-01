"""
Performance Evaluator

Evaluiert Performance-Metriken für Chat Model Generation
"""

import logging
import time
from typing import Dict

logger = logging.getLogger(__name__)


class PerformanceEvaluator:
    """
    Evaluiert Performance-Metriken
    """

    def __init__(self):
        self.start_time = None
        self.start_memory = None

    def start_measurement(self):
        """Startet Performance-Messung"""
        self.start_time = time.time()

        try:
            import psutil

            process = psutil.Process()
            self.start_memory = process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            self.start_memory = 0

    def end_measurement(self, num_tokens: int) -> Dict[str, float]:
        """
        Beendet Performance-Messung

        Args:
            num_tokens: Anzahl generierter Tokens

        Returns:
            Performance-Metriken
        """

        if self.start_time is None:
            return {"response_time": 0.0, "tokens_per_second": 0.0, "memory_usage": 0.0}

        response_time = time.time() - self.start_time
        tokens_per_second = num_tokens / response_time if response_time > 0 else 0.0

        memory_usage = 0.0
        try:
            import psutil

            process = psutil.Process()
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_usage = current_memory - (self.start_memory or 0)
        except ImportError:
            pass

        return {
            "response_time": response_time,
            "tokens_per_second": tokens_per_second,
            "memory_usage": max(memory_usage, 0.0),
        }
