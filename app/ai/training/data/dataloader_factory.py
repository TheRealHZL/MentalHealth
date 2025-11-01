"""
DataLoader Factory

Factory Pattern für DataLoader Creation
"""

import logging
from typing import Any, Optional

from torch.utils.data import DataLoader as TorchDataLoader

from .chat_dataset import ChatDataset
from .emotion_dataset import EmotionDataset
from .mood_dataset import MoodDataset
from .sentiment_dataset import SentimentDataset

logger = logging.getLogger(__name__)


class DataLoaderFactory:
    """Factory für DataLoader Creation"""

    # Map dataset types to classes
    DATASET_MAP = {
        "sentiment": SentimentDataset,
        "emotion": EmotionDataset,
        "mood": MoodDataset,
        "chat": ChatDataset,
    }

    @classmethod
    def create_dataloader(
        cls,
        dataset_type: str,
        data_path: str,
        batch_size: int = 32,
        shuffle: bool = True,
        num_workers: int = 4,
        pin_memory: bool = True,
        tokenizer: Optional[Any] = None,
        max_length: int = 512,
        **kwargs,
    ) -> TorchDataLoader:
        """
        Erstellt DataLoader für spezifischen Dataset-Typ

        Args:
            dataset_type: Type des Datasets (sentiment, emotion, mood, chat)
            data_path: Path zu Daten
            batch_size: Batch size
            shuffle: Ob geshuffled werden soll
            num_workers: Anzahl Worker Threads
            pin_memory: Pin memory für GPU
            tokenizer: Optional tokenizer
            max_length: Maximale Sequenz-Länge
            **kwargs: Zusätzliche Dataset-spezifische Parameter

        Returns:
            DataLoader
        """

        # Validate dataset type
        if dataset_type not in cls.DATASET_MAP:
            raise ValueError(
                f"Unknown dataset type: {dataset_type}. "
                f"Available: {list(cls.DATASET_MAP.keys())}"
            )

        # Get dataset class
        dataset_class = cls.DATASET_MAP[dataset_type]

        # Create dataset
        dataset = dataset_class(
            data_path=data_path, tokenizer=tokenizer, max_length=max_length, **kwargs
        )

        # Create dataloader
        dataloader = TorchDataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=shuffle,
            num_workers=num_workers,
            pin_memory=pin_memory,
            drop_last=True if shuffle else False,
        )

        logger.info(f"✅ Created {dataset_type} DataLoader:")
        logger.info(f"   - Samples: {len(dataset)}")
        logger.info(f"   - Batches: {len(dataloader)}")
        logger.info(f"   - Batch Size: {batch_size}")

        return dataloader

    @classmethod
    def create_train_val_test_loaders(
        cls,
        dataset_type: str,
        train_path: str,
        val_path: str,
        test_path: str,
        batch_size: int = 32,
        tokenizer: Optional[Any] = None,
        num_workers: int = 4,
        **kwargs,
    ) -> tuple:
        """
        Erstellt Train, Validation und Test DataLoader

        Args:
            dataset_type: Type des Datasets
            train_path: Path zu Training Daten
            val_path: Path zu Validation Daten
            test_path: Path zu Test Daten
            batch_size: Batch size
            tokenizer: Optional tokenizer
            num_workers: Anzahl Worker Threads
            **kwargs: Zusätzliche Parameter

        Returns:
            Tuple of (train_loader, val_loader, test_loader)
        """

        logger.info(f"🔄 Creating train/val/test loaders for {dataset_type}")

        # Train loader (with shuffle)
        train_loader = cls.create_dataloader(
            dataset_type=dataset_type,
            data_path=train_path,
            batch_size=batch_size,
            shuffle=True,
            num_workers=num_workers,
            tokenizer=tokenizer,
            **kwargs,
        )

        # Validation loader (no shuffle)
        val_loader = cls.create_dataloader(
            dataset_type=dataset_type,
            data_path=val_path,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            tokenizer=tokenizer,
            **kwargs,
        )

        # Test loader (no shuffle)
        test_loader = cls.create_dataloader(
            dataset_type=dataset_type,
            data_path=test_path,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            tokenizer=tokenizer,
            **kwargs,
        )

        logger.info("✅ All loaders created successfully")

        return train_loader, val_loader, test_loader
