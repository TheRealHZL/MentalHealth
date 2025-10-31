"""
Sample Data Generator

Generiert Sample Training Data für Testing
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def create_sample_data(output_dir: str = "data/training"):
    """
    Erstellt Sample Training Data für alle Models

    Args:
        output_dir: Output directory
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"📝 Generating sample training data in {output_dir}")

    # 1. Sentiment Analysis Data
    _create_sentiment_data(output_dir)

    # 2. Emotion Classification Data
    _create_emotion_data(output_dir)

    # 3. Mood Prediction Data
    _create_mood_data(output_dir)

    # 4. Chat Generation Data
    _create_chat_data(output_dir)

    logger.info("✅ Sample data generation complete!")


def _create_sentiment_data(output_dir: Path):
    """Erstellt Sentiment Analysis Sample Data"""

    sentiment_samples = [
        # Positive samples
        {"text": "I feel amazing today! Life is wonderful.", "label": 2},
        {"text": "I'm so happy and grateful for everything!", "label": 2},
        {"text": "This is the best day ever!", "label": 2},
        {"text": "I'm feeling optimistic about the future.", "label": 2},
        {"text": "Everything is going great!", "label": 2},
        # Negative samples
        {"text": "I'm feeling down and hopeless.", "label": 0},
        {"text": "I feel terrible and worthless.", "label": 0},
        {"text": "Nothing is going right for me.", "label": 0},
        {"text": "I'm so sad and depressed.", "label": 0},
        {"text": "I feel awful about everything.", "label": 0},
        # Neutral samples
        {"text": "It's an okay day, nothing special.", "label": 1},
        {"text": "Just another regular day.", "label": 1},
        {"text": "I'm feeling neutral about this situation.", "label": 1},
        {"text": "Things are neither good nor bad.", "label": 1},
        {"text": "I don't have strong feelings either way.", "label": 1},
    ]

    # Multiply for more data
    train_data = sentiment_samples * 50  # 750 samples
    val_data = sentiment_samples * 10  # 150 samples
    test_data = sentiment_samples * 5  # 75 samples

    # Save files
    with open(output_dir / "sentiment_train.json", "w") as f:
        json.dump(train_data, f, indent=2)

    with open(output_dir / "sentiment_val.json", "w") as f:
        json.dump(val_data, f, indent=2)

    with open(output_dir / "sentiment_test.json", "w") as f:
        json.dump(test_data, f, indent=2)

    logger.info(
        f"   ✓ Sentiment data: {len(train_data)} train, {len(val_data)} val, {len(test_data)} test"
    )


def _create_emotion_data(output_dir: Path):
    """Erstellt Emotion Classification Sample Data"""

    emotion_samples = [
        {"text": "I'm so excited about this opportunity!", "emotion": 0},  # joy
        {"text": "I feel so sad and lonely right now.", "emotion": 1},  # sadness
        {"text": "I'm furious about what happened!", "emotion": 2},  # anger
        {"text": "I'm scared and worried about the future.", "emotion": 3},  # fear
        {"text": "Wow, I didn't expect that at all!", "emotion": 4},  # surprise
        {"text": "That's absolutely disgusting.", "emotion": 5},  # disgust
        {"text": "I'm feeling neutral about this.", "emotion": 6},  # neutral
    ]

    train_data = emotion_samples * 100
    val_data = emotion_samples * 20
    test_data = emotion_samples * 10

    with open(output_dir / "emotion_train.json", "w") as f:
        json.dump(train_data, f, indent=2)

    with open(output_dir / "emotion_val.json", "w") as f:
        json.dump(val_data, f, indent=2)

    with open(output_dir / "emotion_test.json", "w") as f:
        json.dump(test_data, f, indent=2)

    logger.info(
        f"   ✓ Emotion data: {len(train_data)} train, {len(val_data)} val, {len(test_data)} test"
    )


def _create_mood_data(output_dir: Path):
    """Erstellt Mood Prediction Sample Data"""

    mood_samples = [
        {
            "mood_sequence": [6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0],
            "metadata": {
                "sleep_hours": 8.0,
                "stress_level": 3.0,
                "exercise_minutes": 30.0,
                "social_interaction": 5.0,
            },
            "target_mood": 9.0,
        },
        {
            "mood_sequence": [5.0, 4.5, 4.0, 3.5, 3.0, 2.5, 2.0],
            "metadata": {
                "sleep_hours": 5.0,
                "stress_level": 8.0,
                "exercise_minutes": 0.0,
                "social_interaction": 1.0,
            },
            "target_mood": 2.0,
        },
        {
            "mood_sequence": [5.0, 5.5, 5.0, 5.5, 6.0, 5.5, 6.0],
            "metadata": {
                "sleep_hours": 7.0,
                "stress_level": 5.0,
                "exercise_minutes": 15.0,
                "social_interaction": 3.0,
            },
            "target_mood": 6.0,
        },
    ]

    train_data = mood_samples * 200
    val_data = mood_samples * 40
    test_data = mood_samples * 20

    with open(output_dir / "mood_train.json", "w") as f:
        json.dump(train_data, f, indent=2)

    with open(output_dir / "mood_val.json", "w") as f:
        json.dump(val_data, f, indent=2)

    with open(output_dir / "mood_test.json", "w") as f:
        json.dump(test_data, f, indent=2)

    logger.info(
        f"   ✓ Mood data: {len(train_data)} train, {len(val_data)} val, {len(test_data)} test"
    )


def _create_chat_data(output_dir: Path):
    """Erstellt Chat Generation Sample Data"""

    chat_samples = [
        {
            "context": "User is feeling anxious",
            "input": "I'm feeling really stressed about work.",
            "target": "I understand that work stress can be overwhelming. It's important to take care of your mental health. Consider talking to your supervisor about workload and taking regular breaks.",
            "emotion": 3,
            "mood": 4.0,
        },
        {
            "context": "User is seeking help",
            "input": "I don't know how to cope with my anxiety.",
            "target": "Anxiety can be challenging to manage. Some helpful strategies include deep breathing exercises, mindfulness meditation, and talking to a mental health professional. Would you like to explore some coping techniques together?",
            "emotion": 3,
            "mood": 4.5,
        },
        {
            "context": "User is feeling better",
            "input": "I've been feeling much better lately!",
            "target": "That's wonderful to hear! It's great that you're feeling better. What changes do you think have helped you the most?",
            "emotion": 0,
            "mood": 8.0,
        },
    ]

    train_data = chat_samples * 150
    val_data = chat_samples * 30
    test_data = chat_samples * 15

    with open(output_dir / "chat_train.json", "w") as f:
        json.dump(train_data, f, indent=2)

    with open(output_dir / "chat_val.json", "w") as f:
        json.dump(val_data, f, indent=2)

    with open(output_dir / "chat_test.json", "w") as f:
        json.dump(test_data, f, indent=2)

    logger.info(
        f"   ✓ Chat data: {len(train_data)} train, {len(val_data)} val, {len(test_data)} test"
    )


if __name__ == "__main__":
    # Allow running directly
    logging.basicConfig(level=logging.INFO)
    create_sample_data()
