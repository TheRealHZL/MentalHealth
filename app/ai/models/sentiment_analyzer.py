"""
Sentiment Analyzer Model

CNN-basiertes Neural Network für schnelle und akkurate Sentiment-Analyse.
Optimiert für Mental Health Texte mit deutscher Sprache.
"""

import logging
import math
from typing import Any, Dict, List, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

logger = logging.getLogger(__name__)


class TextCNN1D(nn.Module):
    """
    1D Convolutional Neural Network für Text Classification
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        padding: str = "same",
        dropout: float = 0.1,
    ):
        super().__init__()

        self.conv = nn.Conv1d(
            in_channels=in_channels,
            out_channels=out_channels,
            kernel_size=kernel_size,
            padding=padding,
        )

        self.batch_norm = nn.BatchNorm1d(out_channels)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass

        Args:
            x: Input tensor [batch_size, in_channels, seq_len]

        Returns:
            Output tensor [batch_size, out_channels, seq_len]
        """
        x = self.conv(x)
        x = self.batch_norm(x)
        x = F.relu(x)
        x = self.dropout(x)
        return x


class MultiScaleCNN(nn.Module):
    """
    Multi-Scale CNN für verschiedene n-gram Patterns
    """

    def __init__(
        self,
        embed_dim: int,
        num_filters: int,
        filter_sizes: List[int],
        dropout: float = 0.1,
    ):
        super().__init__()

        self.embed_dim = embed_dim
        self.num_filters = num_filters
        self.filter_sizes = filter_sizes

        # Convolutional layers for different filter sizes
        self.convs = nn.ModuleList(
            [
                nn.Sequential(
                    nn.Conv1d(
                        in_channels=embed_dim,
                        out_channels=num_filters,
                        kernel_size=filter_size,
                        padding=0,
                    ),
                    nn.BatchNorm1d(num_filters),
                    nn.ReLU(),
                    nn.Dropout(dropout),
                )
                for filter_size in filter_sizes
            ]
        )

        # Total output dimension
        self.output_dim = len(filter_sizes) * num_filters

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass

        Args:
            x: Input tensor [batch_size, seq_len, embed_dim]

        Returns:
            Concatenated features [batch_size, total_filters]
        """
        # Transpose for conv1d: [batch_size, embed_dim, seq_len]
        x = x.transpose(1, 2)

        conv_outputs = []

        for conv in self.convs:
            # Apply convolution
            conv_out = conv(x)  # [batch_size, num_filters, conv_seq_len]

            # Global max pooling
            pooled = F.max_pool1d(conv_out, kernel_size=conv_out.size(2))
            pooled = pooled.squeeze(2)  # [batch_size, num_filters]

            conv_outputs.append(pooled)

        # Concatenate all filter outputs
        concatenated = torch.cat(conv_outputs, dim=1)

        return concatenated


class AttentionPooling1D(nn.Module):
    """
    Attention-based pooling für CNN features
    """

    def __init__(self, feature_dim: int):
        super().__init__()

        self.feature_dim = feature_dim

        # Attention mechanism
        self.attention = nn.Sequential(
            nn.Linear(feature_dim, feature_dim // 2),
            nn.Tanh(),
            nn.Linear(feature_dim // 2, 1),
        )

    def forward(
        self, features: torch.Tensor, mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Attention pooling

        Args:
            features: Feature tensor [batch_size, seq_len, feature_dim]
            mask: Optional mask [batch_size, seq_len]

        Returns:
            Pooled features [batch_size, feature_dim]
        """
        # Compute attention weights
        attention_scores = self.attention(features).squeeze(-1)  # [batch_size, seq_len]

        # Apply mask if provided
        if mask is not None:
            attention_scores = attention_scores.masked_fill(mask == 0, float("-inf"))

        # Softmax
        attention_weights = F.softmax(attention_scores, dim=-1)  # [batch_size, seq_len]

        # Weighted sum
        pooled = torch.sum(
            features * attention_weights.unsqueeze(-1), dim=1
        )  # [batch_size, feature_dim]

        return pooled


