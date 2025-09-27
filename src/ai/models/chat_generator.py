"""
Chat Generator Model

Custom Transformer für empathische Chat-Antworten.
Generiert einfühlsame, sichere und hilfreiche Responses für Mental Health Support.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Any, Optional, List, Tuple
import logging
import math
import random

logger = logging.getLogger(__name__)

class MultiHeadAttention(nn.Module):
    """
    Optimized Multi-Head Attention für Chat Generation
    """
    
    def __init__(
        self, 
        embed_dim: int, 
        num_heads: int, 
        dropout: float = 0.1,
        is_causal: bool = True
    ):
        super().__init__()
        
        assert embed_dim % num_heads == 0
        
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        self.is_causal = is_causal
        
        # Combined QKV projection for efficiency
        self.qkv_proj = nn.Linear(embed_dim, 3 * embed_dim)
        
        # Output projection
        self.out_proj = nn.Linear(embed_dim, embed_dim)
        
        # Dropout
        self.dropout = nn.Dropout(dropout)
        
        # Scale factor
        self.scale = self.head_dim ** -0.5
        
        # Register causal mask buffer
        if is_causal:
            self.register_buffer(
                "causal_mask",
                torch.tril(torch.ones(1024, 1024)).view(1, 1, 1024, 1024)
            )
    
    def forward(
        self, 
        x: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        past_key_value: Optional[Tuple[torch.Tensor, torch.Tensor]] = None
    ) -> Tuple[torch.Tensor, Optional[Tuple[torch.Tensor, torch.Tensor]]]:
        """
        Forward pass with optional past key-value caching
        
        Args:
            x: Input tensor [batch_size, seq_len, embed_dim]
            attention_mask: Optional attention mask [batch_size, seq_len]
            past_key_value: Optional cached (key, value) from previous steps
        
        Returns:
            output: Attention output [batch_size, seq_len, embed_dim]
            present_key_value: Current (key, value) for caching
        """
        batch_size, seq_len, embed_dim = x.size()
        
        # Compute Q, K, V
        qkv = self.qkv_proj(x)  # [batch_size, seq_len, 3 * embed_dim]
        qkv = qkv.view(batch_size, seq_len, 3, self.num_heads, self.head_dim)
        qkv = qkv.permute(2, 0, 3, 1, 4)  # [3, batch_size, num_heads, seq_len, head_dim]
        
        q, k, v = qkv[0], qkv[1], qkv[2]
        
        # Handle past key-value caching
        if past_key_value is not None:
            past_k, past_v = past_key_value
            k = torch.cat([past_k, k], dim=-2)
            v = torch.cat([past_v, v], dim=-2)
        
        present_key_value = (k, v)
        
        # Compute attention scores
        scores = torch.matmul(q, k.transpose(-2, -1)) * self.scale
        # Shape: [batch_size, num_heads, seq_len, full_seq_len]
        
        full_seq_len = k.size(-2)
        
        # Apply causal mask for autoregressive generation
        if self.is_causal:
            causal_mask = self.causal_mask[:, :, :seq_len, :full_seq_len]
            scores = scores.masked_fill(causal_mask == 0, float('-inf'))
        
        # Apply attention mask if provided
        if attention_mask is not None:
            # Expand mask for multi-head attention
            mask = attention_mask.unsqueeze(1).unsqueeze(2)  # [batch_size, 1, 1, full_seq_len]
            scores = scores.masked_fill(mask == 0, float('-inf'))
        
        # Softmax and dropout
        attention_weights = F.softmax(scores, dim=-1)
        attention_weights = self.dropout(attention_weights)
        
        # Apply attention to values
        out = torch.matmul(attention_weights, v)
        # Shape: [batch_size, num_heads, seq_len, head_dim]
        
        # Concatenate heads
        out = out.transpose(1, 2).contiguous().view(batch_size, seq_len, embed_dim)
        
        # Final projection
        out = self.out_proj(out)
        
        return out, present_key_value

class FeedForwardNetwork(nn.Module):
    """
    Enhanced Feed-Forward Network mit GLU activation
    """
    
    def __init__(self, embed_dim: int, ff_dim: int, dropout: float = 0.1):
        super().__init__()
        
        # Gated Linear Unit (GLU) für bessere Performance
        self.gate_proj = nn.Linear(embed_dim, ff_dim)
        self.up_proj = nn.Linear(embed_dim, ff_dim)
        self.down_proj = nn.Linear(ff_dim, embed_dim)
        
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """GLU-based feed-forward"""
        gate = F.gelu(self.gate_proj(x))
        up = self.up_proj(x)
        hidden = gate * up
        hidden = self.dropout(hidden)
        return self.down_proj(hidden)

class TransformerDecoderLayer(nn.Module):
    """
    Transformer Decoder Layer für autoregressive Generation
    """
    
    def __init__(
        self,
        embed_dim: int,
        num_heads: int,
        ff_dim: int,
        dropout: float = 0.1
    ):
        super().__init__()
        
        # Self-attention
        self.self_attention = MultiHeadAttention(
            embed_dim, num_heads, dropout, is_causal=True
        )
        
        # Feed-forward network
        self.feed_forward = FeedForwardNetwork(embed_dim, ff_dim, dropout)
        
        # Layer normalization (Pre-LN architecture)
        self.norm1 = nn.LayerNorm(embed_dim)
        self.norm2 = nn.LayerNorm(embed_dim)
        
        # Dropout
        self.dropout = nn.Dropout(dropout)
    
    def forward(
        self,
        x: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        past_key_value: Optional[Tuple[torch.Tensor, torch.Tensor]] = None
    ) -> Tuple[torch.Tensor, Optional[Tuple[torch.Tensor, torch.Tensor]]]:
        """
        Forward pass with residual connections
        
        Args:
            x: Input tensor [batch_size, seq_len, embed_dim]
            attention_mask: Optional attention mask
            past_key_value: Optional cached key-value
        
        Returns:
            output: Layer output [batch_size, seq_len, embed_dim]
            present_key_value: Current key-value for caching
        """
        # Pre-layer norm + self-attention + residual
        residual = x
        x = self.norm1(x)
        attn_out, present_key_value = self.self_attention(x, attention_mask, past_key_value)
        x = residual + self.dropout(attn_out)
        
        # Pre-layer norm + feed-forward + residual
        residual = x
        x = self.norm2(x)
        ff_out = self.feed_forward(x)
        x = residual + self.dropout(ff_out)
        
        return x, present_key_value

class EmpathyEncoder(nn.Module):
    """
    Special encoder für empathische Kontext-Verarbeitung
    """
    
    def __init__(self, embed_dim: int, num_emotions: int = 7):
        super().__init__()
        
        self.embed_dim = embed_dim
        self.num_emotions = num_emotions
        
        # Emotion embeddings
        self.emotion_embeddings = nn.Embedding(num_emotions, embed_dim)
        
        # Empathy context processor
        self.empathy_processor = nn.Sequential(
            nn.Linear(embed_dim, embed_dim),
            nn.GELU(),
            nn.Linear(embed_dim, embed_dim)
        )
        
        # Context gate
        self.context_gate = nn.Sequential(
            nn.Linear(embed_dim * 2, embed_dim),
            nn.Sigmoid()
        )
    
    def forward(
        self, 
        text_embeds: torch.Tensor,
        emotion_ids: Optional[torch.Tensor] = None,
        mood_scores: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Encode empathetic context
        
        Args:
            text_embeds: Text embeddings [batch_size, seq_len, embed_dim]
            emotion_ids: Emotion IDs [batch_size]
            mood_scores: Mood scores [batch_size]
        
        Returns:
            Enhanced embeddings with empathetic context
        """
        batch_size, seq_len, embed_dim = text_embeds.size()
        
        # Process empathy context
        empathy_context = self.empathy_processor(text_embeds)
        
        # Add emotion information if available
        if emotion_ids is not None:
            emotion_embeds = self.emotion_embeddings(emotion_ids)  # [batch_size, embed_dim]
            emotion_embeds = emotion_embeds.unsqueeze(1).expand(-1, seq_len, -1)
            
            # Gated fusion
            combined = torch.cat([empathy_context, emotion_embeds], dim=-1)
            gate = self.context_gate(combined)
            empathy_context = empathy_context * gate + emotion_embeds * (1 - gate)
        
        # Add mood information if available
        if mood_scores is not None:
            # Normalize mood scores to [-1, 1] range
            mood_normalized = (mood_scores - 5.5) / 4.5  # [batch_size]
            mood_embeds = mood_normalized.unsqueeze(1).unsqueeze(2).expand(-1, seq_len, embed_dim)
            empathy_context = empathy_context + 0.1 * mood_embeds
        
        return text_embeds + empathy_context

