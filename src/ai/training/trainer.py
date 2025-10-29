"""
Model Trainer

Hauptklasse für Model Training mit Multilingual Support
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from typing import Optional, Dict, Any, List
import logging
from pathlib import Path
import time
from tqdm import tqdm

from .config import TrainingConfig
from .utils import (
    set_seed, save_checkpoint, AverageMeter, 
    EarlyStopping, get_lr, format_time, count_parameters
)

logger = logging.getLogger(__name__)

class ModelTrainer:
    """
    Universeller Model Trainer für alle AI Models
    Unterstützt: Deutsch, Englisch, Französisch
    """
    
    def __init__(
        self,
        model: nn.Module,
        config: TrainingConfig,
        train_loader: DataLoader,
        val_loader: Optional[DataLoader] = None,
        test_loader: Optional[DataLoader] = None,
        multilingual: bool = False,
        languages: List[str] = ['de', 'en', 'fr']
    ):
        self.model = model
        self.config = config
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.test_loader = test_loader
        self.multilingual = multilingual
        self.languages = languages
        
        # Setup device
        self.device = torch.device(config.device if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        
        # Setup optimizer
        self.optimizer = self._create_optimizer()
        
        # Setup scheduler
        self.scheduler = self._create_scheduler()
        
        # Setup loss function
        self.criterion = self._create_criterion()
        
        # Early stopping
        self.early_stopping = EarlyStopping(
            patience=config.early_stopping_patience,
            mode=config.early_stopping_mode
        )
        
        # Training state
        self.current_epoch = 0
        self.global_step = 0
        self.best_metric = float('inf') if config.early_stopping_mode == 'min' else float('-inf')
        
        # Training history
        self.history = {
            'train_loss': [],
            'val_loss': [],
            'train_metrics': [],
            'val_metrics': []
        }
        
        # Set seed
        set_seed(config.seed, config.deterministic)
        
        # Log info
        param_counts = count_parameters(model)
        logger.info("🧠 Model Trainer initialized:")
        logger.info(f"   - Device: {self.device}")
        logger.info(f"   - Multilingual: {multilingual}")
        if multilingual:
            logger.info(f"   - Languages: {', '.join(languages)}")
        logger.info(f"   - Total Parameters: {param_counts['total']:,}")
        logger.info(f"   - Trainable: {param_counts['trainable']:,}")
    
    def _create_optimizer(self) -> optim.Optimizer:
        """Erstellt Optimizer"""
        
        if self.config.optimizer.lower() == 'adam':
            optimizer = optim.Adam(
                self.model.parameters(),
                lr=self.config.learning_rate,
                eps=self.config.adam_epsilon
            )
        elif self.config.optimizer.lower() == 'adamw':
            optimizer = optim.AdamW(
                self.model.parameters(),
                lr=self.config.learning_rate,
                weight_decay=self.config.weight_decay
            )
        elif self.config.optimizer.lower() == 'sgd':
            optimizer = optim.SGD(
                self.model.parameters(),
                lr=self.config.learning_rate,
                momentum=0.9
            )
        else:
            raise ValueError(f"Unknown optimizer: {self.config.optimizer}")
        
        return optimizer
    
    def _create_scheduler(self):
        """Erstellt Learning Rate Scheduler"""
        
        if self.config.scheduler.lower() == 'linear':
            from torch.optim.lr_scheduler import LinearLR
            scheduler = LinearLR(
                self.optimizer,
                start_factor=1.0,
                end_factor=0.1,
                total_iters=self.config.num_epochs
            )
        elif self.config.scheduler.lower() == 'cosine':
            from torch.optim.lr_scheduler import CosineAnnealingLR
            scheduler = CosineAnnealingLR(
                self.optimizer,
                T_max=self.config.num_epochs
            )
        else:
            scheduler = None
        
        return scheduler
    
    def _create_criterion(self):
        """Erstellt Loss Function"""
        
        if self.config.model_type in ['sentiment_analyzer', 'emotion_classifier']:
            # Classification loss
            return nn.CrossEntropyLoss(label_smoothing=self.config.label_smoothing)
        elif self.config.model_type == 'mood_predictor':
            # Regression loss
            return nn.MSELoss()
        elif self.config.model_type == 'chat_generator':
            # Language modeling loss
            return nn.CrossEntropyLoss(ignore_index=0)  # Ignore padding
        else:
            return nn.CrossEntropyLoss()
    
    def train(self):
        """Haupttraining Loop"""
        
        logger.info("🚀 Starting training...")
        logger.info(f"   - Epochs: {self.config.num_epochs}")
        logger.info(f"   - Batch Size: {self.config.batch_size}")
        logger.info(f"   - Learning Rate: {self.config.learning_rate}")
        
        start_time = time.time()
        
        for epoch in range(self.config.num_epochs):
            self.current_epoch = epoch
            
            # Train one epoch
            train_loss, train_metrics = self._train_epoch()
            
            # Validate
            if self.val_loader:
                val_loss, val_metrics = self._validate()
            else:
                val_loss, val_metrics = 0.0, {}
            
            # Update scheduler
            if self.scheduler:
                self.scheduler.step()
            
            # Log progress
            logger.info(
                f"Epoch {epoch+1}/{self.config.num_epochs} - "
                f"Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}, "
                f"LR: {get_lr(self.optimizer):.6f}"
            )
            
            # Save history
            self.history['train_loss'].append(train_loss)
            self.history['val_loss'].append(val_loss)
            self.history['train_metrics'].append(train_metrics)
            self.history['val_metrics'].append(val_metrics)
            
            # Save checkpoint
            if (epoch + 1) % self.config.save_every_n_epochs == 0:
                save_checkpoint(
                    model=self.model,
                    optimizer=self.optimizer,
                    scheduler=self.scheduler,
                    epoch=epoch,
                    step=self.global_step,
                    best_metric=self.best_metric,
                    checkpoint_dir=self.config.checkpoint_dir,
                    config=self.config.to_dict()
                )
            
            # Early stopping check
            metric_to_monitor = val_loss if self.val_loader else train_loss
            if self.early_stopping(metric_to_monitor):
                logger.info(f"⏹️  Early stopping at epoch {epoch+1}")
                break
            
            # Update best metric
            if self.config.early_stopping_mode == 'min':
                if metric_to_monitor < self.best_metric:
                    self.best_metric = metric_to_monitor
                    self._save_best_model()
            else:
                if metric_to_monitor > self.best_metric:
                    self.best_metric = metric_to_monitor
                    self._save_best_model()
        
        # Training complete
        total_time = time.time() - start_time
        logger.info(f"✅ Training complete in {format_time(total_time)}")
        logger.info(f"   - Best metric: {self.best_metric:.4f}")
        
        return self.history
    
    def _train_epoch(self) -> tuple:
        """Training für eine Epoch"""
        
        self.model.train()
        losses = AverageMeter()
        
        pbar = tqdm(self.train_loader, desc=f"Epoch {self.current_epoch+1}")
        
        for batch_idx, batch in enumerate(pbar):
            # Move to device
            batch = {k: v.to(self.device) if isinstance(v, torch.Tensor) else v 
                    for k, v in batch.items()}
            
            # Forward pass
            loss = self._compute_loss(batch)
            
            # Backward pass
            loss.backward()
            
            # Gradient clipping
            if self.config.max_grad_norm > 0:
                torch.nn.utils.clip_grad_norm_(
                    self.model.parameters(), 
                    self.config.max_grad_norm
                )
            
            # Optimizer step
            if (batch_idx + 1) % self.config.gradient_accumulation_steps == 0:
                self.optimizer.step()
                self.optimizer.zero_grad()
                self.global_step += 1
            
            # Update metrics
            losses.update(loss.item(), batch['input_ids'].size(0))
            
            # Update progress bar
            pbar.set_postfix({'loss': losses.avg})
        
        return losses.avg, {}
    
    def _validate(self) -> tuple:
        """Validation"""
        
        self.model.eval()
        losses = AverageMeter()
        
        with torch.no_grad():
            for batch in tqdm(self.val_loader, desc="Validation"):
                # Move to device
                batch = {k: v.to(self.device) if isinstance(v, torch.Tensor) else v 
                        for k, v in batch.items()}
                
                # Forward pass
                loss = self._compute_loss(batch)
                
                # Update metrics
                losses.update(loss.item(), batch['input_ids'].size(0) if 'input_ids' in batch else batch['mood_sequence'].size(0))
        
        return losses.avg, {}
    
    def _compute_loss(self, batch: Dict[str, torch.Tensor]) -> torch.Tensor:
        """Berechnet Loss basierend auf Model Type"""
        
        if self.config.model_type in ['sentiment_analyzer', 'emotion_classifier']:
            # Classification
            outputs = self.model(
                input_ids=batch['input_ids'],
                attention_mask=batch.get('attention_mask')
            )
            logits = outputs['logits']
            loss = self.criterion(logits, batch['labels'])
            
        elif self.config.model_type == 'mood_predictor':
            # Regression
            outputs = self.model(
                mood_sequence=batch['mood_sequence'],
                metadata=batch.get('metadata')
            )
            predictions = outputs['predictions']
            loss = self.criterion(predictions.squeeze(), batch['labels'])
            
        elif self.config.model_type == 'chat_generator':
            # Language modeling
            outputs = self.model(
                input_ids=batch['input_ids'],
                attention_mask=batch.get('attention_mask'),
                emotion_context=batch.get('emotion_context'),
                mood_context=batch.get('mood_context')
            )
            logits = outputs['logits']
            
            # Shift for next token prediction
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = batch['labels'][..., 1:].contiguous()
            
            loss = self.criterion(
                shift_logits.view(-1, shift_logits.size(-1)),
                shift_labels.view(-1)
            )
        else:
            raise ValueError(f"Unknown model type: {self.config.model_type}")
        
        return loss
    
    def _save_best_model(self):
        """Speichert bestes Model"""
        
        save_checkpoint(
            model=self.model,
            optimizer=self.optimizer,
            scheduler=self.scheduler,
            epoch=self.current_epoch,
            step=self.global_step,
            best_metric=self.best_metric,
            checkpoint_dir=self.config.checkpoint_dir,
            filename="best_model.pt",
            config=self.config.to_dict()
        )
        
        logger.info(f"💾 Best model saved (metric: {self.best_metric:.4f})")
    
    def test(self) -> Dict[str, Any]:
        """Evaluiert Model auf Test Set"""
        
        if not self.test_loader:
            logger.warning("No test loader provided")
            return {}
        
        logger.info("🧪 Running test evaluation...")
        
        self.model.eval()
        losses = AverageMeter()
        
        with torch.no_grad():
            for batch in tqdm(self.test_loader, desc="Testing"):
                batch = {k: v.to(self.device) if isinstance(v, torch.Tensor) else v 
                        for k, v in batch.items()}
                
                loss = self._compute_loss(batch)
                losses.update(loss.item())
        
        test_loss = losses.avg
        logger.info(f"✅ Test Loss: {test_loss:.4f}")
        
        return {'test_loss': test_loss}
