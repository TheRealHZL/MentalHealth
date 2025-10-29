"""
Training Utilities

Hilfsfunktionen für Training Pipeline
"""

import torch
import numpy as np
import random
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional
import os

logger = logging.getLogger(__name__)

def set_seed(seed: int = 42, deterministic: bool = True):
    """
    Setzt Random Seeds für Reproduzierbarkeit
    
    Args:
        seed: Random seed
        deterministic: Ob deterministische CUDA operations verwendet werden sollen
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    
    if deterministic:
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        # Set environment variable for reproducibility
        os.environ['PYTHONHASHSEED'] = str(seed)
    
    logger.info(f"🎲 Random seed set to {seed} (deterministic={deterministic})")

def save_checkpoint(
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    scheduler: Any,
    epoch: int,
    step: int,
    best_metric: float,
    checkpoint_dir: str,
    filename: Optional[str] = None,
    config: Optional[Dict] = None
) -> str:
    """
    Speichert Model Checkpoint
    
    Args:
        model: PyTorch Model
        optimizer: Optimizer
        scheduler: Learning Rate Scheduler
        epoch: Aktuelle Epoch
        step: Aktueller Step
        best_metric: Beste Metrik bisher
        checkpoint_dir: Checkpoint Verzeichnis
        filename: Optional filename
        config: Training Config
    
    Returns:
        Path zum gespeicherten Checkpoint
    """
    checkpoint_dir = Path(checkpoint_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    if filename is None:
        filename = f"checkpoint_epoch_{epoch}_step_{step}.pt"
    
    checkpoint_path = checkpoint_dir / filename
    
    # Prepare checkpoint
    checkpoint = {
        'epoch': epoch,
        'step': step,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'scheduler_state_dict': scheduler.state_dict() if scheduler else None,
        'best_metric': best_metric,
        'config': config
    }
    
    # Save checkpoint
    torch.save(checkpoint, checkpoint_path)
    logger.info(f"💾 Checkpoint saved to {checkpoint_path}")
    
    return str(checkpoint_path)

def load_checkpoint(
    checkpoint_path: str,
    model: torch.nn.Module,
    optimizer: Optional[torch.optim.Optimizer] = None,
    scheduler: Optional[Any] = None,
    device: str = "cpu"
) -> Dict[str, Any]:
    """
    Lädt Model Checkpoint
    
    Args:
        checkpoint_path: Path zum Checkpoint
        model: PyTorch Model
        optimizer: Optional Optimizer
        scheduler: Optional Scheduler
        device: Device für Model
    
    Returns:
        Dictionary mit Checkpoint Informationen
    """
    checkpoint_path = Path(checkpoint_path)
    
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
    
    logger.info(f"📂 Loading checkpoint from {checkpoint_path}")
    
    # Load checkpoint
    checkpoint = torch.load(checkpoint_path, map_location=device)
    
    # Load model state
    model.load_state_dict(checkpoint['model_state_dict'])
    
    # Load optimizer state
    if optimizer and 'optimizer_state_dict' in checkpoint:
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    
    # Load scheduler state
    if scheduler and 'scheduler_state_dict' in checkpoint and checkpoint['scheduler_state_dict']:
        scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
    
    logger.info(f"✅ Checkpoint loaded (Epoch: {checkpoint['epoch']}, Step: {checkpoint['step']})")
    
    return {
        'epoch': checkpoint.get('epoch', 0),
        'step': checkpoint.get('step', 0),
        'best_metric': checkpoint.get('best_metric', float('inf')),
        'config': checkpoint.get('config', {})
    }

def cleanup_old_checkpoints(checkpoint_dir: str, keep_last_n: int = 3):
    """
    Löscht alte Checkpoints, behält nur die letzten N
    
    Args:
        checkpoint_dir: Checkpoint Verzeichnis
        keep_last_n: Anzahl Checkpoints die behalten werden sollen
    """
    checkpoint_dir = Path(checkpoint_dir)
    
    if not checkpoint_dir.exists():
        return
    
    # Get all checkpoint files
    checkpoints = sorted(
        checkpoint_dir.glob("checkpoint_epoch_*.pt"),
        key=lambda x: x.stat().st_mtime
    )
    
    # Delete old checkpoints
    if len(checkpoints) > keep_last_n:
        for checkpoint in checkpoints[:-keep_last_n]:
            checkpoint.unlink()
            logger.info(f"🗑️  Deleted old checkpoint: {checkpoint.name}")

def count_parameters(model: torch.nn.Module) -> Dict[str, int]:
    """
    Zählt Model Parameter
    
    Args:
        model: PyTorch Model
    
    Returns:
        Dictionary mit Parameter Counts
    """
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    non_trainable_params = total_params - trainable_params
    
    return {
        'total': total_params,
        'trainable': trainable_params,
        'non_trainable': non_trainable_params
    }

def format_time(seconds: float) -> str:
    """
    Formatiert Zeit in lesbarem Format
    
    Args:
        seconds: Zeit in Sekunden
    
    Returns:
        Formatierte Zeit String
    """
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.2f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.2f}h"

def get_device(prefer_cuda: bool = True) -> torch.device:
    """
    Ermittelt bestes verfügbares Device
    
    Args:
        prefer_cuda: Ob CUDA bevorzugt werden soll
    
    Returns:
        torch.device
    """
    if prefer_cuda and torch.cuda.is_available():
        device = torch.device("cuda")
        logger.info(f"🚀 Using CUDA: {torch.cuda.get_device_name(0)}")
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
        logger.info("🍎 Using Apple MPS")
    else:
        device = torch.device("cpu")
        logger.info("💻 Using CPU")
    
    return device

def save_training_metrics(metrics: Dict[str, Any], filepath: str):
    """
    Speichert Training Metriken als JSON
    
    Args:
        metrics: Metriken Dictionary
        filepath: Pfad zur Datei
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"📊 Metrics saved to {filepath}")

def load_training_metrics(filepath: str) -> Dict[str, Any]:
    """
    Lädt Training Metriken von JSON
    
    Args:
        filepath: Pfad zur Datei
    
    Returns:
        Metriken Dictionary
    """
    filepath = Path(filepath)
    
    if not filepath.exists():
        return {}
    
    with open(filepath, 'r') as f:
        metrics = json.load(f)
    
    return metrics

class AverageMeter:
    """Computes and stores the average and current value"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.val = 0
        self.avg = 0
        self.sum = 0
        self.count = 0
    
    def update(self, val, n=1):
        self.val = val
        self.sum += val * n
        self.count += n
        self.avg = self.sum / self.count

class EarlyStopping:
    """Early Stopping Handler"""
    
    def __init__(
        self,
        patience: int = 3,
        mode: str = "min",
        delta: float = 0.0
    ):
        self.patience = patience
        self.mode = mode
        self.delta = delta
        self.counter = 0
        self.best_score = None
        self.early_stop = False
        
        self.is_better = (
            lambda score, best: score < best - delta
            if mode == "min"
            else score > best + delta
        )
    
    def __call__(self, score: float) -> bool:
        """
        Check if training should stop
        
        Args:
            score: Current metric score
        
        Returns:
            True if training should stop
        """
        if self.best_score is None:
            self.best_score = score
            return False
        
        if self.is_better(score, self.best_score):
            self.best_score = score
            self.counter = 0
        else:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
                logger.info(f"⏹️  Early stopping triggered (patience={self.patience})")
                return True
        
        return False

def get_lr(optimizer: torch.optim.Optimizer) -> float:
    """Get current learning rate from optimizer"""
    for param_group in optimizer.param_groups:
        return param_group['lr']
    return 0.0
