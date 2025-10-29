"""
Mood Dataset

Dataset für Mood Prediction Training
"""

import torch
from typing import Dict, Optional, Any
from .base_dataset import BaseDataset

class MoodDataset(BaseDataset):
    """Dataset für Mood Prediction"""
    
    def __init__(
        self, 
        data_path: str, 
        tokenizer: Optional[Any] = None,
        max_length: int = 512, 
        sequence_length: int = 7, 
        mode: str = "train"
    ):
        self.sequence_length = sequence_length
        super().__init__(data_path, tokenizer, max_length, mode)
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """
        Get sample
        
        Returns:
            Dictionary mit:
            - mood_sequence: Historical mood scores [sequence_length]
            - metadata: Metadata features [10]
            - labels: Target mood score (float)
        """
        item = self.data[idx]
        
        # Historical mood scores
        mood_sequence = item['mood_sequence']
        
        # Metadata features
        metadata = item.get('metadata', {})
        metadata_features = self._extract_metadata_features(metadata)
        
        # Target: next mood score
        target_mood = item['target_mood']
        
        # Pad mood sequence if needed
        mood_sequence = self._pad_mood_sequence(mood_sequence)
        
        return {
            'mood_sequence': torch.tensor(mood_sequence, dtype=torch.float32),
            'metadata': torch.tensor(metadata_features, dtype=torch.float32),
            'labels': torch.tensor(target_mood, dtype=torch.float32)
        }
    
    def _extract_metadata_features(self, metadata: Dict[str, Any]) -> list:
        """Extract metadata features"""
        return [
            metadata.get('sleep_hours', 7.0),
            metadata.get('stress_level', 5.0),
            metadata.get('exercise_minutes', 0.0),
            metadata.get('social_interaction', 0.0),
            metadata.get('medication', 0.0),
            metadata.get('therapy_session', 0.0),
            metadata.get('work_hours', 8.0),
            metadata.get('caffeine_intake', 0.0),
            metadata.get('alcohol_intake', 0.0),
            metadata.get('screen_time', 0.0)
        ]
    
    def _pad_mood_sequence(self, mood_sequence: list) -> list:
        """Pad or truncate mood sequence"""
        if len(mood_sequence) < self.sequence_length:
            # Pad with neutral mood (5.0)
            return [5.0] * (self.sequence_length - len(mood_sequence)) + mood_sequence
        else:
            # Take last N entries
            return mood_sequence[-self.sequence_length:]
