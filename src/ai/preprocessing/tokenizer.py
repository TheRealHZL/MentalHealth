"""
Custom Tokenizer for MindBridge

Eigener Tokenizer speziell für Mental Health Domain.
Versteht deutsche Sprache und psychologische Begriffe.
"""

import json
import pickle
import logging
from typing import List, Dict, Set, Optional, Tuple
from pathlib import Path
from collections import Counter, defaultdict
import re
import unicodedata

logger = logging.getLogger(__name__)

class MindBridgeTokenizer:
    """
    Custom Tokenizer für Mental Health Text Processing
    
    Features:
    - Deutsche Sprache optimiert
    - Mental Health Vokabular
    - Subword Tokenization (BPE-ähnlich)
    - Emoticons und Emojis
    - Spezielle Tokens für Kontext
    """
    
    def __init__(self, vocab_size: int = 30000):
        self.vocab_size = vocab_size
        
        # Special tokens
        self.special_tokens = {
            '<pad>': 0,
            '<unk>': 1,
            '<bos>': 2,  # Beginning of sequence
            '<eos>': 3,  # End of sequence
            '<mood>': 4,  # Mood indicator
            '<stress>': 5,  # Stress level
            '<emotion>': 6,  # Emotion marker
            '<user>': 7,  # User message
            '<assistant>': 8,  # Assistant response
            '<context>': 9,  # Context information
        }
        
        # Vocabulary mappings
        self.token_to_id: Dict[str, int] = self.special_tokens.copy()
        self.id_to_token: Dict[int, str] = {v: k for k, v in self.special_tokens.items()}
        
        # BPE merges for subword tokenization
        self.bpe_merges: List[Tuple[str, str]] = []
        self.bpe_cache: Dict[str, List[str]] = {}
        
        # Mental health vocabulary
        self.mental_health_vocab = self._get_mental_health_vocab()
        
        # German language patterns
        self.german_patterns = self._get_german_patterns()
        
        # Emotion patterns
        self.emotion_patterns = self._get_emotion_patterns()
        
        logger.info(f"🔤 MindBridge Tokenizer initialized with vocab_size={vocab_size}")
    
    def _get_mental_health_vocab(self) -> Set[str]:
        """Mental Health spezifisches Vokabular"""
        return {
            # Emotionen
            'angst', 'freude', 'trauer', 'wut', 'überraschung', 'ekel', 'furcht',
            'ängstlich', 'fröhlich', 'traurig', 'wütend', 'überrascht', 'angeekelt',
            'glücklich', 'deprimiert', 'hoffnungslos', 'optimistisch', 'pessimistisch',
            
            # Stimmungen
            'stimmung', 'laune', 'gefühl', 'emotion', 'empfindung', 'zustand',
            'niedergeschlagen', 'aufgewühlt', 'ausgeglichen', 'unruhig', 'entspannt',
            
            # Stress und Belastung
            'stress', 'belastung', 'druck', 'anspannung', 'überforderung',
            'burnout', 'erschöpfung', 'müdigkeit', 'schlaflos', 'unkonzentriert',
            
            # Therapie und Behandlung
            'therapie', 'behandlung', 'beratung', 'psychologe', 'psychiater',
            'therapeut', 'medikament', 'antidepressiva', 'gespräch', 'sitzung',
            
            # Bewältigungsstrategien
            'bewältigung', 'entspannung', 'meditation', 'achtsamkeit', 'atmung',
            'sport', 'bewegung', 'schlaf', 'ernährung', 'sozial', 'unterstützung',
            
            # Problembereiche
            'depression', 'angststörung', 'panik', 'zwang', 'trauma', 'sucht',
            'essstörung', 'schlafstörung', 'beziehung', 'arbeit', 'familie',
            
            # Positive Ressourcen
            'kraft', 'mut', 'hoffnung', 'vertrauen', 'selbstwert', 'resilientz',
            'bewusstsein', 'klarheit', 'ruhe', 'gelassenheit', 'stabilität'
        }
    
    def _get_german_patterns(self) -> List[str]:
        """Deutsche Sprachmuster"""
        return [
            # Umlaute
            'ä', 'ö', 'ü', 'ß',
            
            # Häufige deutsche Endungen
            'ung', 'keit', 'heit', 'schaft', 'lich', 'isch', 'bar',
            
            # Präfixe
            'un', 'ver', 'be', 'ge', 'er', 'zer', 'ent', 'emp',
            
            # Häufige Wörter
            'ich', 'du', 'er', 'sie', 'es', 'wir', 'ihr', 'sie',
            'der', 'die', 'das', 'den', 'dem', 'des',
            'und', 'oder', 'aber', 'wenn', 'dass', 'weil',
            'nicht', 'kein', 'keine', 'nichts', 'niemand'
        ]
    
    def _get_emotion_patterns(self) -> Dict[str, List[str]]:
        """Emoticon und Emoji Patterns"""
        return {
            'positive': [
                ':-)', ':)', '=)', ':D', ':-D', '=D', ':P', ':-P',
                '😊', '😄', '😃', '😁', '🙂', '😍', '🥰', '😘'
            ],
            'negative': [
                ':-(', ':(', '=(', ':/', ':-/', ':|', ':-|',
                '😢', '😭', '😞', '😔', '😟', '😕', '🙁', '😩'
            ],
            'neutral': [
                ':-|', ':|', '😐', '😑', '🤔', '🤷', '😶'
            ]
        }
    
    def normalize_text(self, text: str) -> str:
        """
        Normalisiert Text für Tokenization
        
        Args:
            text: Raw text input
        
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        # Unicode normalization
        text = unicodedata.normalize('NFC', text)
        
        # Lowercase
        text = text.lower()
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Preserve emoticons and emojis
        text = self._preserve_emoticons(text)
        
        # Handle special mental health markers
        text = self._handle_special_markers(text)
        
        return text.strip()
    
    def _preserve_emoticons(self, text: str) -> str:
        """Preserves emoticons and emojis during normalization"""
        
        # Replace common emoticons with special tokens
        emoticon_map = {
            ':-)': ' <EMOTICON_HAPPY> ',
            ':)': ' <EMOTICON_HAPPY> ',
            ':-(': ' <EMOTICON_SAD> ',
            ':(': ' <EMOTICON_SAD> ',
            ':D': ' <EMOTICON_VERY_HAPPY> ',
            ':/': ' <EMOTICON_CONFUSED> ',
            ':|': ' <EMOTICON_NEUTRAL> '
        }
        
        for emoticon, replacement in emoticon_map.items():
            text = text.replace(emoticon, replacement)
        
        return text
    
    def _handle_special_markers(self, text: str) -> str:
        """Handles special mental health markers in text"""
        
        # Mood scale patterns (1-10, 1/10, etc.)
        text = re.sub(r'\b(\d+)(/10|/10)\b', r'<MOOD_SCALE_\1>', text)
        text = re.sub(r'\b(\d+)\s*von\s*10\b', r'<MOOD_SCALE_\1>', text)
        
        # Stress level patterns
        text = re.sub(r'stress\s*level?\s*(\d+)', r'<STRESS_LEVEL_\1>', text)
        text = re.sub(r'stress\s*(\d+)/10', r'<STRESS_LEVEL_\1>', text)
        
        return text
    
    def _get_word_pieces(self, word: str) -> List[str]:
        """
        Breaks word into subword pieces using BPE-like algorithm
        
        Args:
            word: Input word
        
        Returns:
            List of subword pieces
        """
        if word in self.bpe_cache:
            return self.bpe_cache[word]
        
        # Start with character-level tokenization
        word_pieces = list(word)
        
        # Apply BPE merges
        for merge_a, merge_b in self.bpe_merges:
            new_pieces = []
            i = 0
            
            while i < len(word_pieces):
                if (i < len(word_pieces) - 1 and 
                    word_pieces[i] == merge_a and 
                    word_pieces[i + 1] == merge_b):
                    new_pieces.append(merge_a + merge_b)
                    i += 2
                else:
                    new_pieces.append(word_pieces[i])
                    i += 1
            
            word_pieces = new_pieces
        
        # Cache result
        self.bpe_cache[word] = word_pieces
        return word_pieces
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenizes text into tokens
        
        Args:
            text: Input text
        
        Returns:
            List of tokens
        """
        # Normalize text
        text = self.normalize_text(text)
        
        if not text:
            return []
        
        tokens = []
        
        # Split on whitespace and punctuation
        words = re.findall(r'\S+', text)
        
        for word in words:
            # Check for special tokens
            if word in self.token_to_id:
                tokens.append(word)
                continue
            
            # Check for mental health vocabulary
            if word in self.mental_health_vocab:
                tokens.append(word)
                continue
            
            # Handle punctuation
            if re.match(r'^[^\w\s]+$', word):
                tokens.append(word)
                continue
            
            # Apply subword tokenization
            subwords = self._get_word_pieces(word)
            tokens.extend(subwords)
        
        return tokens
    
    def encode(self, text: str) -> List[int]:
        """
        Encodes text to token IDs
        
        Args:
            text: Input text
        
        Returns:
            List of token IDs
        """
        tokens = self.tokenize(text)
        
        token_ids = []
        for token in tokens:
            if token in self.token_to_id:
                token_ids.append(self.token_to_id[token])
            else:
                # Unknown token
                token_ids.append(self.token_to_id['<unk>'])
        
        return token_ids
    
    def decode(self, token_ids: List[int]) -> str:
        """
        Decodes token IDs back to text
        
        Args:
            token_ids: List of token IDs
        
        Returns:
            Decoded text
        """
        tokens = []
        
        for token_id in token_ids:
            if token_id in self.id_to_token:
                token = self.id_to_token[token_id]
                
                # Skip special tokens in output
                if token not in ['<pad>', '<bos>', '<eos>']:
                    tokens.append(token)
        
        # Join tokens and clean up
        text = ' '.join(tokens)
        
        # Post-process
        text = self._post_process_decoded_text(text)
        
        return text
    
    def _post_process_decoded_text(self, text: str) -> str:
        """Post-processes decoded text"""
        
        # Restore emoticons
        emoticon_restore = {
            '<EMOTICON_HAPPY>': '🙂',
            '<EMOTICON_SAD>': '😢',
            '<EMOTICON_VERY_HAPPY>': '😄',
            '<EMOTICON_CONFUSED>': '😕',
            '<EMOTICON_NEUTRAL>': '😐'
        }
        
        for token, emoticon in emoticon_restore.items():
            text = text.replace(token, emoticon)
        
        # Clean up spacing
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        
        return text.strip()
    
    def encode_batch(self, texts: List[str], max_length: int = None) -> List[List[int]]:
        """
        Encodes multiple texts with optional padding
        
        Args:
            texts: List of input texts
            max_length: Maximum sequence length (padding/truncation)
        
        Returns:
            List of encoded sequences
        """
        encoded_batch = []
        
        for text in texts:
            encoded = self.encode(text)
            
            if max_length:
                if len(encoded) > max_length:
                    # Truncate
                    encoded = encoded[:max_length-1] + [self.token_to_id['<eos>']]
                else:
                    # Pad
                    encoded = encoded + [self.token_to_id['<pad>']] * (max_length - len(encoded))
            
            encoded_batch.append(encoded)
        
        return encoded_batch
    
    async def train_from_samples(self, sample_texts: Optional[List[str]] = None):
        """
        Trains tokenizer on sample data
        
        Args:
            sample_texts: Training texts (uses default if None)
        """
        if sample_texts is None:
            sample_texts = self._get_default_training_data()
        
        logger.info(f"🏃 Training tokenizer on {len(sample_texts)} samples...")
        
        # Build vocabulary
        word_freq = Counter()
        
        for text in sample_texts:
            normalized_text = self.normalize_text(text)
            words = re.findall(r'\S+', normalized_text)
            word_freq.update(words)
        
        # Add high-frequency words to vocabulary
        next_id = len(self.special_tokens)
        
        # Add mental health vocabulary first (higher priority)
        for word in self.mental_health_vocab:
            if word not in self.token_to_id:
                self.token_to_id[word] = next_id
                self.id_to_token[next_id] = word
                next_id += 1
        
        # Add most frequent words
        for word, freq in word_freq.most_common():
            if next_id >= self.vocab_size:
                break
            
            if word not in self.token_to_id:
                self.token_to_id[word] = next_id
                self.id_to_token[next_id] = word
                next_id += 1
        
        # Train BPE merges
        await self._train_bpe_merges(sample_texts)
        
        logger.info(f"✅ Tokenizer training completed. Vocabulary size: {len(self.token_to_id)}")
    
    async def _train_bpe_merges(self, texts: List[str], num_merges: int = 1000):
        """Trains BPE merges for subword tokenization"""
        
        # Count character pairs
        pair_counts = defaultdict(int)
        
        for text in texts:
            words = re.findall(r'\S+', self.normalize_text(text))
            
            for word in words:
                chars = list(word)
                for i in range(len(chars) - 1):
                    pair = (chars[i], chars[i + 1])
                    pair_counts[pair] += 1
        
        # Learn merges
        for _ in range(min(num_merges, len(pair_counts))):
            if not pair_counts:
                break
            
            # Find most frequent pair
            best_pair = max(pair_counts, key=pair_counts.get)
            
            if pair_counts[best_pair] < 2:  # Minimum frequency threshold
                break
            
            # Add merge
            self.bpe_merges.append(best_pair)
            
            # Update pair counts
            new_pair_counts = defaultdict(int)
            
            for (a, b), count in pair_counts.items():
                if (a, b) == best_pair:
                    continue
                
                # Update counts for new merges
                new_pair_counts[(a, b)] += count
            
            pair_counts = new_pair_counts
        
        logger.info(f"✅ Learned {len(self.bpe_merges)} BPE merges")
    
    def _get_default_training_data(self) -> List[str]:
        """Default training data for German mental health domain"""
        return [
            "Ich fühle mich heute sehr traurig und niedergeschlagen.",
            "Meine Stimmung ist schlecht, etwa 3 von 10.",
            "Stress level 8/10, ich bin total überfordert.",
            "Die Therapie hilft mir sehr beim Umgang mit Angst.",
            "Ich bin glücklich und voller Hoffnung :)",
            "Depression macht mich müde und antriebslos.",
            "Entspannung und Meditation helfen mir sehr.",
            "Mein Psychologe gibt mir gute Bewältigungsstrategien.",
            "Ich habe Panikattacken und Angststörungen.",
            "Sport und Bewegung verbessern meine Laune.",
            "Schlaflosigkeit belastet mich sehr.",
            "Meine Familie unterstützt mich bei der Behandlung.",
            "Achtsamkeit und Atmung beruhigen mich.",
            "Ich fühle mich isoliert und allein :(",
            "Hoffnung und Mut geben mir Kraft weiter zu machen.",
            "Burnout und Erschöpfung beherrschen meinen Alltag.",
            "Selbstwert und Vertrauen muss ich wieder aufbauen.",
            "Die Beratung zeigt mir neue Perspektiven auf.",
            "Zwangsgedanken und Trauma belasten mich täglich.",
            "Resilientz und Stabilität entwickle ich Schritt für Schritt."
        ]
    
    def get_vocab_info(self) -> Dict[str, any]:
        """Returns vocabulary information"""
        return {
            'vocab_size': len(self.token_to_id),
            'special_tokens': len(self.special_tokens),
            'mental_health_terms': len(self.mental_health_vocab & set(self.token_to_id.keys())),
            'bpe_merges': len(self.bpe_merges),
            'cache_size': len(self.bpe_cache)
        }
    
    def save(self, path: Path):
        """
        Saves tokenizer to disk
        
        Args:
            path: Directory path to save tokenizer
        """
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        
        # Save vocabulary
        vocab_file = path / 'vocab.json'
        with open(vocab_file, 'w', encoding='utf-8') as f:
            json.dump({
                'token_to_id': self.token_to_id,
                'id_to_token': {str(k): v for k, v in self.id_to_token.items()},
                'vocab_size': self.vocab_size
            }, f, ensure_ascii=False, indent=2)
        
        # Save BPE merges
        merges_file = path / 'merges.json'
        with open(merges_file, 'w', encoding='utf-8') as f:
            json.dump(self.bpe_merges, f, ensure_ascii=False, indent=2)
        
        # Save cache
        cache_file = path / 'bpe_cache.pkl'
        with open(cache_file, 'wb') as f:
            pickle.dump(self.bpe_cache, f)
        
        logger.info(f"✅ Tokenizer saved to {path}")
    
    @classmethod
    def load(cls, path: Path) -> 'MindBridgeTokenizer':
        """
        Loads tokenizer from disk
        
        Args:
            path: Directory path containing tokenizer files
        
        Returns:
            Loaded tokenizer instance
        """
        path = Path(path)
        
        # Load vocabulary
        vocab_file = path / 'vocab.json'
        with open(vocab_file, 'r', encoding='utf-8') as f:
            vocab_data = json.load(f)
        
        # Create tokenizer instance
        tokenizer = cls(vocab_data['vocab_size'])
        tokenizer.token_to_id = vocab_data['token_to_id']
        tokenizer.id_to_token = {int(k): v for k, v in vocab_data['id_to_token'].items()}
        
        # Load BPE merges
        merges_file = path / 'merges.json'
        if merges_file.exists():
            with open(merges_file, 'r', encoding='utf-8') as f:
                tokenizer.bpe_merges = [tuple(merge) for merge in json.load(f)]
        
        # Load cache
        cache_file = path / 'bpe_cache.pkl'
        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                tokenizer.bpe_cache = pickle.load(f)
        
        logger.info(f"✅ Tokenizer loaded from {path}")
        return tokenizer
