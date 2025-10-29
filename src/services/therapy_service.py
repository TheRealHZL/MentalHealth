"""
Therapy Service - Strukturierte Therapie-Tools

Business Logic für therapeutische Arbeitsblätter und Selbsthilfe-Tools.
CBT-Techniken, Gedankenprotokolle, Therapievorbereitung etc.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc, asc
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import date, datetime, timedelta
import uuid
import logging
from collections import Counter

from src.models import TherapyNote, TherapyNoteType, TherapyTechnique
from src.schemas.ai import TherapyNoteCreate, TherapyNoteUpdate, PaginationParams

logger = logging.getLogger(__name__)

class TherapyService:
    """Therapy Tools & Structured Worksheets Service"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # =============================================================================
    # CRUD Operations
    # =============================================================================
    
    async def create_therapy_note(
        self,
        user_id: str,
        note_data: TherapyNoteCreate
    ) -> TherapyNote:
        """Create new therapy note/worksheet"""
        
        therapy_note = TherapyNote(
            user_id=uuid.UUID(user_id),
            note_date=note_data.note_date,
            note_type=note_data.note_type,
            title=note_data.title,
            content=note_data.content,
            session_number=note_data.session_number,
            therapist_name=note_data.therapist_name,
            session_duration=note_data.session_duration,
            techniques_used=[tech.value for tech in note_data.techniques_used],
            homework_assigned=note_data.homework_assigned,
            goals_discussed=note_data.goals_discussed,
            progress_made=note_data.progress_made,
            challenges_faced=note_data.challenges_faced,
            mood_before_session=note_data.mood_before_session.value if note_data.mood_before_session else None,
            mood_after_session=note_data.mood_after_session.value if note_data.mood_after_session else None,
            key_emotions=note_data.key_emotions,
            key_insights=note_data.key_insights,
            action_items=note_data.action_items,
            is_private=note_data.is_private,
            share_with_therapist=note_data.share_with_therapist,
            tags=note_data.tags
        )
        
        self.db.add(therapy_note)
        await self.db.commit()
        await self.db.refresh(therapy_note)
        
        logger.info(f"Created therapy note for user {user_id}: {note_data.note_type}")
        return therapy_note
    
    async def create_thought_record(
        self,
        user_id: str,
        situation: str,
        negative_thought: str,
        emotion: str,
        emotion_intensity: int,
        evidence_for: str,
        evidence_against: str,
        balanced_thought: str,
        new_emotion_intensity: int
    ) -> TherapyNote:
        """Create CBT thought record"""
        
        thought_record_content = f"""GEDANKENPROTOKOLL (CBT)
        
🎯 SITUATION:
{situation}

💭 AUTOMATISCHER GEDANKE:
{negative_thought}

😔 EMOTION & INTENSITÄT:
{emotion} - {emotion_intensity}/10

✅ BEWEISE DAFÜR:
{evidence_for}

❌ BEWEISE DAGEGEN:
{evidence_against}

🧠 AUSGEWOGENER GEDANKE:
{balanced_thought}

😊 NEUE EMOTION & INTENSITÄT:
{emotion} - {new_emotion_intensity}/10

📈 VERBESSERUNG: {emotion_intensity - new_emotion_intensity} Punkte"""
        
        thought_record = TherapyNote(
            user_id=uuid.UUID(user_id),
            note_date=date.today(),
            note_type=TherapyNoteType.SELF_REFLECTION,
            title=f"Gedankenprotokoll - {emotion}",
            content=thought_record_content,
            techniques_used=[TherapyTechnique.CBT.value],
            key_emotions=[emotion],
            mood_before_session=emotion_intensity,
            mood_after_session=new_emotion_intensity,
            tags=["gedankenprotokoll", "cbt", "selbsthilfe"]
        )
        
        self.db.add(thought_record)
        await self.db.commit()
        await self.db.refresh(thought_record)
        
        return thought_record
    
    async def create_therapy_preparation(
        self,
        user_id: str,
        session_goals: List[str],
        topics_to_discuss: List[str],
        current_challenges: List[str],
        homework_review: str,
        questions_for_therapist: List[str],
        current_mood: int,
        progress_since_last: str
    ) -> TherapyNote:
        """Create therapy session preparation worksheet"""
        
        prep_content = f"""THERAPIE-VORBEREITUNG
        
📅 Vorbereitung für nächste Sitzung

🎯 ZIELE FÜR DIESE SITZUNG:
{chr(10).join(f'• {goal}' for goal in session_goals)}

💬 THEMEN ZUM BESPRECHEN:
{chr(10).join(f'• {topic}' for topic in topics_to_discuss)}

⚠️ AKTUELLE HERAUSFORDERUNGEN:
{chr(10).join(f'• {challenge}' for challenge in current_challenges)}

📝 HAUSAUFGABEN REVIEW:
{homework_review}

❓ FRAGEN AN THERAPEUT:
{chr(10).join(f'• {question}' for question in questions_for_therapist)}

📊 AKTUELLE STIMMUNG: {current_mood}/10

📈 FORTSCHRITT SEIT LETZTER SITZUNG:
{progress_since_last}"""
        
        prep_note = TherapyNote(
            user_id=uuid.UUID(user_id),
            note_date=date.today(),
            note_type=TherapyNoteType.SESSION_NOTES,
            title="Therapie-Vorbereitung",
            content=prep_content,
            goals_discussed=session_goals,
            challenges_faced=current_challenges,
            mood_before_session=current_mood,
            progress_made=progress_since_last,
            tags=["vorbereitung", "therapie", "ziele"]
        )
        
        self.db.add(prep_note)
        await self.db.commit()
        await self.db.refresh(prep_note)
        
        return prep_note
    
    async def create_emotion_regulation_worksheet(
        self,
        user_id: str,
        trigger_situation: str,
        emotions_felt: List[str],
        emotion_intensities: Dict[str, int],
        physical_sensations: List[str],
        coping_strategies_used: List[str],
        effectiveness_rating: Dict[str, int],
        alternative_strategies: List[str]
    ) -> TherapyNote:
        """Create emotion regulation worksheet (DBT style)"""
        
        emotion_content = f"""EMOTIONSREGULATION ARBEITSBLATT
        
🎭 AUSLÖSENDE SITUATION:
{trigger_situation}

😭 GEFÜHLTE EMOTIONEN:
{chr(10).join(f'• {emotion}: {emotion_intensities.get(emotion, 0)}/10' for emotion in emotions_felt)}

🫀 KÖRPERLICHE EMPFINDUNGEN:
{chr(10).join(f'• {sensation}' for sensation in physical_sensations)}

🛠️ VERWENDETE BEWÄLTIGUNGSSTRATEGIEN:
{chr(10).join(f'• {strategy}: {effectiveness_rating.get(strategy, 0)}/10 Wirksamkeit' for strategy in coping_strategies_used)}

💡 ALTERNATIVE STRATEGIEN FÜR NÄCHSTES MAL:
{chr(10).join(f'• {strategy}' for strategy in alternative_strategies)}

📝 ERKENNTNISSE:
Was hat funktioniert? Was würde ich anders machen?"""
        
        emotion_note = TherapyNote(
            user_id=uuid.UUID(user_id),
            note_date=date.today(),
            note_type=TherapyNoteType.SELF_REFLECTION,
            title="Emotionsregulation",
            content=emotion_content,
            techniques_used=[TherapyTechnique.DBT.value],
            key_emotions=emotions_felt,
            mood_before_session=max(emotion_intensities.values()) if emotion_intensities else 5,
            tags=["emotionsregulation", "dbt", "bewältigung"]
        )
        
        self.db.add(emotion_note)
        await self.db.commit()
        await self.db.refresh(emotion_note)
        
        return emotion_note
    
    async def create_quick_reflection(
        self,
        user_id: str,
        reflection_text: str,
        current_mood: int
    ) -> TherapyNote:
        """Create quick self-reflection entry"""
        
        reflection_note = TherapyNote(
            user_id=uuid.UUID(user_id),
            note_date=date.today(),
            note_type=TherapyNoteType.SELF_REFLECTION,
            title=f"Reflexion - {date.today().strftime('%d.%m.%Y')}",
            content=reflection_text,
            mood_before_session=current_mood,
            tags=["reflexion", "selbsthilfe", "quick"]
        )
        
        self.db.add(reflection_note)
        await self.db.commit()
        await self.db.refresh(reflection_note)
        
        return reflection_note
    
    # =============================================================================
    # Structured Therapy Tools
    # =============================================================================
    
    def get_cbt_worksheet_template(self) -> Dict[str, Any]:
        """CBT Gedankenprotokoll Template"""
        return {
            "name": "CBT Gedankenprotokoll",
            "description": "Strukturiertes Arbeitsblatt zur Gedankenumstrukturierung",
            "fields": [
                {
                    "label": "Situation",
                    "type": "textarea",
                    "placeholder": "Beschreibe die Situation, in der der Gedanke auftrat",
                    "required": True
                },
                {
                    "label": "Automatischer Gedanke",
                    "type": "textarea", 
                    "placeholder": "Welcher Gedanke ging dir durch den Kopf?",
                    "required": True
                },
                {
                    "label": "Emotion",
                    "type": "select",
                    "options": ["Trauer", "Angst", "Wut", "Scham", "Schuld", "Frustration"],
                    "required": True
                },
                {
                    "label": "Intensität der Emotion",
                    "type": "scale",
                    "range": [1, 10],
                    "required": True
                },
                {
                    "label": "Beweise dafür",
                    "type": "textarea",
                    "placeholder": "Was spricht für diesen Gedanken?"
                },
                {
                    "label": "Beweise dagegen", 
                    "type": "textarea",
                    "placeholder": "Was spricht gegen diesen Gedanken?"
                },
                {
                    "label": "Ausgewogener Gedanke",
                    "type": "textarea",
                    "placeholder": "Formuliere einen realistischeren Gedanken",
                    "required": True
                },
                {
                    "label": "Neue Intensität",
                    "type": "scale", 
                    "range": [1, 10],
                    "required": True
                }
            ]
        }
    
    def get_therapy_prep_template(self) -> Dict[str, Any]:
        """Therapie-Vorbereitung Template"""
        return {
            "name": "Therapie-Vorbereitung",
            "description": "Strukturierte Vorbereitung für Therapiesitzungen",
            "fields": [
                {
                    "label": "Ziele für diese Sitzung",
                    "type": "list",
                    "placeholder": "Was möchtest du heute besprechen?",
                    "max_items": 5
                },
                {
                    "label": "Aktuelle Herausforderungen",
                    "type": "list", 
                    "placeholder": "Womit kämpfst du gerade?",
                    "max_items": 5
                },
                {
                    "label": "Hausaufgaben Review",
                    "type": "textarea",
                    "placeholder": "Wie sind die Aufgaben gelaufen?"
                },
                {
                    "label": "Fragen an Therapeut",
                    "type": "list",
                    "placeholder": "Was möchtest du fragen?",
                    "max_items": 10
                },
                {
                    "label": "Aktuelle Stimmung",
                    "type": "scale",
                    "range": [1, 10],
                    "required": True
                },
                {
                    "label": "Fortschritt seit letzter Sitzung",
                    "type": "textarea",
                    "placeholder": "Was hat sich verändert?"
                }
            ]
        }
    
    def get_emotion_regulation_template(self) -> Dict[str, Any]:
        """Emotionsregulation Template (DBT)"""
        return {
            "name": "Emotionsregulation",
            "description": "DBT-basiertes Arbeitsblatt für Emotionsmanagement",
            "fields": [
                {
                    "label": "Auslösende Situation",
                    "type": "textarea",
                    "placeholder": "Was ist passiert?",
                    "required": True
                },
                {
                    "label": "Emotionen",
                    "type": "emotion_intensity_grid",
                    "emotions": ["Wut", "Trauer", "Angst", "Freude", "Scham", "Schuld"],
                    "scale": [1, 10]
                },
                {
                    "label": "Körperliche Empfindungen",
                    "type": "checklist",
                    "options": [
                        "Herzrasen", "Schwitzen", "Zittern", "Anspannung", 
                        "Atemnot", "Schwindel", "Übelkeit", "Müdigkeit"
                    ]
                },
                {
                    "label": "Bewältigungsstrategien verwendet",
                    "type": "list",
                    "placeholder": "Was hast du versucht?",
                    "max_items": 5
                },
                {
                    "label": "Wirksamkeit der Strategien",
                    "type": "effectiveness_rating",
                    "scale": [1, 10]
                },
                {
                    "label": "Alternative Strategien",
                    "type": "list",
                    "placeholder": "Was könntest du nächstes Mal versuchen?",
                    "max_items": 5
                }
            ]
        }
    
    def get_mood_tracking_template(self) -> Dict[str, Any]:
        """Detailliertes Mood Tracking Template"""
        return {
            "name": "Detailliertes Stimmungstagebuch",
            "description": "Umfassendes Tracking für Stimmung und Einflussfaktoren",
            "fields": [
                {
                    "label": "Datum und Uhrzeit",
                    "type": "datetime",
                    "required": True
                },
                {
                    "label": "Stimmung",
                    "type": "scale",
                    "range": [1, 10],
                    "required": True
                },
                {
                    "label": "Energielevel", 
                    "type": "scale",
                    "range": [1, 10],
                    "required": True
                },
                {
                    "label": "Stresslevel",
                    "type": "scale", 
                    "range": [1, 10],
                    "required": True
                },
                {
                    "label": "Schlaf letzte Nacht",
                    "type": "sleep_quality",
                    "hours": [0, 12],
                    "quality": [1, 10]
                },
                {
                    "label": "Aktivitäten heute",
                    "type": "checklist",
                    "options": [
                        "Arbeit", "Sport", "Sozialer Kontakt", "Entspannung",
                        "Therapie", "Meditation", "Kreatives", "Hausarbeit"
                    ]
                },
                {
                    "label": "Auslöser/Trigger",
                    "type": "list",
                    "placeholder": "Was hat deine Stimmung beeinflusst?",
                    "max_items": 5
                },
                {
                    "label": "Dankbarkeit",
                    "type": "list",
                    "placeholder": "Wofür bist du heute dankbar?", 
                    "max_items": 3
                },
                {
                    "label": "Notizen",
                    "type": "textarea",
                    "placeholder": "Weitere Gedanken und Beobachtungen"
                }
            ]
        }
    
    def get_self_care_suggestions(self, mood_score: int) -> List[str]:
        """Get mood-based self-care suggestions"""
        
        if mood_score <= 3:
            return [
                "🛁 Warmes Bad oder Dusche nehmen",
                "☕ Einen beruhigenden Tee trinken",
                "🤗 Dir selbst Mitgefühl zeigen",
                "📱 Einen vertrauten Menschen anrufen",
                "🧘 5 Minuten Atemübungen"
            ]
        elif mood_score <= 6:
            return [
                "🚶 Kurzer Spaziergang an der frischen Luft",
                "📖 In einem guten Buch lesen",
                "🎵 Entspannende Musik hören",
                "📝 Gedanken aufschreiben",
                "🌱 Eine kleine Pflanze versorgen"
            ]
        else:
            return [
                "🎨 Kreative Aktivität starten",
                "💪 Sport oder Bewegung",
                "🤝 Zeit mit Freunden verbringen",
                "🎯 Neues Ziel setzen",
                "📚 Etwas Neues lernen"
            ]
    
    # =============================================================================
    # Analytics & Progress Tracking
    # =============================================================================
    
    async def analyze_therapy_progress(self, user_id: str, days: int) -> Dict[str, Any]:
        """Analyze therapy progress over time"""
        
        start_date = datetime.now() - timedelta(days=days)
        
        result = await self.db.execute(
            select(TherapyNote).where(
                and_(
                    TherapyNote.user_id == uuid.UUID(user_id),
                    TherapyNote.created_at >= start_date
                )
            ).order_by(TherapyNote.note_date)
        )
        
        notes = list(result.scalars().all())
        
        if not notes:
            return {"total_notes": 0, "message": "Keine Therapie-Notizen in diesem Zeitraum"}
        
        # Progress analysis
        mood_before = [n.mood_before_session for n in notes if n.mood_before_session]
        mood_after = [n.mood_after_session for n in notes if n.mood_after_session]
        
        techniques_used = []
        for note in notes:
            if note.techniques_used:
                techniques_used.extend(note.techniques_used)
        
        goals_discussed = []
        for note in notes:
            if note.goals_discussed:
                goals_discussed.extend(note.goals_discussed)
        
        return {
            "total_notes": len(notes),
            "note_types": dict(Counter(note.note_type.value for note in notes)),
            "avg_mood_before": round(sum(mood_before) / len(mood_before), 1) if mood_before else None,
            "avg_mood_after": round(sum(mood_after) / len(mood_after), 1) if mood_after else None,
            "mood_improvement": round(
                (sum(mood_after) / len(mood_after)) - (sum(mood_before) / len(mood_before)), 1
            ) if mood_before and mood_after else None,
            "most_used_techniques": dict(Counter(techniques_used).most_common(3)),
            "common_goals": dict(Counter(goals_discussed).most_common(5)),
            "consistency_score": self._calculate_consistency_score(notes, days)
        }
    
    def _calculate_consistency_score(self, notes: List[TherapyNote], days: int) -> int:
        """Calculate consistency score (0-100)"""
        
        # How regularly are notes being made?
        note_frequency = len(notes) / days
        
        # Score based on frequency (aim for 2-3 times per week)
        if note_frequency >= 0.4:  # ~3 times per week
            frequency_score = 100
        elif note_frequency >= 0.3:  # ~2 times per week
            frequency_score = 80
        elif note_frequency >= 0.14:  # ~1 time per week
            frequency_score = 60
        else:
            frequency_score = int(note_frequency * 400)  # Scale proportionally
        
        return min(100, frequency_score)
    
    # =============================================================================
    # Rest of CRUD and helper methods (similar to previous services)
    # =============================================================================
    
    async def get_therapy_note_by_id(self, note_id: str, user_id: str) -> Optional[TherapyNote]:
        """Get therapy note by ID"""
        result = await self.db.execute(
            select(TherapyNote).where(
                and_(
                    TherapyNote.id == uuid.UUID(note_id),
                    TherapyNote.user_id == uuid.UUID(user_id)
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def update_ai_analysis(self, note_id: uuid.UUID, ai_analysis: Dict[str, Any]) -> None:
        """Update AI analysis for therapy note"""
        result = await self.db.execute(
            select(TherapyNote).where(TherapyNote.id == note_id)
        )
        therapy_note = result.scalar_one_or_none()
        
        if therapy_note:
            therapy_note.ai_insights = ai_analysis.get("progress_insights")
            therapy_note.progress_analysis = ai_analysis.get("goal_assessment")
            await self.db.commit()
    
    def get_motivation_message(self, monthly_stats: Dict[str, Any]) -> str:
        """Get motivational message based on progress"""
        
        total_notes = monthly_stats.get("total_notes", 0)
        mood_improvement = monthly_stats.get("mood_improvement", 0)
        
        if total_notes == 0:
            return "Starte deine Selbstreflexions-Reise! Jeder Schritt zählt. 🌱"
        elif mood_improvement and mood_improvement > 1:
            return f"Fantastisch! Du hast deine Stimmung um {mood_improvement} Punkte verbessert! 🎉"
        elif total_notes >= 10:
            return "Du bleibst konsequent dran - das ist der Schlüssel zum Erfolg! 💪"
        else:
            return "Du machst wichtige Scschritte in deiner Entwicklung! Weiter so! ⭐"
