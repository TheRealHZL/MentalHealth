"""
Sentiment Dataset

Dataset für Sentiment Analysis Training
"""

import torch
from typing import Dict
from .base_dataset import BaseDataset

class SentimentDataset(BaseDataset):
    """Dataset für Sentiment Analysis"""
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """
        Get sample
        
        Returns:
            Dictionary mit:
            - input_ids: Token IDs
            - attention_mask: Attention mask
            - labels: Sentiment label (0: negative, 1: neutral, 2: positive)
        """
        item = self.data[idx]
        
        text = item['text']
        label = item['label']  # 0: negative, 1: neutral, 2: positive
        
        # Tokenize text
        tokens = self._tokenize(text)
        tokens = self._pad_tokens(tokens)
        
        return {
            'input_ids': torch.tensor(tokens, dtype=torch.long),
            'attention_mask': torch.tensor(self._create_attention_mask(tokens), dtype=torch.long),
            'labels': torch.tensor(label, dtype=torch.long)
        }
