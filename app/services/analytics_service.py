"""
Analytics Service - Self-Help Insights

Generiert personalisierte Insights für Selbsthilfe-Nutzer.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Union

from sqlalchemy import and_, asc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MoodEntry

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Analytics für Selbsthilfe-Nutzer"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_mood_trend(
        self, user_id: Union[str, uuid.UUID], days: int = 7
    ) -> Dict[str, Any]:
        """Calculate mood trend for self-help insights"""
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        start_date = datetime.now() - timedelta(days=days)

        result = await self.db.execute(
            select(MoodEntry.mood_score, MoodEntry.entry_date)
            .where(
                and_(MoodEntry.user_id == user_id, MoodEntry.created_at >= start_date)
            )
            .order_by(asc(MoodEntry.entry_date))
        )

        mood_data = result.all()

        if not mood_data:
            return {
                "trend": "no_data",
                "current_average": 5.0,
                "recommendation": "Beginne mit dem Tracking! 📊",
            }

        mood_scores = [entry.mood_score for entry in mood_data]
        current_average = sum(mood_scores) / len(mood_scores)

        # Trend calculation
        mid_point = len(mood_scores) // 2
        if mid_point > 0:
            first_half_avg = sum(mood_scores[:mid_point]) / mid_point
            second_half_avg = sum(mood_scores[mid_point:]) / (
                len(mood_scores) - mid_point
            )
            change = second_half_avg - first_half_avg
        else:
            change = 0

        # Classify trend
        if change > 0.5:
            trend = "improving"
            trend_emoji = "📈"
        elif change < -0.5:
            trend = "declining"
            trend_emoji = "📉"
        else:
            trend = "stable"
            trend_emoji = "➡️"

        return {
            "trend": trend,
            "trend_emoji": trend_emoji,
            "current_average": round(current_average, 1),
            "total_entries": len(mood_data),
            "recommendation": self._generate_mood_recommendation(
                current_average, trend
            ),
        }

    async def get_achievements(
        self, user_id: Union[str, uuid.UUID]
    ) -> List[Dict[str, Any]]:
        """Get user achievements for gamification"""
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        achievements = []

        # Count total entries
        result = await self.db.execute(
            select(MoodEntry.id).where(MoodEntry.user_id == user_id)
        )
        total_entries = len(result.all())

        # First entry achievement
        if total_entries >= 1:
            achievements.append(
                {
                    "id": "first_entry",
                    "title": "Erster Schritt! 🎯",
                    "description": "Deinen ersten Eintrag erstellt",
                    "unlocked": True,
                }
            )

        # Weekly warrior
        if total_entries >= 7:
            achievements.append(
                {
                    "id": "weekly_warrior",
                    "title": "Wochen-Krieger 💪",
                    "description": "7 Einträge erstellt",
                    "unlocked": True,
                }
            )

        # Monthly master
        if total_entries >= 30:
            achievements.append(
                {
                    "id": "monthly_master",
                    "title": "Monats-Meister 🏆",
                    "description": "30 Einträge erstellt",
                    "unlocked": True,
                }
            )

        return achievements

    async def get_self_help_insights(
        self, user_id: Union[str, uuid.UUID]
    ) -> Dict[str, Any]:
        """Generate personalized self-help insights"""
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        mood_trend = await self.get_mood_trend(user_id, 14)
        achievements = await self.get_achievements(user_id)

        return {
            "mood_trend": mood_trend,
            "achievements": achievements,
            "next_check_in": self._suggest_next_check_in(),
            "self_help_tips": self._get_self_help_tips(mood_trend),
            "crisis_support": self._get_crisis_support_info(),
        }

    def _generate_mood_recommendation(self, avg_mood: float, trend: str) -> str:
        """Generate mood-based recommendations"""
        if avg_mood < 3:
            return "🤗 Bei niedrigen Werten: Kleine Schritte sind okay. Nutze unseren KI-Chat!"
        elif avg_mood < 5:
            if trend == "improving":
                return "🌱 Du bist auf dem richtigen Weg! Bleibe dran."
            else:
                return "💪 Fokussiere dich auf Selbstfürsorge: Schlaf, Bewegung, Entspannung."
        elif avg_mood >= 7:
            return "🌟 Fantastische Stimmung! Nutze diese Energie für neue Ziele."
        else:
            return "✨ Stabile Stimmung - ein gutes Fundament für Wachstum."

    def _suggest_next_check_in(self) -> str:
        """Suggest next check-in time"""
        current_hour = datetime.now().hour

        if current_hour < 12:
            return "Perfekt für einen Morgen-Check-in! 🌅"
        elif current_hour < 18:
            return "Zeit für eine Mittags-Reflektion! ☀️"
        else:
            return "Ideal für eine Abend-Reflexion! 🌙"

    def _get_self_help_tips(self, mood_trend: Dict[str, Any]) -> List[str]:
        """Get personalized self-help tips"""
        current_mood = mood_trend.get("current_average", 5)
        trend = mood_trend.get("trend", "stable")

        tips = []

        if current_mood < 4:
            tips.extend(
                [
                    "🧘 Probiere eine 5-minütige Atemübung",
                    "🚶 Ein kurzer Spaziergang kann helfen",
                    "📱 Nutze unseren KI-Chat für Unterstützung",
                ]
            )

        if trend == "declining":
            tips.extend(
                [
                    "📝 Schreibe deine Gedanken auf",
                    "💪 Setze dir kleine, erreichbare Ziele",
                ]
            )
        elif trend == "improving":
            tips.extend(
                [
                    "🎉 Feiere deine Fortschritte!",
                    "📈 Bleibe bei deinen gesunden Gewohnheiten",
                ]
            )

        if not tips:
            tips = [
                "📊 Tracke deine Stimmung regelmäßig",
                "🌱 Entwickle eine Abendroutine",
                "🎯 Setze dir realistische Tagesziele",
            ]

        return tips[:3]

    def _get_crisis_support_info(self) -> Dict[str, Any]:
        """Get crisis support information"""
        return {
            "emergency_contacts": [
                {
                    "name": "Telefonseelsorge",
                    "phone": "0800 111 0 111",
                    "available": "24/7",
                },
                {
                    "name": "Nummer gegen Kummer",
                    "phone": "116 123",
                    "available": "24/7",
                },
            ],
            "immediate_help_tips": [
                "🧘 Atme tief: 4 Sekunden ein, 6 Sekunden aus",
                "🚶 Gehe 5 Minuten spazieren",
                "📱 Nutze unseren KI-Chat für sofortige Hilfe",
            ],
        }

    async def calculate_wellness_score(
        self, user_id: Union[str, uuid.UUID], start_date: datetime
    ) -> Dict[str, Any]:
        """Calculate overall wellness score"""
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        # Get mood entries for period
        result = await self.db.execute(
            select(MoodEntry)
            .where(
                and_(
                    MoodEntry.user_id == user_id,
                    MoodEntry.created_at >= start_date
                )
            )
            .order_by(asc(MoodEntry.entry_date))
        )
        entries = list(result.scalars().all())

        if not entries:
            return {
                "score": 50,
                "category": "neutral",
                "trend": "no_data",
                "message": "Nicht genug Daten verfügbar. Beginne mit dem Tracking!",
                "components": {
                    "mood": 50,
                    "sleep": 50,
                    "energy": 50,
                    "consistency": 0,
                }
            }

        # Calculate average scores
        avg_mood = sum(e.mood_score for e in entries) / len(entries) * 10
        avg_energy = sum(e.energy_level for e in entries) / len(entries) * 10

        # Sleep score
        sleep_entries = [e for e in entries if e.sleep_quality is not None]
        avg_sleep = (sum(e.sleep_quality for e in sleep_entries) / len(sleep_entries) * 10) if sleep_entries else 50

        # Consistency score (based on tracking frequency)
        days_range = (datetime.now() - start_date).days
        consistency = min(100, (len(entries) / days_range) * 100) if days_range > 0 else 0

        # Overall wellness score (weighted average)
        wellness_score = (
            avg_mood * 0.35 +
            avg_sleep * 0.25 +
            avg_energy * 0.25 +
            consistency * 0.15
        )

        # Determine category
        if wellness_score >= 75:
            category = "excellent"
        elif wellness_score >= 60:
            category = "good"
        elif wellness_score >= 40:
            category = "fair"
        else:
            category = "needs_attention"

        return {
            "score": round(wellness_score, 1),
            "category": category,
            "trend": "stable",
            "components": {
                "mood": round(avg_mood, 1),
                "sleep": round(avg_sleep, 1),
                "energy": round(avg_energy, 1),
                "consistency": round(consistency, 1),
            },
            "entries_count": len(entries),
            "period_days": days_range,
        }

    async def get_user_analytics_overview(
        self, user_id: Union[str, uuid.UUID]
    ) -> Dict[str, Any]:
        """Get comprehensive analytics overview"""
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        # Get data for last 30 days
        start_date = datetime.now() - timedelta(days=30)

        # Get mood trend
        mood_trend = await self.get_mood_trend(user_id, days=30)

        # Get wellness score
        wellness = await self.calculate_wellness_score(user_id, start_date)

        # Get achievements
        achievements = await self.get_achievements(user_id)

        return {
            "wellness_score": wellness,
            "mood_trend": mood_trend,
            "achievements": achievements,
            "insights_count": len(achievements),
            "last_updated": datetime.now().isoformat(),
        }
