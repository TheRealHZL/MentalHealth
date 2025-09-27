"""
Mood Predictor Model

LSTM-basiertes Neural Network für Stimmungsvorhersage.
Analysiert Zeitreihen von Texten und Metadaten zur Mood-Prognose.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Any, Optional, List, Tuple
import logging
import math

logger = logging.getLogger(__name__)

class BiLSTMLayer(nn.Module):
    """
    Bidirectional LSTM Layer mit verbesserter Performance
    """
    
    def __init__(
        self,
        input_dim: int,
        hidden_dim: int,
        dropout: float = 0.1,
        layer_norm: bool = True
    ):
        super().__init__()
        
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        
        # Bidirectional LSTM
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=1,
            dropout=0,  # We handle dropout manually
            bidirectional=True,
            batch_first=True
        )
        
        # Output dimension is 2 * hidden_dim due to bidirectionality
        self.output_dim = 2 * hidden_dim
        
        # Layer normalization
        if layer_norm:
            self.layer_norm = nn.LayerNorm(self.output_dim)
        else:
            self.layer_norm = None
        
        # Dropout
        self.dropout = nn.Dropout(dropout)
    
    def forward(
        self, 
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, Tuple[torch.Tensor, torch.Tensor]]:
        """
        Forward pass
        
        Args:
            x: Input tensor [batch_size, seq_len, input_dim]
            mask: Optional padding mask [batch_size, seq_len]
        
        Returns:
            output: LSTM outputs [batch_size, seq_len, 2*hidden_dim]
            hidden: Final hidden states (h_n, c_n)
        """
        batch_size, seq_len, _ = x.size()
        
        # Pack padded sequences if mask is provided
        if mask is not None:
            # Get sequence lengths
            lengths = mask.sum(dim=1).cpu()
            x_packed = nn.utils.rnn.pack_padded_sequence(
                x, lengths, batch_first=True, enforce_sorted=False
            )
            output_packed, hidden = self.lstm(x_packed)
            output, _ = nn.utils.rnn.pad_packed_sequence(
                output_packed, batch_first=True
            )
        else:
            output, hidden = self.lstm(x)
        
        # Apply layer normalization
        if self.layer_norm is not None:
            output = self.layer_norm(output)
        
        # Apply dropout
        output = self.dropout(output)
        
        return output, hidden

class AttentionPooling(nn.Module):
    """
    Attention-based pooling mechanism für variable Sequenzlängen
    """
    
    def __init__(self, hidden_dim: int):
        super().__init__()
        
        self.hidden_dim = hidden_dim
        
        # Attention mechanism
        self.attention = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1)
        )
    
    def forward(
        self, 
        hidden_states: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Attention pooling
        
        Args:
            hidden_states: [batch_size, seq_len, hidden_dim]
            mask: Optional mask [batch_size, seq_len]
        
        Returns:
            Pooled representation [batch_size, hidden_dim]
        """
        # Compute attention weights
        attention_scores = self.attention(hidden_states).squeeze(-1)  # [batch_size, seq_len]
        
        # Apply mask if provided
        if mask is not None:
            attention_scores = attention_scores.masked_fill(mask == 0, float('-inf'))
        
        # Softmax
        attention_weights = F.softmax(attention_scores, dim=-1)  # [batch_size, seq_len]
        
        # Weighted sum
        pooled = torch.sum(
            hidden_states * attention_weights.unsqueeze(-1), 
            dim=1
        )  # [batch_size, hidden_dim]
        
        return pooled

