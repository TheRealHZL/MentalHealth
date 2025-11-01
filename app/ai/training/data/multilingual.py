"""
Multilingual Dataset Support

Unterstützt Training mit Deutsch, Englisch und Französisch
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Multilingual Sample Data
MULTILINGUAL_SAMPLES = {
    "sentiment": {
        "de": [
            {
                "text": "Ich fühle mich heute großartig! Das Leben ist wunderbar.",
                "label": 2,
            },
            {
                "text": "Mir geht es schlecht und ich fühle mich hoffnungslos.",
                "label": 0,
            },
            {"text": "Es ist ein normaler Tag, nichts Besonderes.", "label": 1},
            {"text": "Ich bin so glücklich und dankbar für alles!", "label": 2},
            {"text": "Ich fühle mich schrecklich und wertlos.", "label": 0},
        ],
        "en": [
            {"text": "I feel amazing today! Life is wonderful.", "label": 2},
            {"text": "I'm feeling down and hopeless.", "label": 0},
            {"text": "It's an okay day, nothing special.", "label": 1},
            {"text": "I'm so happy and grateful for everything!", "label": 2},
            {"text": "I feel terrible and worthless.", "label": 0},
        ],
        "fr": [
            {
                "text": "Je me sens incroyable aujourd'hui! La vie est merveilleuse.",
                "label": 2,
            },
            {"text": "Je me sens mal et désespéré.", "label": 0},
            {"text": "C'est une journée normale, rien de spécial.", "label": 1},
            {"text": "Je suis tellement heureux et reconnaissant!", "label": 2},
            {"text": "Je me sens terrible et sans valeur.", "label": 0},
        ],
    },
    "emotion": {
        "de": [
            {
                "text": "Ich bin so aufgeregt über diese Gelegenheit!",
                "emotion": 0,
            },  # joy
            {"text": "Ich fühle mich so traurig und einsam.", "emotion": 1},  # sadness
            {
                "text": "Ich bin wütend über das, was passiert ist!",
                "emotion": 2,
            },  # anger
            {"text": "Ich habe Angst und mache mir Sorgen.", "emotion": 3},  # fear
            {"text": "Wow, das habe ich nicht erwartet!", "emotion": 4},  # surprise
            {"text": "Das ist absolut ekelhaft.", "emotion": 5},  # disgust
            {"text": "Ich fühle mich neutral darüber.", "emotion": 6},  # neutral
        ],
        "en": [
            {"text": "I'm so excited about this opportunity!", "emotion": 0},
            {"text": "I feel so sad and lonely right now.", "emotion": 1},
            {"text": "I'm furious about what happened!", "emotion": 2},
            {"text": "I'm scared and worried about the future.", "emotion": 3},
            {"text": "Wow, I didn't expect that at all!", "emotion": 4},
            {"text": "That's absolutely disgusting.", "emotion": 5},
            {"text": "I'm feeling neutral about this.", "emotion": 6},
        ],
        "fr": [
            {
                "text": "Je suis tellement enthousiaste à propos de cette opportunité!",
                "emotion": 0,
            },
            {"text": "Je me sens si triste et seul en ce moment.", "emotion": 1},
            {"text": "Je suis furieux de ce qui s'est passé!", "emotion": 2},
            {"text": "J'ai peur et je m'inquiète pour l'avenir.", "emotion": 3},
            {"text": "Wow, je ne m'attendais pas du tout à ça!", "emotion": 4},
            {"text": "C'est absolument dégoûtant.", "emotion": 5},
            {"text": "Je me sens neutre à ce sujet.", "emotion": 6},
        ],
    },
    "chat": {
        "de": [
            {
                "context": "Benutzer fühlt sich ängstlich",
                "input": "Ich fühle mich wegen der Arbeit sehr gestresst.",
                "target": "Ich verstehe, dass Arbeitsstress überwältigend sein kann. Es ist wichtig, auf deine mentale Gesundheit zu achten. Überlege, mit deinem Vorgesetzten über die Arbeitsbelastung zu sprechen.",
                "emotion": 3,
                "mood": 4.0,
            },
            {
                "context": "Benutzer sucht Hilfe",
                "input": "Ich weiß nicht, wie ich mit meiner Angst umgehen soll.",
                "target": "Angst kann herausfordernd sein. Hilfreiche Strategien umfassen Atemübungen, Achtsamkeitsmeditation und das Gespräch mit einem Psychologen. Möchtest du einige Bewältigungstechniken erkunden?",
                "emotion": 3,
                "mood": 4.5,
            },
        ],
        "en": [
            {
                "context": "User is feeling anxious",
                "input": "I'm feeling really stressed about work.",
                "target": "I understand that work stress can be overwhelming. It's important to take care of your mental health. Consider talking to your supervisor about workload.",
                "emotion": 3,
                "mood": 4.0,
            },
            {
                "context": "User is seeking help",
                "input": "I don't know how to cope with my anxiety.",
                "target": "Anxiety can be challenging. Helpful strategies include breathing exercises, mindfulness meditation, and talking to a mental health professional. Would you like to explore some coping techniques?",
                "emotion": 3,
                "mood": 4.5,
            },
        ],
        "fr": [
            {
                "context": "L'utilisateur se sent anxieux",
                "input": "Je me sens vraiment stressé par le travail.",
                "target": "Je comprends que le stress au travail peut être accablant. Il est important de prendre soin de votre santé mentale. Envisagez de parler à votre superviseur de la charge de travail.",
                "emotion": 3,
                "mood": 4.0,
            },
            {
                "context": "L'utilisateur cherche de l'aide",
                "input": "Je ne sais pas comment gérer mon anxiété.",
                "target": "L'anxiété peut être difficile à gérer. Des stratégies utiles incluent les exercices de respiration, la méditation de pleine conscience et parler à un professionnel. Voulez-vous explorer des techniques d'adaptation?",
                "emotion": 3,
                "mood": 4.5,
            },
        ],
    },
}


def create_multilingual_data(
    output_dir: str = "data/training",
    languages: List[str] = ["de", "en", "fr"],
    dataset_types: List[str] = ["sentiment", "emotion", "chat"],
):
    """
    Erstellt multilinguales Training Data

    Args:
        output_dir: Output directory
        languages: Liste von Sprachen (de, en, fr)
        dataset_types: Liste von Dataset-Typen
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"🌍 Generating multilingual training data")
    logger.info(f"   - Languages: {', '.join(languages)}")
    logger.info(f"   - Dataset types: {', '.join(dataset_types)}")

    for dataset_type in dataset_types:
        if dataset_type not in MULTILINGUAL_SAMPLES:
            logger.warning(f"No samples for dataset type: {dataset_type}")
            continue

        # Combine all languages
        combined_train = []
        combined_val = []
        combined_test = []

        for lang in languages:
            if lang not in MULTILINGUAL_SAMPLES[dataset_type]:
                logger.warning(f"No samples for language {lang} in {dataset_type}")
                continue

            samples = MULTILINGUAL_SAMPLES[dataset_type][lang]

            # Add language tag to each sample
            tagged_samples = [{**sample, "language": lang} for sample in samples]

            # Split data: 70% train, 15% val, 15% test
            train_samples = tagged_samples * 100  # Multiply for more data
            val_samples = tagged_samples * 20
            test_samples = tagged_samples * 10

            combined_train.extend(train_samples)
            combined_val.extend(val_samples)
            combined_test.extend(test_samples)

        # Save combined multilingual data
        train_file = output_dir / f"{dataset_type}_multilingual_train.json"
        val_file = output_dir / f"{dataset_type}_multilingual_val.json"
        test_file = output_dir / f"{dataset_type}_multilingual_test.json"

        with open(train_file, "w", encoding="utf-8") as f:
            json.dump(combined_train, f, indent=2, ensure_ascii=False)

        with open(val_file, "w", encoding="utf-8") as f:
            json.dump(combined_val, f, indent=2, ensure_ascii=False)

        with open(test_file, "w", encoding="utf-8") as f:
            json.dump(combined_test, f, indent=2, ensure_ascii=False)

        logger.info(
            f"   ✓ {dataset_type}: {len(combined_train)} train, {len(combined_val)} val, {len(combined_test)} test"
        )

    logger.info("✅ Multilingual data generation complete!")


def get_language_token_mapping() -> Dict[str, int]:
    """
    Returns special tokens für Sprachen
    Kann im Tokenizer verwendet werden
    """
    return {
        "[DE]": 1,  # German
        "[EN]": 2,  # English
        "[FR]": 3,  # French
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    create_multilingual_data()
