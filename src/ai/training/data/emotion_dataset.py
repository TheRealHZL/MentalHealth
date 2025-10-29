"""
Emotion Dataset

Dataset für Emotion Classification Training
"""

import torch
from typing import Dict
from .base_dataset import BaseDataset

class EmotionDataset(BaseDataset):
    """Dataset für Emotion Classification"""
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """
        Get sample
        
        Returns:
            Dictionary mit:
            - input_ids: Token IDs
            - attention_mask: Attention mask
            - labels: Emotion label (0-6: joy, sadness, anger, fear, surprise, disgust, neutral)
        """
        item = self.data[idx]
        
        text = item['text']
        emotion = item['emotion']  # 0-6
        
        # Tokenize
        tokens = self._tokenize(text)
        tokens = self._pad_tokens(tokens)
        
        return {
            'input_ids': torch.tensor(tokens, dtype=torch.long),
            'attention_mask': torch.tensor(self._create_attention_mask(tokens), dtype=torch.long),
            'labels': torch.tensor(emotion, dtype=torch.long)
        }