class ChatGenerator(nn.Module):
    """
    Chat Generator Model für empathische Mental Health Responses
    
    Architektur:
    - Token Embedding + Positional Encoding
    - Empathy Encoder für Kontext-Verständnis
    - Multi-layer Transformer Decoder
    - Safety-aware Generation Head
    """
    
    def __init__(
        self,
        vocab_size: int,
        embedding_dim: int = 512,
        hidden_dim: int = 512,
        num_layers: int = 6,
        num_heads: int = 8,
        ff_dim: int = 2048,
        dropout_rate: float = 0.1,
        max_length: int = 512,
        pad_token_id: int = 0,
        bos_token_id: int = 2,
        eos_token_id: int = 3
    ):
        super().__init__()
        
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.num_heads = num_heads
        self.max_length = max_length
        self.pad_token_id = pad_token_id
        self.bos_token_id = bos_token_id
        self.eos_token_id = eos_token_id
        
        # Token embedding
        self.token_embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=pad_token_id)
        
        # Positional embedding
        self.pos_embedding = nn.Embedding(max_length, embedding_dim)
        
        # Input projection (if embedding_dim != hidden_dim)
        if embedding_dim != hidden_dim:
            self.input_projection = nn.Linear(embedding_dim, hidden_dim)
        else:
            self.input_projection = nn.Identity()
        
        # Empathy encoder
        self.empathy_encoder = EmpathyEncoder(hidden_dim)
        
        # Transformer decoder layers
        self.decoder_layers = nn.ModuleList([
            TransformerDecoderLayer(
                embed_dim=hidden_dim,
                num_heads=num_heads,
                ff_dim=ff_dim,
                dropout=dropout_rate
            )
            for _ in range(num_layers)
        ])
        
        # Final layer norm
        self.final_norm = nn.LayerNorm(hidden_dim)
        
        # Language modeling head
        self.lm_head = nn.Linear(hidden_dim, vocab_size, bias=False)
        
        # Safety classifier head
        self.safety_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_dim // 2, 2),  # safe/unsafe
        )
        
        # Empathy score head
        self.empathy_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 4),
            nn.GELU(),
            nn.Linear(hidden_dim // 4, 1),
            nn.Sigmoid()
        )
        
        # Initialize weights
        self._init_weights()
        
        logger.info(f"🧠 ChatGenerator initialized:")
        logger.info(f"   - Vocab size: {vocab_size}")
        logger.info(f"   - Embedding dim: {embedding_dim}")
        logger.info(f"   - Hidden dim: {hidden_dim}")
        logger.info(f"   - Num layers: {num_layers}")
        logger.info(f"   - Num heads: {num_heads}")
        logger.info(f"   - Max length: {max_length}")
    
    def _init_weights(self):
        """Initialize model weights"""
        
        # Initialize embeddings
        nn.init.normal_(self.token_embedding.weight, mean=0, std=0.02)
        nn.init.normal_(self.pos_embedding.weight, mean=0, std=0.02)
        
        # Initialize linear layers
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.constant_(module.bias, 0)
        
        # Tie token embedding and lm_head weights
        self.lm_head.weight = self.token_embedding.weight
    
    def create_attention_mask(self, input_ids: torch.Tensor) -> torch.Tensor:
        """Creates attention mask for padding tokens"""
        return (input_ids != self.pad_token_id).float()
    
    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        past_key_values: Optional[List[Tuple[torch.Tensor, torch.Tensor]]] = None,
        emotion_context: Optional[torch.Tensor] = None,
        mood_context: Optional[torch.Tensor] = None,
        return_safety_scores: bool = False
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass
        
        Args:
            input_ids: Token IDs [batch_size, seq_len]
            attention_mask: Attention mask [batch_size, seq_len]
            past_key_values: Cached key-values for efficient generation
            emotion_context: Emotion context [batch_size]
            mood_context: Mood context [batch_size]
            return_safety_scores: Whether to compute safety scores
        
        Returns:
            Dictionary with logits and optional safety/empathy scores
        """
        batch_size, seq_len = input_ids.size()
        device = input_ids.device
        
        # Create attention mask if not provided
        if attention_mask is None:
            attention_mask = self.create_attention_mask(input_ids)
        
        # Handle past key values for efficient generation
        if past_key_values is not None:
            past_length = past_key_values[0][0].size(-2)
            position_ids = torch.arange(
                past_length, past_length + seq_len, 
                dtype=torch.long, device=device
            ).unsqueeze(0)
        else:
            position_ids = torch.arange(seq_len, dtype=torch.long, device=device).unsqueeze(0)
        
        # Token and positional embeddings
        token_embeds = self.token_embedding(input_ids)
        pos_embeds = self.pos_embedding(position_ids)
        embeddings = token_embeds + pos_embeds
        
        # Project to hidden dimension
        hidden_states = self.input_projection(embeddings)
        
        # Apply empathy encoding
        hidden_states = self.empathy_encoder(
            hidden_states, emotion_context, mood_context
        )
        
        # Pass through transformer decoder layers
        present_key_values = []
        
        for i, decoder_layer in enumerate(self.decoder_layers):
            past_key_value = past_key_values[i] if past_key_values else None
            
            hidden_states, present_key_value = decoder_layer(
                hidden_states, attention_mask, past_key_value
            )
            
            present_key_values.append(present_key_value)
        
        # Final layer norm
        hidden_states = self.final_norm(hidden_states)
        
        # Language modeling head
        logits = self.lm_head(hidden_states)
        
        outputs = {
            'logits': logits,
            'past_key_values': present_key_values,
            'hidden_states': hidden_states
        }
        
        # Optional safety and empathy scoring
        if return_safety_scores:
            # Use last token's hidden state for classification
            last_hidden = hidden_states[:, -1, :]  # [batch_size, hidden_dim]
            
            safety_logits = self.safety_head(last_hidden)
            safety_scores = F.softmax(safety_logits, dim=-1)
            
            empathy_scores = self.empathy_head(last_hidden)
            
            outputs.update({
                'safety_scores': safety_scores,
                'empathy_scores': empathy_scores
            })
        
        return outputs
    
    def generate(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        max_length: int = 200,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
        repetition_penalty: float = 1.1,
        emotion_context: Optional[torch.Tensor] = None,
        mood_context: Optional[torch.Tensor] = None,
        safety_filter: bool = True
    ) -> Dict[str, Any]:
        """
        Autoregressive text generation mit Safety-Filtering
        
        Args:
            input_ids: Input token IDs [batch_size, seq_len]
            attention_mask: Attention mask
            max_length: Maximum generation length
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            repetition_penalty: Repetition penalty
            emotion_context: Emotion context for empathy
            mood_context: Mood context for empathy
            safety_filter: Whether to apply safety filtering
        
        Returns:
            Generated text and metadata
        """
        self.eval()
        
        batch_size = input_ids.size(0)
        device = input_ids.device
        
        # Initialize generation
        generated_ids = input_ids.clone()
        past_key_values = None
        
        # Safety tracking
        unsafe_generations = 0
        max_unsafe_attempts = 3
        
        with torch.no_grad():
            for step in range(max_length):
                # Forward pass
                outputs = self.forward(
                    input_ids=generated_ids[:, -1:] if past_key_values else generated_ids,
                    past_key_values=past_key_values,
                    emotion_context=emotion_context,
                    mood_context=mood_context,
                    return_safety_scores=safety_filter
                )
                
                logits = outputs['logits'][:, -1, :]  # [batch_size, vocab_size]
                past_key_values = outputs['past_key_values']
                
                # Apply repetition penalty
                if repetition_penalty != 1.0:
                    for i in range(batch_size):
                        for token_id in set(generated_ids[i].tolist()):
                            if logits[i, token_id] < 0:
                                logits[i, token_id] *= repetition_penalty
                            else:
                                logits[i, token_id] /= repetition_penalty
                
                # Apply temperature
                if temperature != 1.0:
                    logits = logits / temperature
                
                # Top-k filtering
                if top_k > 0:
                    indices_to_remove = logits < torch.topk(logits, top_k)[0][..., -1, None]
                    logits[indices_to_remove] = float('-inf')
                
                # Top-p (nucleus) filtering
                if top_p < 1.0:
                    sorted_logits, sorted_indices = torch.sort(logits, descending=True)
                    cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)
                    
                    # Remove tokens with cumulative probability above the threshold
                    sorted_indices_to_remove = cumulative_probs > top_p
                    sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
                    sorted_indices_to_remove[..., 0] = 0
                    
                    indices_to_remove = torch.zeros_like(logits, dtype=torch.bool)
                    indices_to_remove.scatter_(1, sorted_indices, sorted_indices_to_remove)
                    logits[indices_to_remove] = float('-inf')
                
                # Sample next token
                probs = F.softmax(logits, dim=-1)
                next_tokens = torch.multinomial(probs, num_samples=1)
                
                # Safety check if enabled
                if safety_filter and 'safety_scores' in outputs:
                    safety_scores = outputs['safety_scores']
                    is_safe = safety_scores[:, 0] > 0.5  # Index 0 = safe
                    
                    if not is_safe.all():
                        unsafe_generations += 1
                        if unsafe_generations < max_unsafe_attempts:
                            # Try again with more conservative sampling
                            logits = logits / (temperature * 1.5)  # Lower temperature
                            probs = F.softmax(logits, dim=-1)
                            next_tokens = torch.multinomial(probs, num_samples=1)
                        else:
                            # Force safe token (e.g., period)
                            next_tokens = torch.full_like(next_tokens, self.eos_token_id)
                
                # Append generated token
                generated_ids = torch.cat([generated_ids, next_tokens], dim=-1)
                
                # Check for EOS token
                if (next_tokens == self.eos_token_id).all():
                    break
        
        # Remove input tokens from generated sequence
        input_length = input_ids.size(1)
        generated_tokens = generated_ids[:, input_length:]
        
        return {
            'generated_ids': generated_tokens,
            'full_sequence': generated_ids,
            'generation_length': generated_tokens.size(1),
            'unsafe_attempts': unsafe_generations,
            'finished_by_eos': (next_tokens == self.eos_token_id).all().item()
        }
    
    def compute_loss(
        self,
        input_ids: torch.Tensor,
        labels: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        safety_labels: Optional[torch.Tensor] = None,
        empathy_labels: Optional[torch.Tensor] = None,
        emotion_context: Optional[torch.Tensor] = None,
        mood_context: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        """
        Computes training loss with multiple objectives
        
        Args:
            input_ids: Input token IDs [batch_size, seq_len]
            labels: Target token IDs [batch_size, seq_len]
            attention_mask: Attention mask
            safety_labels: Safety labels [batch_size] (0=unsafe, 1=safe)
            empathy_labels: Empathy scores [batch_size] (0-1)
            emotion_context: Emotion context
            mood_context: Mood context
        
        Returns:
            Dictionary with losses and metrics
        """
        outputs = self.forward(
            input_ids=input_ids,
            attention_mask=attention_mask,
            emotion_context=emotion_context,
            mood_context=mood_context,
            return_safety_scores=(safety_labels is not None or empathy_labels is not None)
        )
        
        logits = outputs['logits']
        
        # Language modeling loss
        shift_logits = logits[..., :-1, :].contiguous()
        shift_labels = labels[..., 1:].contiguous()
        
        lm_loss = F.cross_entropy(
            shift_logits.view(-1, shift_logits.size(-1)),
            shift_labels.view(-1),
            ignore_index=self.pad_token_id
        )
        
        total_loss = lm_loss
        loss_dict = {'lm_loss': lm_loss}
        
        # Safety loss
        if safety_labels is not None and 'safety_scores' in outputs:
            safety_loss = F.cross_entropy(outputs['safety_scores'], safety_labels)
            total_loss += 0.1 * safety_loss  # Weight safety loss
            loss_dict['safety_loss'] = safety_loss
        
        # Empathy loss
        if empathy_labels is not None and 'empathy_scores' in outputs:
            empathy_loss = F.mse_loss(
                outputs['empathy_scores'].squeeze(-1), 
                empathy_labels.float()
            )
            total_loss += 0.1 * empathy_loss  # Weight empathy loss
            loss_dict['empathy_loss'] = empathy_loss
        
        # Compute perplexity
        perplexity = torch.exp(lm_loss)
        
        loss_dict.update({
            'total_loss': total_loss,
            'perplexity': perplexity
        })
        
        return loss_dict
    
    def get_model_info(self) -> Dict[str, Any]:
        """Returns model information"""
        
        total_params = sum(p.numel() for p in self.parameters())
        trainable_params = sum(p.numel() for p in self.parameters() if p.requires_grad)
        
        return {
            'model_name': 'ChatGenerator',
            'architecture': 'Transformer Decoder + Empathy Encoder',
            'vocab_size': self.vocab_size,
            'embedding_dim': self.embedding_dim,
            'hidden_dim': self.hidden_dim,
            'num_layers': self.num_layers,
            'num_heads': self.num_heads,
            'max_length': self.max_length,
            'total_parameters': total_params,
            'trainable_parameters': trainable_params,
            'model_size_mb': total_params * 4 / (1024 * 1024),
            'features': [
                'autoregressive_generation',
                'empathy_encoding',
                'safety_filtering',
                'multi_objective_training',
                'context_aware_responses',
                'nucleus_sampling',
                'repetition_penalty'
            ]
        }
