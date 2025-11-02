"""
Mood Analytics Service - Self-Help Insights

Analytics und Insights für Stimmungsdaten ohne Therapeut-Abhängigkeit.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MoodEntry

logger = logging.getLogger(__name__)


class MoodAnalyticsService:
    """Mood Analytics für Selbsthilfe-Nutzer"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_mood_entry(self, mood_entry: MoodEntry) -> Dict[str, Any]:
        """Analyze single mood entry"""

        analysis = {
            "mood_category": self._categorize_mood(mood_entry.mood_score),
            "stress_assessment": self._assess_stress(mood_entry.stress_level),
            "energy_assessment": self._assess_energy(mood_entry.energy_level),
            "sleep_impact": self._analyze_sleep_impact(
                mood_entry.sleep_quality, mood_entry.sleep_hours
            ),
            "activity_benefits": self._analyze_activities(
                mood_entry.activities, mood_entry.exercise_minutes
            ),
            "risk_flags": self._check_risk_indicators(mood_entry),
            "positive_signals": self._identify_positive_signals(mood_entry),
            "recommendations": self._generate_recommendations(mood_entry),
        }

        return analysis

    async def get_mood_correlations(
        self, user_id: str, days: int = 30
    ) -> Dict[str, Any]:
        """Analyze correlations between mood and other factors"""

        start_date = datetime.now() - timedelta(days=days)

        result = await self.db.execute(
            select(MoodEntry).where(
                and_(
                    MoodEntry.user_id == uuid.UUID(user_id),
                    MoodEntry.created_at >= start_date,
                )
            )
        )

        entries = list(result.scalars().all())

        if len(entries) < 5:
            return {"message": "Mehr Daten benötigt für Korrelationsanalyse"}

        # Calculate correlations
        mood_sleep_corr = self._calculate_correlation(
            [e.mood_score for e in entries], [e.sleep_hours for e in entries]
        )

        mood_exercise_corr = self._calculate_correlation(
            [e.mood_score for e in entries], [e.exercise_minutes for e in entries]
        )

        mood_stress_corr = self._calculate_correlation(
            [e.mood_score for e in entries],
            [-e.stress_level for e in entries],  # Negative correlation expected
        )

        return {
            "sleep_correlation": {
                "score": mood_sleep_corr,
                "interpretation": self._interpret_correlation(mood_sleep_corr, "sleep"),
            },
            "exercise_correlation": {
                "score": mood_exercise_corr,
                "interpretation": self._interpret_correlation(
                    mood_exercise_corr, "exercise"
                ),
            },
            "stress_correlation": {
                "score": mood_stress_corr,
                "interpretation": self._interpret_correlation(
                    mood_stress_corr, "stress"
                ),
            },
            "insights": self._generate_correlation_insights(
                mood_sleep_corr, mood_exercise_corr, mood_stress_corr
            ),
        }

    async def find_mood_patterns(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Find patterns in mood data"""

        start_date = datetime.now() - timedelta(days=days)

        result = await self.db.execute(
            select(MoodEntry)
            .where(
                and_(
                    MoodEntry.user_id == uuid.UUID(user_id),
                    MoodEntry.created_at >= start_date,
                )
            )
            .order_by(MoodEntry.entry_date)
        )

        entries = list(result.scalars().all())

        if len(entries) < 7:
            return {"message": "Mehr Daten für Muster-Erkennung benötigt"}

        patterns = {
            "weekly_patterns": self._analyze_weekly_patterns(entries),
            "time_patterns": self._analyze_time_patterns(entries),
            "activity_patterns": self._analyze_activity_patterns(entries),
            "trigger_patterns": self._analyze_trigger_patterns(entries),
            "improvement_patterns": self._find_improvement_patterns(entries),
        }

        return patterns

    async def generate_mood_insights(self, user_id: str) -> List[str]:
        """Generate personalized mood insights"""

        insights = []

        # Recent trend analysis
        recent_entries = await self._get_recent_entries(user_id, 7)

        if len(recent_entries) >= 3:
            avg_mood = sum(e.mood_score for e in recent_entries) / len(recent_entries)

            if avg_mood >= 7:
                insights.append("🌟 Deine Stimmung ist in letzter Zeit sehr positiv!")
            elif avg_mood <= 4:
                insights.append(
                    "💙 Du durchlebst eine schwierige Phase. Das ist normal und geht vorbei."
                )

            # Check consistency
            mood_variance = self._calculate_variance(
                [e.mood_score for e in recent_entries]
            )
            if mood_variance < 1.5:
                insights.append(
                    "🎯 Deine Stimmung ist sehr stabil - das zeigt emotionale Balance."
                )

        # Sleep insights
        sleep_entries = [e for e in recent_entries if e.sleep_hours > 0]
        if sleep_entries:
            avg_sleep = sum(e.sleep_hours for e in sleep_entries) / len(sleep_entries)
            if avg_sleep < 6:
                insights.append(
                    "😴 Mehr Schlaf könnte deine Stimmung deutlich verbessern."
                )
            elif avg_sleep > 9:
                insights.append(
                    "💤 Du schläfst viel - achte auf die Schlafqualität, nicht nur die Dauer."
                )

        # Exercise insights
        exercise_entries = [e for e in recent_entries if e.exercise_minutes > 0]
        if len(exercise_entries) >= len(recent_entries) * 0.7:
            insights.append("💪 Regelmäßige Bewegung scheint dir gut zu tun!")
        elif len(exercise_entries) == 0:
            insights.append(
                "🚶 Schon 10 Minuten Bewegung täglich können deine Stimmung heben."
            )

        return insights[:3]  # Max 3 insights

    def get_mood_recommendations(self, mood_trend: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on mood trend"""

        current_mood = mood_trend.get("current_average", 5)
        trend = mood_trend.get("trend", "stable")

        recommendations = []

        # Mood-based recommendations
        if current_mood <= 3:
            recommendations.extend(
                [
                    "🤗 Kontaktiere Freunde oder Familie für Unterstützung",
                    "🧘 Probiere Entspannungsübungen oder Meditation",
                    "📱 Nutze unseren KI-Chat für sofortige Hilfe",
                ]
            )
        elif current_mood <= 5:
            recommendations.extend(
                [
                    "🌱 Konzentriere dich auf kleine, positive Veränderungen",
                    "📝 Führe ein Dankbarkeitstagebuch",
                    "🎯 Setze dir kleine, erreichbare Tagesziele",
                ]
            )
        elif current_mood >= 7:
            recommendations.extend(
                [
                    "🚀 Nutze diese positive Energie für neue Projekte",
                    "🤝 Hilf anderen - das verstärkt positive Gefühle",
                    "📈 Reflektiere, was gut läuft, um es beizubehalten",
                ]
            )

        # Trend-based recommendations
        if trend == "declining":
            recommendations.extend(
                [
                    "⚠️ Achte besonders auf Selbstfürsorge",
                    "🔄 Überprüfe deine Routinen und Gewohnheiten",
                ]
            )
        elif trend == "improving":
            recommendations.extend(
                [
                    "🎉 Bleibe bei dem, was funktioniert!",
                    "📊 Dokumentiere, was zur Verbesserung beiträgt",
                ]
            )

        return recommendations[:4]  # Max 4 recommendations

    # =============================================================================
    # Helper Methods
    # =============================================================================

    def _categorize_mood(self, mood_score: int) -> str:
        """Categorize mood score"""
        if mood_score <= 3:
            return "low"
        elif mood_score <= 6:
            return "moderate"
        else:
            return "high"

    def _assess_stress(self, stress_level: int) -> Dict[str, Any]:
        """Assess stress level"""
        if stress_level <= 3:
            category = "low"
            message = "Niedriger Stress - gute Balance! 😌"
        elif stress_level <= 6:
            category = "moderate"
            message = "Moderater Stress - achte auf Entspannung. 🧘"
        else:
            category = "high"
            message = "Hoher Stress - Zeit für Stressabbau! 🚨"

        return {"category": category, "message": message}

    def _assess_energy(self, energy_level: int) -> Dict[str, Any]:
        """Assess energy level"""
        if energy_level <= 3:
            return {
                "category": "low",
                "message": "Niedrige Energie - mehr Erholung nötig. 🔋",
            }
        elif energy_level <= 6:
            return {
                "category": "moderate",
                "message": "Moderate Energie - ausgewogen. ⚡",
            }
        else:
            return {"category": "high", "message": "Hohe Energie - nutze sie! 🚀"}

    def _analyze_sleep_impact(
        self, sleep_quality: int, sleep_hours: float
    ) -> Dict[str, Any]:
        """Analyze sleep impact on mood"""

        quality_assessment = (
            "gut"
            if sleep_quality >= 7
            else "schlecht" if sleep_quality <= 4 else "okay"
        )
        duration_assessment = (
            "zu wenig"
            if sleep_hours < 6
            else "zu viel" if sleep_hours > 9 else "angemessen"
        )

        return {
            "quality": quality_assessment,
            "duration": duration_assessment,
            "recommendation": self._get_sleep_recommendation(
                sleep_quality, sleep_hours
            ),
        }

    def _analyze_activities(
        self, activities: List[str], exercise_minutes: int
    ) -> Dict[str, Any]:
        """Analyze activity impact"""

        activity_count = len(activities) if activities else 0
        has_exercise = exercise_minutes > 0

        return {
            "activity_variety": "hoch" if activity_count >= 3 else "niedrig",
            "includes_exercise": has_exercise,
            "exercise_duration": exercise_minutes,
            "recommendation": self._get_activity_recommendation(
                activity_count, exercise_minutes
            ),
        }

    def _check_risk_indicators(self, mood_entry: MoodEntry) -> List[str]:
        """Check for risk indicators"""

        risks = []

        if mood_entry.mood_score <= 2:
            risks.append("Sehr niedrige Stimmung")

        if mood_entry.stress_level >= 8:
            risks.append("Sehr hoher Stress")

        if mood_entry.sleep_hours < 4:
            risks.append("Kritischer Schlafmangel")

        if mood_entry.symptoms and any(
            "suizid" in symptom.lower() for symptom in mood_entry.symptoms
        ):
            risks.append("Notfall - professionelle Hilfe erforderlich")

        return risks

    def _identify_positive_signals(self, mood_entry: MoodEntry) -> List[str]:
        """Identify positive signals"""

        positives = []

        if mood_entry.mood_score >= 7:
            positives.append("Hohe Stimmung")

        if mood_entry.exercise_minutes >= 30:
            positives.append("Ausreichend Bewegung")

        if mood_entry.sleep_quality >= 7 and mood_entry.sleep_hours >= 7:
            positives.append("Guter Schlaf")

        if mood_entry.activities and len(mood_entry.activities) >= 2:
            positives.append("Vielfältige Aktivitäten")

        return positives

    def _generate_recommendations(self, mood_entry: MoodEntry) -> List[str]:
        """Generate specific recommendations for this entry"""

        recommendations = []

        if mood_entry.mood_score <= 4:
            recommendations.append("🤗 Sei liebevoll zu dir selbst heute")

        if mood_entry.stress_level >= 7:
            recommendations.append("🧘 Probiere eine 5-minütige Atemübung")

        if mood_entry.exercise_minutes == 0:
            recommendations.append("🚶 Ein kurzer Spaziergang könnte helfen")

        if mood_entry.sleep_hours < 6:
            recommendations.append("😴 Prioritisiere heute guten Schlaf")

        return recommendations[:3]

    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate simple correlation coefficient"""

        if len(x) != len(y) or len(x) < 2:
            return 0.0

        n = len(x)
        mean_x = sum(x) / n
        mean_y = sum(y) / n

        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        denominator_x = sum((x[i] - mean_x) ** 2 for i in range(n))
        denominator_y = sum((y[i] - mean_y) ** 2 for i in range(n))

        if denominator_x == 0 or denominator_y == 0:
            return 0.0

        return numerator / (denominator_x * denominator_y) ** 0.5

    def _interpret_correlation(self, correlation: float, factor: str) -> str:
        """Interpret correlation coefficient"""

        if abs(correlation) < 0.3:
            return f"Schwacher Zusammenhang zwischen Stimmung und {factor}"
        elif abs(correlation) < 0.7:
            return f"Moderater Zusammenhang zwischen Stimmung und {factor}"
        else:
            direction = "positiver" if correlation > 0 else "negativer"
            return f"Starker {direction} Zusammenhang zwischen Stimmung und {factor}"

    async def _get_recent_entries(self, user_id: str, days: int) -> List[MoodEntry]:
        """Get recent mood entries"""

        start_date = datetime.now() - timedelta(days=days)

        result = await self.db.execute(
            select(MoodEntry)
            .where(
                and_(
                    MoodEntry.user_id == uuid.UUID(user_id),
                    MoodEntry.created_at >= start_date,
                )
            )
            .order_by(MoodEntry.entry_date)
        )

        return list(result.scalars().all())

    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of values"""

        if len(values) < 2:
            return 0.0

        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / len(values)

    def _get_sleep_recommendation(self, quality: int, hours: float) -> str:
        """Get sleep recommendation"""

        if hours < 6:
            return "Versuche 7-9 Stunden Schlaf zu bekommen"
        elif quality <= 4:
            return "Arbeite an der Schlafqualität: regelmäßige Zeiten, dunkler Raum"
        else:
            return "Dein Schlaf scheint gut zu sein - weiter so!"

    def _get_activity_recommendation(
        self, activity_count: int, exercise_minutes: int
    ) -> str:
        """Get activity recommendation"""

        if exercise_minutes == 0:
            return "Baue täglich 10-15 Minuten Bewegung ein"
        elif activity_count < 2:
            return "Probiere verschiedene Aktivitäten für mehr Abwechslung"
        else:
            return "Gute Aktivitätsbalance!"

    async def get_mood_trends(
        self, user_id: str, start_date: datetime
    ) -> Dict[str, Any]:
        """Get mood trends over time period"""

        entries = await self._get_recent_entries(
            user_id,
            days=(datetime.now() - start_date).days
        )

        if not entries:
            return {
                "trend": "no_data",
                "average_mood": 5.0,
                "data_points": [],
                "message": "Nicht genug Daten verfügbar",
            }

        # Calculate trend
        mood_scores = [e.mood_score for e in entries]
        avg_mood = sum(mood_scores) / len(mood_scores)

        # Calculate trend direction
        mid_point = len(mood_scores) // 2
        if mid_point > 0:
            first_half = sum(mood_scores[:mid_point]) / mid_point
            second_half = sum(mood_scores[mid_point:]) / (len(mood_scores) - mid_point)
            change = second_half - first_half

            if change > 0.5:
                trend = "improving"
            elif change < -0.5:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"

        # Prepare data points
        data_points = [
            {
                "date": e.entry_date.isoformat(),
                "mood": e.mood_score,
                "stress": e.stress_level,
                "energy": e.energy_level,
            }
            for e in entries
        ]

        return {
            "trend": trend,
            "average_mood": round(avg_mood, 1),
            "highest_mood": max(mood_scores),
            "lowest_mood": min(mood_scores),
            "data_points": data_points,
            "total_entries": len(entries),
        }

    async def detect_patterns(self, user_id: str) -> Dict[str, Any]:
        """Detect mood patterns and correlations"""

        patterns_data = await self.find_mood_patterns(user_id, days=30)

        return {
            "patterns_detected": True,
            "patterns": patterns_data,
            "message": "Muster erfolgreich erkannt",
        }
