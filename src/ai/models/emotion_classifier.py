"""
Emotion Classifier Model

Custom Neural Network für Emotionserkennung in Mental Health Texten.
Erkennt 7 Basis-Emotionen: Freude, Trauer, Wut, Angst, Überraschung, Ekel, Neutral.
"""

import logging
from typing import Any, Dict, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

logger = logging.getLogger(__name__)


class MultiHeadAttention(nn.Module):
    """
    Custom Multi-Head Attention für bessere Textverständnis
    """

    def __init__(self, embed_dim: int, num_heads: int, dropout: float = 0.1):
        super().__init__()

        assert embed_dim % num_heads == 0

        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads

        # Linear projections for Q, K, V
        self.q_proj = nn.Linear(embed_dim, embed_dim)
        self.k_proj = nn.Linear(embed_dim, embed_dim)
        self.v_proj = nn.Linear(embed_dim, embed_dim)

        # Output projection
        self.out_proj = nn.Linear(embed_dim, embed_dim)

        # Dropout
        self.dropout = nn.Dropout(dropout)

        # Scale factor
        self.scale = self.head_dim**-0.5

    def forward(
        self, x: torch.Tensor, mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Forward pass

        Args:
            x: Input tensor [batch_size, seq_len, embed_dim]
            mask: Optional attention mask [batch_size, seq_len]

        Returns:
            Output tensor [batch_size, seq_len, embed_dim]
        """
        batch_size, seq_len, embed_dim = x.size()

        # Compute Q, K, V
        Q = self.q_proj(x)  # [batch_size, seq_len, embed_dim]
        K = self.k_proj(x)  # [batch_size, seq_len, embed_dim]
        V = self.v_proj(x)  # [batch_size, seq_len, embed_dim]

        # Reshape for multi-head attention
        Q = Q.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        K = K.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        V = V.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        # Shape: [batch_size, num_heads, seq_len, head_dim]

        # Compute attention scores
        scores = torch.matmul(Q, K.transpose(-2, -1)) * self.scale
        # Shape: [batch_size, num_heads, seq_len, seq_len]

        # Apply mask if provided
        if mask is not None:
            mask = mask.unsqueeze(1).unsqueeze(2)  # [batch_size, 1, 1, seq_len]
            scores = scores.masked_fill(mask == 0, float("-inf"))

        # Apply softmax
        attention_weights = F.softmax(scores, dim=-1)
        attention_weights = self.dropout(attention_weights)

        # Apply attention to values
        out = torch.matmul(attention_weights, V)
        # Shape: [batch_size, num_heads, seq_len, head_dim]

        # Concatenate heads
        out = out.transpose(1, 2).contiguous().view(batch_size, seq_len, embed_dim)

        # Final projection
        out = self.out_proj(out)

        return out


class PositionalEncoding(nn.Module):
    """
    Positional Encoding für Transformer-ähnliche Architektur
    """

    def __init__(self, embed_dim: int, max_length: int = 512):
        super().__init__()

        pe = torch.zeros(max_length, embed_dim)
        position = torch.arange(0, max_length).unsqueeze(1).float()

        div_term = torch.exp(
            torch.arange(0, embed_dim, 2).float()
            * -(torch.log(torch.tensor(10000.0)) / embed_dim)
        )

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)

        self.register_buffer("pe", pe.unsqueeze(0))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Input tensor [batch_size, seq_len, embed_dim]

        Returns:
            Tensor with positional encoding added
        """
        return x + self.pe[:, : x.size(1)]


class TransformerEncoderLayer(nn.Module):
    """
    Custom Transformer Encoder Layer
    """

    def __init__(
        self, embed_dim: int, num_heads: int, ff_dim: int, dropout: float = 0.1
    ):
        super().__init__()

        # Multi-head attention
        self.self_attention = MultiHeadAttention(embed_dim, num_heads, dropout)

        # Feed-forward network
        self.ff_network = nn.Sequential(
            nn.Linear(embed_dim, ff_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(ff_dim, embed_dim),
        )

        # Layer normalization
        self.norm1 = nn.LayerNorm(embed_dim)
        self.norm2 = nn.LayerNorm(embed_dim)

        # Dropout
        self.dropout = nn.Dropout(dropout)

    def forward(
        self, x: torch.Tensor, mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Forward pass with residual connections

        Args:
            x: Input tensor [batch_size, seq_len, embed_dim]
            mask: Optional attention mask

        Returns:
            Output tensor [batch_size, seq_len, embed_dim]
        """
        # Self-attention with residual connection
        attn_out = self.self_attention(x, mask)
        x = self.norm1(x + self.dropout(attn_out))

        # Feed-forward with residual connection
        ff_out = self.ff_network(x)
        x = self.norm2(x + self.dropout(ff_out))

        return x


class EmotionClassifier(nn.Module):
    """
    Custom Emotion Classification Model

    Architektur:
    - Embedding Layer
    - Positional Encoding
    - Multiple Transformer Encoder Layers
    - Global Average Pooling
    - Classification Head
    """

    def __init__(
        self,
        vocab_size: int,
        embedding_dim: int,
        hidden_dim: int,
        num_classes: int = 7,
        num_layers: int = 4,
        num_heads: int = 8,
        ff_dim: int = None,
        dropout_rate: float = 0.1,
        max_length: int = 512,
    ):
        super().__init__()

        if ff_dim is None:
            ff_dim = hidden_dim * 4

        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        self.num_classes = num_classes
        self.num_layers = num_layers

        # Emotion labels
        self.emotion_labels = [
            "joy",  # Freude
            "sadness",  # Trauer
            "anger",  # Wut
            "fear",  # Angst
            "surprise",  # Überraschung
            "disgust",  # Ekel
            "neutral",  # Neutral
        ]

        # Embedding layer
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)

        # Positional encoding
        self.pos_encoding = PositionalEncoding(embedding_dim, max_length)

        # Input projection (if embedding_dim != hidden_dim)
        if embedding_dim != hidden_dim:
            self.input_projection = nn.Linear(embedding_dim, hidden_dim)
        else:
            self.input_projection = nn.Identity()

        # Transformer encoder layers
        self.encoder_layers = nn.ModuleList(
            [
                TransformerEncoderLayer(
                    embed_dim=hidden_dim,
                    num_heads=num_heads,
                    ff_dim=ff_dim,
                    dropout=dropout_rate,
                )
                for _ in range(num_layers)
            ]
        )

        # Classification head
        self.classifier = nn.Sequential(
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_dim // 2, num_classes),
        )

        # Initialize weights
        self._init_weights()

        logger.info(f"🧠 EmotionClassifier initialized:")
        logger.info(f"   - Vocab size: {vocab_size}")
        logger.info(f"   - Embedding dim: {embedding_dim}")
        logger.info(f"   - Hidden dim: {hidden_dim}")
        logger.info(f"   - Num classes: {num_classes}")
        logger.info(f"   - Num layers: {num_layers}")
        logger.info(f"   - Num heads: {num_heads}")

    def _init_weights(self):
        """Initialize model weights"""

        # Initialize embeddings
        nn.init.normal_(self.embedding.weight, mean=0, std=0.02)
        nn.init.constant_(self.embedding.weight[0], 0)  # Padding token

        # Initialize linear layers
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.constant_(module.bias, 0)

    def create_padding_mask(self, input_ids: torch.Tensor) -> torch.Tensor:
        """
        Creates padding mask for attention

        Args:
            input_ids: Input token IDs [batch_size, seq_len]

        Returns:
            Padding mask [batch_size, seq_len]
        """
        return (input_ids != 0).float()  # 0 is padding token

    def forward(
        self, input_ids: torch.Tensor, attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Forward pass

        Args:
            input_ids: Token IDs [batch_size, seq_len]
            attention_mask: Optional attention mask [batch_size, seq_len]

        Returns:
            Emotion logits [batch_size, num_classes]
        """
        batch_size, seq_len = input_ids.size()

        # Create attention mask if not provided
        if attention_mask is None:
            attention_mask = self.create_padding_mask(input_ids)

        # Embedding
        embeddings = self.embedding(input_ids)  # [batch_size, seq_len, embedding_dim]

        # Add positional encoding
        embeddings = self.pos_encoding(embeddings)

        # Project to hidden dimension if needed
        hidden_states = self.input_projection(
            embeddings
        )  # [batch_size, seq_len, hidden_dim]

        # Pass through transformer encoder layers
        for encoder_layer in self.encoder_layers:
            hidden_states = encoder_layer(hidden_states, attention_mask)

        # Global average pooling (considering mask)
        mask_expanded = attention_mask.unsqueeze(-1).expand_as(hidden_states)

        # Sum over sequence length, then divide by actual length
        pooled = (hidden_states * mask_expanded).sum(dim=1)  # [batch_size, hidden_dim]
        seq_lengths = attention_mask.sum(dim=1, keepdim=True)  # [batch_size, 1]
        pooled = pooled / seq_lengths.clamp(min=1)

        # Classification
        logits = self.classifier(pooled)  # [batch_size, num_classes]

        return logits

    def predict_emotion(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        return_probabilities: bool = False,
    ) -> Dict[str, Any]:
        """
        Predicts emotion with confidence scores

        Args:
            input_ids: Token IDs [batch_size, seq_len]
            attention_mask: Optional attention mask
            return_probabilities: Whether to return all probabilities

        Returns:
            Dictionary with prediction results
        """
        self.eval()

        with torch.no_grad():
            logits = self.forward(input_ids, attention_mask)
            probabilities = F.softmax(logits, dim=-1)

            # Get predictions
            predicted_classes = torch.argmax(probabilities, dim=-1)
            confidence_scores = torch.max(probabilities, dim=-1)[0]

            results = []

            for i in range(input_ids.size(0)):
                pred_class = predicted_classes[i].item()
                confidence = confidence_scores[i].item()
                emotion = self.emotion_labels[pred_class]

                result = {
                    "emotion": emotion,
                    "confidence": confidence,
                    "predicted_class": pred_class,
                }

                if return_probabilities:
                    result["probabilities"] = {
                        label: probabilities[i][j].item()
                        for j, label in enumerate(self.emotion_labels)
                    }

                results.append(result)

            return results if len(results) > 1 else results[0]

    def get_attention_weights(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        layer_idx: int = -1,
    ) -> torch.Tensor:
        """
        Extracts attention weights for visualization

        Args:
            input_ids: Token IDs [batch_size, seq_len]
            attention_mask: Optional attention mask
            layer_idx: Which layer to extract weights from (-1 for last)

        Returns:
            Attention weights [batch_size, num_heads, seq_len, seq_len]
        """
        # This would require modifying the forward pass to return attention weights
        # For now, return placeholder
        batch_size, seq_len = input_ids.size()
        num_heads = 8  # Default

        return torch.zeros(batch_size, num_heads, seq_len, seq_len)

    def get_emotion_embeddings(
        self, input_ids: torch.Tensor, attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Extracts intermediate emotion embeddings

        Args:
            input_ids: Token IDs [batch_size, seq_len]
            attention_mask: Optional attention mask

        Returns:
            Emotion embeddings [batch_size, hidden_dim]
        """
        batch_size, seq_len = input_ids.size()

        if attention_mask is None:
            attention_mask = self.create_padding_mask(input_ids)

        # Get embeddings up to the classifier
        embeddings = self.embedding(input_ids)
        embeddings = self.pos_encoding(embeddings)
        hidden_states = self.input_projection(embeddings)

        for encoder_layer in self.encoder_layers:
            hidden_states = encoder_layer(hidden_states, attention_mask)

        # Global average pooling
        mask_expanded = attention_mask.unsqueeze(-1).expand_as(hidden_states)
        pooled = (hidden_states * mask_expanded).sum(dim=1)
        seq_lengths = attention_mask.sum(dim=1, keepdim=True)
        emotion_embeddings = pooled / seq_lengths.clamp(min=1)

        return emotion_embeddings

    def compute_loss(
        self,
        input_ids: torch.Tensor,
        labels: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        class_weights: Optional[torch.Tensor] = None,
    ) -> Dict[str, torch.Tensor]:
        """
        Computes training loss

        Args:
            input_ids: Token IDs [batch_size, seq_len]
            labels: Emotion labels [batch_size]
            attention_mask: Optional attention mask
            class_weights: Optional class weights for imbalanced data

        Returns:
            Dictionary with loss and metrics
        """
        logits = self.forward(input_ids, attention_mask)

        # Cross-entropy loss
        if class_weights is not None:
            criterion = nn.CrossEntropyLoss(weight=class_weights)
        else:
            criterion = nn.CrossEntropyLoss()

        loss = criterion(logits, labels)

        # Compute accuracy
        predictions = torch.argmax(logits, dim=-1)
        accuracy = (predictions == labels).float().mean()

        # Compute per-class accuracy
        per_class_acc = {}
        for i, emotion in enumerate(self.emotion_labels):
            mask = labels == i
            if mask.sum() > 0:
                class_acc = (predictions[mask] == labels[mask]).float().mean()
                per_class_acc[emotion] = class_acc.item()

        return {
            "loss": loss,
            "accuracy": accuracy,
            "per_class_accuracy": per_class_acc,
            "logits": logits,
        }

    def get_model_info(self) -> Dict[str, Any]:
        """Returns model architecture information"""

        total_params = sum(p.numel() for p in self.parameters())
        trainable_params = sum(p.numel() for p in self.parameters() if p.requires_grad)

        return {
            "model_name": "EmotionClassifier",
            "vocab_size": self.vocab_size,
            "embedding_dim": self.embedding_dim,
            "hidden_dim": self.hidden_dim,
            "num_classes": self.num_classes,
            "num_layers": self.num_layers,
            "emotion_labels": self.emotion_labels,
            "total_parameters": total_params,
            "trainable_parameters": trainable_params,
            "model_size_mb": total_params * 4 / (1024 * 1024),  # Assuming float32
        }
