"""
Base Dataset

Basis-Klasse für alle Datasets
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch
from torch.utils.data import Dataset

logger = logging.getLogger(__name__)


class BaseDataset(Dataset):
    """
    Base Dataset für Mental Health Data
    """

    def __init__(
        self,
        data_path: str,
        tokenizer: Optional[Any] = None,
        max_length: int = 512,
        mode: str = "train",
    ):
        self.data_path = Path(data_path)
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.mode = mode

        # Load data
        self.data = self._load_data()

        logger.info(f"📁 Loaded {len(self.data)} samples from {data_path}")

    def _load_data(self) -> List[Dict[str, Any]]:
        """Lädt Daten von JSON File"""

        if not self.data_path.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_path}")

        with open(self.data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        raise NotImplementedError("Subclasses must implement __getitem__")

    def _tokenize(self, text: str) -> List[int]:
        """
        Tokenize text (mit Fallback)

        Args:
            text: Input text

        Returns:
            List of token IDs
        """
        if self.tokenizer:
            return self.tokenizer.encode(text, max_length=self.max_length)
        else:
            # Simple word tokenization as fallback
            return [hash(word) % 10000 for word in text.lower().split()][
                : self.max_length
            ]

    def _pad_tokens(self, tokens: List[int]) -> List[int]:
        """
        Pad or truncate tokens to max_length

        Args:
            tokens: Token IDs

        Returns:
            Padded token list
        """
        if len(tokens) < self.max_length:
            return tokens + [0] * (self.max_length - len(tokens))
        else:
            return tokens[: self.max_length]

    def _create_attention_mask(self, tokens: List[int]) -> List[int]:
        """
        Create attention mask (1 for real tokens, 0 for padding)

        Args:
            tokens: Token IDs

        Returns:
            Attention mask
        """
        return [1 if t != 0 else 0 for t in tokens]
