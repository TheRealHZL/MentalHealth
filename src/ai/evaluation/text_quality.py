"""
Text Quality Evaluator

Evaluiert Textqualität mit verschiedenen Metriken (BLEU, ROUGE, Perplexity)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional
import numpy as np
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class TextQualityEvaluator:
    """
    Evaluiert Textqualität mit verschiedenen Metriken
    """
    
    def __init__(self):
        self.n_gram_cache = {}
        
    def compute_perplexity(
        self, 
        model: nn.Module, 
        input_ids: torch.Tensor, 
        labels: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> float:
        """
        Berechnet Perplexity des Modells
        
        Args:
            model: Chat Generator Model
            input_ids: Input token IDs [batch_size, seq_len]
            labels: Target token IDs [batch_size, seq_len]
            attention_mask: Attention mask [batch_size, seq_len]
        
        Returns:
            Perplexity value
        """
        
        model.eval()
        with torch.no_grad():
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask
            )
            
            logits = outputs['logits']
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = labels[..., 1:].contiguous()
            
            loss = F.cross_entropy(
                shift_logits.view(-1, shift_logits.size(-1)),
                shift_labels.view(-1),
                ignore_index=0,  # pad_token_id
                reduction='mean'
            )
            
            perplexity = torch.exp(loss).item()
            
        return perplexity
    
    def compute_bleu_score(
        self, 
        predictions: List[str], 
        references: List[str],
        max_n: int = 4
    ) -> float:
        """
        Berechnet BLEU Score
        
        Args:
            predictions: Liste von Vorhersagen
            references: Liste von Referenz-Texten
            max_n: Maximale n-gram Größe
        
        Returns:
            BLEU score (0-1)
        """
        
        if len(predictions) != len(references):
            raise ValueError("Predictions and references must have same length")
        
        total_score = 0.0
        
        for pred, ref in zip(predictions, references):
            pred_tokens = pred.lower().split()
            ref_tokens = ref.lower().split()
            
            if not pred_tokens or not ref_tokens:
                continue
            
            # Compute n-gram precisions
            precisions = []
            
            for n in range(1, max_n + 1):
                pred_ngrams = self._get_ngrams(pred_tokens, n)
                ref_ngrams = self._get_ngrams(ref_tokens, n)
                
                if not pred_ngrams:
                    precisions.append(0.0)
                    continue
                
                overlap = 0
                for ngram in pred_ngrams:
                    if ngram in ref_ngrams:
                        overlap += min(pred_ngrams[ngram], ref_ngrams[ngram])
                
                precision = overlap / sum(pred_ngrams.values())
                precisions.append(precision)
            
            # Brevity penalty
            bp = min(1.0, len(pred_tokens) / len(ref_tokens)) if ref_tokens else 0.0
            
            # Geometric mean of precisions
            if any(p > 0 for p in precisions):
                log_precisions = [np.log(p) if p > 0 else -float('inf') for p in precisions]
                avg_log_precision = sum(log_precisions) / len(log_precisions)
                bleu = bp * np.exp(avg_log_precision)
            else:
                bleu = 0.0
            
            total_score += bleu
        
        return total_score / len(predictions) if predictions else 0.0
    
    def compute_rouge_scores(
        self, 
        predictions: List[str], 
        references: List[str]
    ) -> Dict[str, float]:
        """
        Berechnet ROUGE Scores (simplified implementation)
        
        Args:
            predictions: Liste von Vorhersagen
            references: Liste von Referenz-Texten
        
        Returns:
            Dictionary mit ROUGE-1, ROUGE-2, ROUGE-L scores
        """
        
        rouge_scores = {'rouge-1': 0.0, 'rouge-2': 0.0, 'rouge-L': 0.0}
        
        for pred, ref in zip(predictions, references):
            pred_tokens = set(pred.lower().split())
            ref_tokens = set(ref.lower().split())
            
            if not ref_tokens:
                continue
            
            # ROUGE-1 (unigram overlap)
            overlap_1 = len(pred_tokens & ref_tokens)
            rouge_1 = overlap_1 / len(ref_tokens) if ref_tokens else 0.0
            rouge_scores['rouge-1'] += rouge_1
            
            # ROUGE-2 (bigram overlap)
            pred_bigrams = set(self._get_ngrams(pred.lower().split(), 2).keys())
            ref_bigrams = set(self._get_ngrams(ref.lower().split(), 2).keys())
            
            overlap_2 = len(pred_bigrams & ref_bigrams)
            rouge_2 = overlap_2 / len(ref_bigrams) if ref_bigrams else 0.0
            rouge_scores['rouge-2'] += rouge_2
            
            # ROUGE-L (longest common subsequence) - simplified as ROUGE-1
            rouge_scores['rouge-L'] += rouge_1
        
        # Average over all samples
        num_samples = len(predictions)
        if num_samples > 0:
            for key in rouge_scores:
                rouge_scores[key] /= num_samples
        
        return rouge_scores
    
    def compute_semantic_similarity(
        self, 
        predictions: List[str], 
        references: List[str]
    ) -> float:
        """
        Berechnet semantische Ähnlichkeit (vereinfacht)
        
        Args:
            predictions: Liste von Vorhersagen
            references: Liste von Referenz-Texten
        
        Returns:
            Semantic similarity score (0-1)
        """
        
        # Vereinfachte semantische Ähnlichkeit basierend auf Schlüsselwörtern
        semantic_keywords = [
            'help', 'support', 'understand', 'feel', 'emotion', 'mood',
            'therapy', 'counseling', 'professional', 'mental health',
            'anxiety', 'depression', 'stress', 'coping', 'strategy'
        ]
        
        total_similarity = 0.0
        
        for pred, ref in zip(predictions, references):
            pred_lower = pred.lower()
            ref_lower = ref.lower()
            
            pred_keywords = [kw for kw in semantic_keywords if kw in pred_lower]
            ref_keywords = [kw for kw in semantic_keywords if kw in ref_lower]
            
            if not ref_keywords:
                similarity = 1.0 if not pred_keywords else 0.5
            else:
                overlap = len(set(pred_keywords) & set(ref_keywords))
                similarity = overlap / len(set(pred_keywords + ref_keywords))
            
            total_similarity += similarity
        
        return total_similarity / len(predictions) if predictions else 0.0
    
    def _get_ngrams(self, tokens: List[str], n: int) -> Dict[Tuple[str, ...], int]:
        """
        Extrahiert n-Grams aus Token-Liste mit Caching
        
        Args:
            tokens: Liste von Tokens
            n: n-gram Größe
        
        Returns:
            Dictionary mit n-grams und deren Häufigkeiten
        """
        
        cache_key = (tuple(tokens), n)
        if cache_key in self.n_gram_cache:
            return self.n_gram_cache[cache_key]
        
        ngrams = defaultdict(int)
        for i in range(len(tokens) - n + 1):
            ngram = tuple(tokens[i:i+n])
            ngrams[ngram] += 1
        
        self.n_gram_cache[cache_key] = dict(ngrams)
        return dict(ngrams)
    
    def evaluate_all(
        self,
        predictions: List[str],
        references: List[str],
        model: Optional[nn.Module] = None,
        input_ids: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None
    ) -> Dict[str, float]:
        """
        Evaluiert alle Text Quality Metriken
        
        Args:
            predictions: Liste von Vorhersagen
            references: Liste von Referenz-Texten
            model: Optional model für Perplexity
            input_ids: Optional input IDs für Perplexity
            labels: Optional labels für Perplexity
        
        Returns:
            Dictionary mit allen Text Quality Metriken
        """
        
        results = {}
        
        # BLEU Score
        try:
            results['bleu_score'] = self.compute_bleu_score(predictions, references)
        except Exception as e:
            logger.warning(f"BLEU computation failed: {e}")
            results['bleu_score'] = 0.0
        
        # ROUGE Scores
        try:
            rouge_scores = self.compute_rouge_scores(predictions, references)
            results.update(rouge_scores)
        except Exception as e:
            logger.warning(f"ROUGE computation failed: {e}")
            results.update({'rouge-1': 0.0, 'rouge-2': 0.0, 'rouge-L': 0.0})
        
        # Semantic Similarity
        try:
            results['semantic_similarity'] = self.compute_semantic_similarity(
                predictions, references
            )
        except Exception as e:
            logger.warning(f"Semantic similarity computation failed: {e}")
            results['semantic_similarity'] = 0.0
        
        # Perplexity (if model and data provided)
        if model is not None and input_ids is not None and labels is not None:
            try:
                results['perplexity'] = self.compute_perplexity(model, input_ids, labels)
            except Exception as e:
                logger.warning(f"Perplexity computation failed: {e}")
                results['perplexity'] = float('inf')
        else:
            results['perplexity'] = 0.0
        
        return results
