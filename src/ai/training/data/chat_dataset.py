"""
Chat Dataset

Dataset für Chat Generation Training
"""

import torch
from typing import Dict
from .base_dataset import BaseDataset

class ChatDataset(BaseDataset):
    """Dataset für Chat Generation"""
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """
        Get sample
        
        Returns:
            Dictionary mit:
            - input_ids: Input token IDs
            - attention_mask: Attention mask
            - labels: Target token IDs
            - emotion_context: Emotion context (optional)
            - mood_context: Mood context (optional)
        """
        item = self.data[idx]
        
        # Get text fields
        context = item.get('context', '')
        input_text = item['input']
        target_text = item['target']
        
        # Combine context and input
        full_input = f"{context} {input_text}".strip()
        
        # Tokenize input and target
        input_tokens = self._tokenize(full_input)
        target_tokens = self._tokenize(target_text)
        
        # Pad tokens
        input_tokens = self._pad_tokens(input_tokens)
        target_tokens = self._pad_tokens(target_tokens)
        
        # Optional: emotion and mood context
        emotion_context = item.get('emotion', 6)  # Default: neutral
        mood_context = item.get('mood', 5.0)
        
        return {
            'input_ids': torch.tensor(input_tokens, dtype=torch.long),
            'attention_mask': torch.tensor(self._create_attention_mask(input_tokens), dtype=torch.long),
            'labels': torch.tensor(target_tokens, dtype=torch.long),
            'emotion_context': torch.tensor(emotion_context, dtype=torch.long),
            'mood_context': torch.tensor(mood_context, dtype=torch.float32)
        }