class MetadataEncoder(nn.Module):
    """
    Encoder für Metadata (Schlaf, Stress, Aktivitäten, etc.)
    """
    
    def __init__(
        self,
        categorical_dims: Dict[str, int],
        numerical_features: int = 5,
        output_dim: int = 64
    ):
        super().__init__()
        
        self.categorical_dims = categorical_dims
        self.numerical_features = numerical_features
        self.output_dim = output_dim
        
        # Embeddings für kategorische Features
        self.embeddings = nn.ModuleDict()
        total_embed_dim = 0
        
        for feature_name, vocab_size in categorical_dims.items():
            embed_dim = min(50, (vocab_size + 1) // 2)  # Heuristic for embedding size
            self.embeddings[feature_name] = nn.Embedding(vocab_size, embed_dim)
            total_embed_dim += embed_dim
        
        # Input dimension
        input_dim = total_embed_dim + numerical_features
        
        # MLP für Metadata Processing
        self.metadata_mlp = nn.Sequential(
            nn.Linear(input_dim, output_dim * 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(output_dim * 2, output_dim),
            nn.ReLU(),
            nn.Dropout(0.1)
        )
    
    def forward(
        self, 
        categorical_features: Dict[str, torch.Tensor],
        numerical_features: torch.Tensor
    ) -> torch.Tensor:
        """
        Encode metadata
        
        Args:
            categorical_features: Dict of categorical tensors [batch_size]
            numerical_features: Numerical tensor [batch_size, num_features]
        
        Returns:
            Encoded metadata [batch_size, output_dim]
        """
        # Process categorical features
        categorical_embeds = []
        for feature_name, feature_tensor in categorical_features.items():
            if feature_name in self.embeddings:
                embed = self.embeddings[feature_name](feature_tensor)
                categorical_embeds.append(embed)
        
        # Concatenate all features
        features = [numerical_features] + categorical_embeds
        combined_features = torch.cat(features, dim=-1)
        
        # Process through MLP
        encoded = self.metadata_mlp(combined_features)
        
        return encoded

class MoodPredictor(nn.Module):
    """
    Mood Prediction Model
    
    Architektur:
    - Text Embedding + Positional Encoding
    - Multi-layer Bidirectional LSTM
    - Metadata Encoder
    - Attention Pooling
    - Fusion Layer
    - Mood Regression Head
    """
    
    def __init__(
        self,
        vocab_size: int,
        embedding_dim: int = 256,
        hidden_dim: int = 512,
        num_layers: int = 3,
        dropout_rate: float = 0.1,
        max_sequence_length: int = 512,
        metadata_dim: int = 64,
        use_metadata: bool = True
    ):
        super().__init__()
        
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.dropout_rate = dropout_rate
        self.max_sequence_length = max_sequence_length
        self.use_metadata = use_metadata
        
        # Text embedding
        self.text_embedding = nn.Embedding(
            vocab_size, 
            embedding_dim, 
            padding_idx=0
        )
        
        # Positional encoding for temporal sequences
        self.positional_encoding = self._create_positional_encoding(
            max_sequence_length, embedding_dim
        )
        
        # LSTM layers
        self.lstm_layers = nn.ModuleList()
        
        # First layer: embedding_dim -> hidden_dim
        self.lstm_layers.append(
            BiLSTMLayer(embedding_dim, hidden_dim, dropout_rate)
        )
        
        # Subsequent layers: 2*hidden_dim -> hidden_dim (due to bidirectionality)
        for _ in range(num_layers - 1):
            self.lstm_layers.append(
                BiLSTMLayer(2 * hidden_dim, hidden_dim, dropout_rate)
            )
        
        # Final LSTM output dimension
        lstm_output_dim = 2 * hidden_dim
        
        # Attention pooling
        self.attention_pooling = AttentionPooling(lstm_output_dim)
        
        # Metadata encoder (if used)
        if use_metadata:
            # Default categorical features for mood prediction
            categorical_dims = {
                'day_of_week': 7,
                'time_of_day': 4,  # morning, afternoon, evening, night
                'sleep_quality': 5,  # 1-5 scale
                'stress_level': 10,  # 1-10 scale
                'activity_type': 10  # different activity types
            }
            
            self.metadata_encoder = MetadataEncoder(
                categorical_dims=categorical_dims,
                numerical_features=5,  # sleep_hours, exercise_minutes, etc.
                output_dim=metadata_dim
            )
            
            # Fusion layer
            fusion_input_dim = lstm_output_dim + metadata_dim
        else:
            self.metadata_encoder = None
            fusion_input_dim = lstm_output_dim
        
        # Fusion and prediction layers
        self.fusion_layer = nn.Sequential(
            nn.Linear(fusion_input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout_rate)
        )
        
        # Mood prediction head
        self.mood_predictor = nn.Sequential(
            nn.Linear(hidden_dim // 2, 32),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(32, 1),  # Single value: mood score
            nn.Sigmoid()  # Normalize to [0, 1], will be scaled to [1, 10]
        )
        
        # Uncertainty estimation head (optional)
        self.uncertainty_head = nn.Sequential(
            nn.Linear(hidden_dim // 2, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Softplus()  # Ensures positive values
        )
        
        # Initialize weights
        self._init_weights()
        
        logger.info(f"🧠 MoodPredictor initialized:")
        logger.info(f"   - Vocab size: {vocab_size}")
        logger.info(f"   - Embedding dim: {embedding_dim}")
        logger.info(f"   - Hidden dim: {hidden_dim}")
        logger.info(f"   - Num LSTM layers: {num_layers}")
        logger.info(f"   - Use metadata: {use_metadata}")
    
    def _create_positional_encoding(self, max_len: int, embed_dim: int) -> torch.Tensor:
        """Creates sinusoidal positional encoding"""
        
        pe = torch.zeros(max_len, embed_dim)
        position = torch.arange(0, max_len).unsqueeze(1).float()
        
        div_term = torch.exp(
            torch.arange(0, embed_dim, 2).float() * 
            -(math.log(10000.0) / embed_dim)
        )
        
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        
        return pe.unsqueeze(0)  # [1, max_len, embed_dim]
    
    def _init_weights(self):
        """Initialize model weights"""
        
        # Initialize embeddings
        nn.init.normal_(self.text_embedding.weight, mean=0, std=0.02)
        nn.init.constant_(self.text_embedding.weight[0], 0)  # Padding token
        
        # Initialize linear layers
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.constant_(module.bias, 0)
    
    def create_padding_mask(self, input_ids: torch.Tensor) -> torch.Tensor:
        """Creates padding mask"""
        return (input_ids != 0).float()
    
    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        metadata: Optional[Dict[str, torch.Tensor]] = None
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass
        
        Args:
            input_ids: Token IDs [batch_size, seq_len]
            attention_mask: Padding mask [batch_size, seq_len]
            metadata: Optional metadata dict
        
        Returns:
            Dictionary with mood predictions and uncertainty
        """
        batch_size, seq_len = input_ids.size()
        device = input_ids.device
        
        # Create attention mask if not provided
        if attention_mask is None:
            attention_mask = self.create_padding_mask(input_ids)
        
        # Text embedding
        embeddings = self.text_embedding(input_ids)  # [batch_size, seq_len, embedding_dim]
        
        # Add positional encoding
        pos_encoding = self.positional_encoding[:, :seq_len, :].to(device)
        embeddings = embeddings + pos_encoding
        
        # Apply dropout
        embeddings = F.dropout(embeddings, p=self.dropout_rate, training=self.training)
        
        # Pass through LSTM layers
        hidden_states = embeddings
        
        for lstm_layer in self.lstm_layers:
            hidden_states, _ = lstm_layer(hidden_states, attention_mask)
        
        # Attention pooling
        text_representation = self.attention_pooling(hidden_states, attention_mask)
        
        # Process metadata if available
        if self.use_metadata and metadata is not None and self.metadata_encoder is not None:
            categorical_features = {
                k: v for k, v in metadata.items() 
                if k in ['day_of_week', 'time_of_day', 'sleep_quality', 'stress_level', 'activity_type']
            }
            
            numerical_features = metadata.get('numerical_features', 
                torch.zeros(batch_size, 5, device=device))
            
            metadata_representation = self.metadata_encoder(
                categorical_features, numerical_features
            )
            
            # Fuse text and metadata
            fused_representation = torch.cat([text_representation, metadata_representation], dim=-1)
        else:
            fused_representation = text_representation
        
        # Fusion layer
        fused_features = self.fusion_layer(fused_representation)
        
        # Mood prediction
        mood_score = self.mood_predictor(fused_features)  # [batch_size, 1]
        
        # Scale from [0, 1] to [1, 10]
        mood_score = mood_score * 9 + 1
        
        # Uncertainty estimation
        uncertainty = self.uncertainty_head(fused_features)  # [batch_size, 1]
        
        return {
            'mood_score': mood_score.squeeze(-1),  # [batch_size]
            'uncertainty': uncertainty.squeeze(-1),  # [batch_size]
            'text_representation': text_representation,
            'fused_features': fused_features
        }
    
    def predict_mood_sequence(
        self,
        input_sequences: List[torch.Tensor],
        metadata_sequences: Optional[List[Dict[str, torch.Tensor]]] = None,
        return_uncertainty: bool = True
    ) -> Dict[str, Any]:
        """
        Predicts mood for a sequence of texts (time series)
        
        Args:
            input_sequences: List of token tensors for each time step
            metadata_sequences: Optional list of metadata for each time step
            return_uncertainty: Whether to return uncertainty estimates
        
        Returns:
            Dictionary with mood predictions and trends
        """
        self.eval()
        
        mood_scores = []
        uncertainties = []
        
        with torch.no_grad():
            for i, input_ids in enumerate(input_sequences):
                metadata = metadata_sequences[i] if metadata_sequences else None
                
                # Add batch dimension if needed
                if input_ids.dim() == 1:
                    input_ids = input_ids.unsqueeze(0)
                
                # Forward pass
                outputs = self.forward(input_ids, metadata=metadata)
                
                mood_scores.append(outputs['mood_score'].item())
                if return_uncertainty:
                    uncertainties.append(outputs['uncertainty'].item())
        
        # Calculate trend
        trend = 'stable'
        if len(mood_scores) > 1:
            recent_change = mood_scores[-1] - mood_scores[-2]
            if recent_change > 0.5:
                trend = 'improving'
            elif recent_change < -0.5:
                trend = 'declining'
        
        # Calculate moving average
        window_size = min(7, len(mood_scores))  # 7-day window
        if len(mood_scores) >= window_size:
            moving_avg = sum(mood_scores[-window_size:]) / window_size
        else:
            moving_avg = sum(mood_scores) / len(mood_scores)
        
        result = {
            'mood_scores': mood_scores,
            'current_mood': mood_scores[-1] if mood_scores else 5.0,
            'trend': trend,
            'moving_average': moving_avg,
            'sequence_length': len(mood_scores)
        }
        
        if return_uncertainty:
            result['uncertainties'] = uncertainties
            result['avg_uncertainty'] = sum(uncertainties) / len(uncertainties) if uncertainties else 0.0
        
        return result
    
    def compute_loss(
        self,
        input_ids: torch.Tensor,
        target_mood: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        metadata: Optional[Dict[str, torch.Tensor]] = None,
        loss_weights: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        """
        Computes training loss
        
        Args:
            input_ids: Token IDs [batch_size, seq_len]
            target_mood: Target mood scores [batch_size]
            attention_mask: Optional attention mask
            metadata: Optional metadata
            loss_weights: Optional sample weights
        
        Returns:
            Dictionary with loss and metrics
        """
        outputs = self.forward(input_ids, attention_mask, metadata)
        
        predicted_mood = outputs['mood_score']
        uncertainty = outputs['uncertainty']
        
        # Main regression loss (MSE)
        mse_loss = F.mse_loss(predicted_mood, target_mood, reduction='none')
        
        # Uncertainty-weighted loss
        uncertainty_weighted_loss = mse_loss / (uncertainty + 1e-6) + torch.log(uncertainty + 1e-6)
        
        # Apply sample weights if provided
        if loss_weights is not None:
            uncertainty_weighted_loss = uncertainty_weighted_loss * loss_weights
        
        # Final loss
        total_loss = uncertainty_weighted_loss.mean()
        
        # Compute metrics
        mae = F.l1_loss(predicted_mood, target_mood)
        rmse = torch.sqrt(mse_loss.mean())
        
        # Correlation coefficient
        pred_centered = predicted_mood - predicted_mood.mean()
        target_centered = target_mood - target_mood.mean()
        correlation = (pred_centered * target_centered).sum() / (
            torch.sqrt((pred_centered ** 2).sum() * (target_centered ** 2).sum()) + 1e-6
        )
        
        return {
            'loss': total_loss,
            'mse_loss': mse_loss.mean(),
            'mae': mae,
            'rmse': rmse,
            'correlation': correlation,
            'avg_uncertainty': uncertainty.mean(),
            'predictions': predicted_mood,
            'targets': target_mood
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Returns model information"""
        
        total_params = sum(p.numel() for p in self.parameters())
        trainable_params = sum(p.numel() for p in self.parameters() if p.requires_grad)
        
        return {
            'model_name': 'MoodPredictor',
            'architecture': 'BiLSTM + Attention + Metadata Fusion',
            'vocab_size': self.vocab_size,
            'embedding_dim': self.embedding_dim,
            'hidden_dim': self.hidden_dim,
            'num_layers': self.num_layers,
            'use_metadata': self.use_metadata,
            'total_parameters': total_params,
            'trainable_parameters': trainable_params,
            'model_size_mb': total_params * 4 / (1024 * 1024),
            'output_range': '1-10 (mood scale)',
            'features': [
                'bidirectional_lstm',
                'attention_pooling',
                'metadata_fusion',
                'uncertainty_estimation',
                'temporal_modeling'
            ]
        }