class EmotionalContextEncoder(nn.Module):
    """
    Encoder für emotionale Kontextinformationen
    """

    def __init__(self, vocab_size: int, embed_dim: int):
        super().__init__()

        # Emotion-aware word embeddings
        self.word_embeddings = nn.Embedding(vocab_size, embed_dim, padding_idx=0)

        # Emotional polarity embeddings
        self.polarity_embeddings = nn.Embedding(
            3, embed_dim
        )  # negative, neutral, positive

        # Intensity embeddings
        self.intensity_embeddings = nn.Embedding(5, embed_dim)  # 1-5 intensity levels

        # Context fusion
        self.context_fusion = nn.Sequential(
            nn.Linear(embed_dim * 3, embed_dim), nn.GELU(), nn.LayerNorm(embed_dim)
        )

    def forward(
        self,
        input_ids: torch.Tensor,
        polarity_ids: Optional[torch.Tensor] = None,
        intensity_ids: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Encode emotional context

        Args:
            input_ids: Token IDs [batch_size, seq_len]
            polarity_ids: Polarity IDs [batch_size, seq_len]
            intensity_ids: Intensity IDs [batch_size, seq_len]

        Returns:
            Enhanced embeddings [batch_size, seq_len, embed_dim]
        """
        batch_size, seq_len = input_ids.size()
        device = input_ids.device

        # Word embeddings
        word_embeds = self.word_embeddings(input_ids)

        # Default polarity and intensity if not provided
        if polarity_ids is None:
            polarity_ids = torch.ones_like(input_ids)  # neutral
        if intensity_ids is None:
            intensity_ids = torch.full_like(input_ids, 2)  # medium intensity

        # Polarity and intensity embeddings
        polarity_embeds = self.polarity_embeddings(polarity_ids)
        intensity_embeds = self.intensity_embeddings(intensity_ids)

        # Concatenate and fuse
        combined_embeds = torch.cat(
            [word_embeds, polarity_embeds, intensity_embeds], dim=-1
        )

        # Apply fusion layer
        fused_embeds = self.context_fusion(combined_embeds)

        return fused_embeds


class SentimentAnalyzer(nn.Module):
    """
    Fast Sentiment Analyzer using CNN architecture

    Architektur:
    - Emotional Context Encoder
    - Multi-Scale CNN für n-gram patterns
    - Attention Pooling
    - Multi-task Classification Head
    """

    def __init__(
        self,
        vocab_size: int,
        embedding_dim: int = 256,
        num_filters: int = 100,
        filter_sizes: List[int] = None,
        dropout_rate: float = 0.1,
        num_classes: int = 3,  # negative, neutral, positive
        max_length: int = 512,
    ):
        super().__init__()

        if filter_sizes is None:
            filter_sizes = [2, 3, 4, 5]  # Different n-gram sizes

        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.num_filters = num_filters
        self.filter_sizes = filter_sizes
        self.num_classes = num_classes
        self.max_length = max_length

        # Class labels
        self.sentiment_labels = ["negative", "neutral", "positive"]

        # Emotional context encoder
        self.context_encoder = EmotionalContextEncoder(vocab_size, embedding_dim)

        # Multi-scale CNN
        self.multi_scale_cnn = MultiScaleCNN(
            embed_dim=embedding_dim,
            num_filters=num_filters,
            filter_sizes=filter_sizes,
            dropout=dropout_rate,
        )

        # Additional CNN layers for hierarchical features
        self.hierarchical_cnns = nn.ModuleList(
            [
                TextCNN1D(
                    in_channels=embedding_dim,
                    out_channels=num_filters // 2,
                    kernel_size=kernel_size,
                    dropout=dropout_rate,
                )
                for kernel_size in [3, 5, 7]
            ]
        )

        # Attention pooling
        self.attention_pooling = AttentionPooling1D(embedding_dim)

        # Feature dimensions
        cnn_features = self.multi_scale_cnn.output_dim
        hierarchical_features = len(self.hierarchical_cnns) * (num_filters // 2)
        attention_features = embedding_dim

        total_features = cnn_features + hierarchical_features + attention_features

        # Classification layers
        self.classifier = nn.Sequential(
            nn.Linear(total_features, total_features // 2),
            nn.GELU(),
            nn.BatchNorm1d(total_features // 2),
            nn.Dropout(dropout_rate),
            nn.Linear(total_features // 2, total_features // 4),
            nn.GELU(),
            nn.BatchNorm1d(total_features // 4),
            nn.Dropout(dropout_rate),
            nn.Linear(total_features // 4, num_classes),
        )

        # Confidence estimation head
        self.confidence_head = nn.Sequential(
            nn.Linear(total_features, total_features // 4),
            nn.GELU(),
            nn.Linear(total_features // 4, 1),
            nn.Sigmoid(),
        )

        # Emotional intensity head
        self.intensity_head = nn.Sequential(
            nn.Linear(total_features, total_features // 4),
            nn.GELU(),
            nn.Linear(total_features // 4, 1),
            nn.Sigmoid(),  # 0-1 intensity
        )

        # Initialize weights
        self._init_weights()

        logger.info(f"🧠 SentimentAnalyzer initialized:")
        logger.info(f"   - Vocab size: {vocab_size}")
        logger.info(f"   - Embedding dim: {embedding_dim}")
        logger.info(f"   - Num filters: {num_filters}")
        logger.info(f"   - Filter sizes: {filter_sizes}")
        logger.info(f"   - Num classes: {num_classes}")
        logger.info(f"   - Total features: {total_features}")

    def _init_weights(self):
        """Initialize model weights"""

        # Initialize embeddings
        for module in self.modules():
            if isinstance(module, nn.Embedding):
                nn.init.normal_(module.weight, mean=0, std=0.02)
                if hasattr(module, "padding_idx") and module.padding_idx is not None:
                    nn.init.constant_(module.weight[module.padding_idx], 0)

            elif isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.constant_(module.bias, 0)

            elif isinstance(module, nn.Conv1d):
                nn.init.kaiming_normal_(
                    module.weight, mode="fan_out", nonlinearity="relu"
                )
                if module.bias is not None:
                    nn.init.constant_(module.bias, 0)

    def create_padding_mask(self, input_ids: torch.Tensor) -> torch.Tensor:
        """Creates padding mask"""
        return (input_ids != 0).float()

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        polarity_context: Optional[torch.Tensor] = None,
        intensity_context: Optional[torch.Tensor] = None,
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass

        Args:
            input_ids: Token IDs [batch_size, seq_len]
            attention_mask: Padding mask [batch_size, seq_len]
            polarity_context: Polarity context [batch_size, seq_len]
            intensity_context: Intensity context [batch_size, seq_len]

        Returns:
            Dictionary with predictions and features
        """
        batch_size, seq_len = input_ids.size()

        # Create attention mask if not provided
        if attention_mask is None:
            attention_mask = self.create_padding_mask(input_ids)

        # Emotional context encoding
        embeddings = self.context_encoder(
            input_ids, polarity_context, intensity_context
        )  # [batch_size, seq_len, embedding_dim]

        # Multi-scale CNN features
        cnn_features = self.multi_scale_cnn(embeddings)  # [batch_size, cnn_features]

        # Hierarchical CNN features
        hierarchical_features = []
        embeddings_transposed = embeddings.transpose(
            1, 2
        )  # [batch_size, embedding_dim, seq_len]

        for hierarchical_cnn in self.hierarchical_cnns:
            h_features = hierarchical_cnn(embeddings_transposed)
            # Global max pooling
            h_pooled = F.adaptive_max_pool1d(h_features, 1).squeeze(2)
            hierarchical_features.append(h_pooled)

        hierarchical_features = torch.cat(hierarchical_features, dim=1)

        # Attention pooling features
        attention_features = self.attention_pooling(embeddings, attention_mask)

        # Concatenate all features
        all_features = torch.cat(
            [cnn_features, hierarchical_features, attention_features], dim=1
        )

        # Classification
        sentiment_logits = self.classifier(all_features)

        # Confidence and intensity estimation
        confidence = self.confidence_head(all_features)
        intensity = self.intensity_head(all_features)

        return {
            "sentiment_logits": sentiment_logits,
            "confidence_scores": confidence.squeeze(-1),
            "intensity_scores": intensity.squeeze(-1),
            "features": all_features,
        }

    def predict_sentiment(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        return_probabilities: bool = False,
        return_confidence: bool = True,
    ) -> Dict[str, Any]:
        """
        Predicts sentiment with confidence and intensity

        Args:
            input_ids: Token IDs [batch_size, seq_len]
            attention_mask: Padding mask
            return_probabilities: Whether to return class probabilities
            return_confidence: Whether to return confidence scores

        Returns:
            Dictionary with sentiment predictions
        """
        self.eval()

        with torch.no_grad():
            outputs = self.forward(input_ids, attention_mask)

            sentiment_logits = outputs["sentiment_logits"]
            probabilities = F.softmax(sentiment_logits, dim=-1)

            # Get predictions
            predicted_classes = torch.argmax(probabilities, dim=-1)
            class_probabilities = torch.max(probabilities, dim=-1)[0]

            results = []

            for i in range(input_ids.size(0)):
                pred_class = predicted_classes[i].item()
                class_prob = class_probabilities[i].item()
                sentiment = self.sentiment_labels[pred_class]

                result = {
                    "sentiment": sentiment,
                    "predicted_class": pred_class,
                    "score": class_prob,
                }

                if return_confidence:
                    confidence = outputs["confidence_scores"][i].item()
                    intensity = outputs["intensity_scores"][i].item()

                    result.update({"confidence": confidence, "intensity": intensity})

                if return_probabilities:
                    result["probabilities"] = {
                        label: probabilities[i][j].item()
                        for j, label in enumerate(self.sentiment_labels)
                    }

                results.append(result)

            return results if len(results) > 1 else results[0]

    def analyze_emotional_aspects(
        self, input_ids: torch.Tensor, attention_mask: Optional[torch.Tensor] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive emotional analysis

        Args:
            input_ids: Token IDs [batch_size, seq_len]
            attention_mask: Padding mask

        Returns:
            Detailed emotional analysis
        """
        self.eval()

        with torch.no_grad():
            outputs = self.forward(input_ids, attention_mask)
            sentiment_prediction = self.predict_sentiment(
                input_ids,
                attention_mask,
                return_probabilities=True,
                return_confidence=True,
            )

            # Additional analysis
            sentiment_logits = outputs["sentiment_logits"]
            probabilities = F.softmax(sentiment_logits, dim=-1)

            # Emotional polarity score (-1 to 1)
            polarity_score = (
                probabilities[:, 2] - probabilities[:, 0]
            )  # positive - negative

            # Emotional stability (how close to neutral)
            stability = probabilities[:, 1]  # neutral probability

            # Emotional arousal (distance from neutral)
            arousal = 1.0 - stability

            results = []

            for i in range(input_ids.size(0)):
                result = {
                    "basic_sentiment": (
                        sentiment_prediction
                        if isinstance(sentiment_prediction, dict)
                        else sentiment_prediction[i]
                    ),
                    "polarity_score": polarity_score[
                        i
                    ].item(),  # -1 (negative) to 1 (positive)
                    "emotional_stability": stability[
                        i
                    ].item(),  # 0 (unstable) to 1 (stable)
                    "emotional_arousal": arousal[i].item(),  # 0 (calm) to 1 (intense)
                    "confidence": outputs["confidence_scores"][i].item(),
                    "intensity": outputs["intensity_scores"][i].item(),
                }

                # Emotional state classification
                if result["polarity_score"] > 0.3:
                    emotional_state = "positive"
                elif result["polarity_score"] < -0.3:
                    emotional_state = "negative"
                else:
                    emotional_state = "neutral"

                if result["emotional_arousal"] > 0.7:
                    emotional_state += "_high_arousal"
                elif result["emotional_arousal"] < 0.3:
                    emotional_state += "_low_arousal"

                result["emotional_state"] = emotional_state

                results.append(result)

            return results if len(results) > 1 else results[0]

    def compute_loss(
        self,
        input_ids: torch.Tensor,
        sentiment_labels: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        confidence_labels: Optional[torch.Tensor] = None,
        intensity_labels: Optional[torch.Tensor] = None,
        class_weights: Optional[torch.Tensor] = None,
    ) -> Dict[str, torch.Tensor]:
        """
        Computes multi-task training loss

        Args:
            input_ids: Token IDs [batch_size, seq_len]
            sentiment_labels: Sentiment labels [batch_size]
            attention_mask: Padding mask
            confidence_labels: Confidence labels [batch_size]
            intensity_labels: Intensity labels [batch_size]
            class_weights: Class weights for imbalanced data

        Returns:
            Dictionary with losses and metrics
        """
        outputs = self.forward(input_ids, attention_mask)

        sentiment_logits = outputs["sentiment_logits"]
        predicted_confidence = outputs["confidence_scores"]
        predicted_intensity = outputs["intensity_scores"]

        # Sentiment classification loss
        if class_weights is not None:
            criterion = nn.CrossEntropyLoss(weight=class_weights)
        else:
            criterion = nn.CrossEntropyLoss()

        sentiment_loss = criterion(sentiment_logits, sentiment_labels)

        total_loss = sentiment_loss
        loss_dict = {"sentiment_loss": sentiment_loss}

        # Confidence loss
        if confidence_labels is not None:
            confidence_loss = F.mse_loss(predicted_confidence, confidence_labels)
            total_loss += 0.1 * confidence_loss
            loss_dict["confidence_loss"] = confidence_loss

        # Intensity loss
        if intensity_labels is not None:
            intensity_loss = F.mse_loss(predicted_intensity, intensity_labels)
            total_loss += 0.1 * intensity_loss
            loss_dict["intensity_loss"] = intensity_loss

        # Compute metrics
        predictions = torch.argmax(sentiment_logits, dim=-1)
        accuracy = (predictions == sentiment_labels).float().mean()

        # Per-class accuracy
        per_class_acc = {}
        for i, label in enumerate(self.sentiment_labels):
            mask = sentiment_labels == i
            if mask.sum() > 0:
                class_acc = (predictions[mask] == sentiment_labels[mask]).float().mean()
                per_class_acc[label] = class_acc.item()

        loss_dict.update(
            {
                "total_loss": total_loss,
                "accuracy": accuracy,
                "per_class_accuracy": per_class_acc,
                "predictions": predictions,
                "targets": sentiment_labels,
            }
        )

        return loss_dict

    def get_model_info(self) -> Dict[str, Any]:
        """Returns model information"""

        total_params = sum(p.numel() for p in self.parameters())
        trainable_params = sum(p.numel() for p in self.parameters() if p.requires_grad)

        return {
            "model_name": "SentimentAnalyzer",
            "architecture": "Multi-Scale CNN + Attention",
            "vocab_size": self.vocab_size,
            "embedding_dim": self.embedding_dim,
            "num_filters": self.num_filters,
            "filter_sizes": self.filter_sizes,
            "num_classes": self.num_classes,
            "sentiment_labels": self.sentiment_labels,
            "total_parameters": total_params,
            "trainable_parameters": trainable_params,
            "model_size_mb": total_params * 4 / (1024 * 1024),
            "features": [
                "multi_scale_cnn",
                "emotional_context_encoding",
                "attention_pooling",
                "confidence_estimation",
                "intensity_scoring",
                "hierarchical_features",
                "multi_task_learning",
            ],
        }
