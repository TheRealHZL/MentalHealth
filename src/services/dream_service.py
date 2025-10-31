"""
Dream Service - Traumtagebuch Business Logic

Kernfunktionalität für Dream Journal ohne Therapeut-Abhängigkeit.
"""

import logging
import uuid
from collections import Counter
from datetime import date, datetime, time, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy import and_, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import DreamEntry, DreamType
from src.schemas.ai import DreamEntryCreate, DreamEntryUpdate, PaginationParams

logger = logging.getLogger(__name__)


class DreamService:
    """Dream Journal Service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =============================================================================
    # CRUD Operations
    # =============================================================================

    async def create_dream_entry(
        self, user_id: str, dream_data: DreamEntryCreate
    ) -> DreamEntry:
        """Create new dream entry"""

        dream_entry = DreamEntry(
            user_id=uuid.UUID(user_id),
            dream_date=dream_data.dream_date,
            dream_type=dream_data.dream_type,
            title=dream_data.title,
            description=dream_data.description,
            mood_during_dream=[mood.value for mood in dream_data.mood_during_dream],
            mood_after_waking=dream_data.mood_after_waking.value,
            people_in_dream=dream_data.people_in_dream,
            locations=dream_data.locations,
            symbols=dream_data.symbols,
            emotions_felt=dream_data.emotions_felt,
            sleep_quality=dream_data.sleep_quality,
            time_to_sleep=dream_data.time_to_sleep,
            wake_up_time=dream_data.wake_up_time,
            became_lucid=dream_data.became_lucid,
            lucid_actions=dream_data.lucid_actions,
            personal_interpretation=dream_data.personal_interpretation,
            life_connection=dream_data.life_connection,
            tags=dream_data.tags,
        )

        self.db.add(dream_entry)
        await self.db.commit()
        await self.db.refresh(dream_entry)

        logger.info(f"Created dream entry for user {user_id}: {dream_data.dream_type}")
        return dream_entry

    async def create_quick_dream_entry(
        self,
        user_id: str,
        description: str,
        dream_type: str = "normal",
        mood_after: int = 5,
    ) -> DreamEntry:
        """Create quick dream entry with minimal data"""

        # Convert string to enum
        try:
            dream_type_enum = DreamType(dream_type.lower())
        except ValueError:
            dream_type_enum = DreamType.NORMAL

        dream_entry = DreamEntry(
            user_id=uuid.UUID(user_id),
            dream_date=date.today(),
            dream_type=dream_type_enum,
            description=description,
            mood_after_waking=mood_after,
            sleep_quality=5,  # Default
            became_lucid=False,
            mood_during_dream=[],
            people_in_dream=[],
            locations=[],
            symbols=[],
            emotions_felt=[],
            tags=[],
        )

        self.db.add(dream_entry)
        await self.db.commit()
        await self.db.refresh(dream_entry)

        return dream_entry

    async def get_dream_entry_by_id(
        self, entry_id: str, user_id: str
    ) -> Optional[DreamEntry]:
        """Get dream entry by ID (user-scoped)"""

        result = await self.db.execute(
            select(DreamEntry).where(
                and_(
                    DreamEntry.id == uuid.UUID(entry_id),
                    DreamEntry.user_id == uuid.UUID(user_id),
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_dream_entries_paginated(
        self,
        user_id: str,
        pagination: PaginationParams,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        dream_type: Optional[str] = None,
        mood_range: Optional[str] = None,
    ) -> Tuple[List[DreamEntry], int]:
        """Get paginated dream entries with filters"""

        # Base query
        query = select(DreamEntry).where(DreamEntry.user_id == uuid.UUID(user_id))
        count_query = select(func.count(DreamEntry.id)).where(
            DreamEntry.user_id == uuid.UUID(user_id)
        )

        # Apply filters
        if start_date:
            query = query.where(DreamEntry.dream_date >= start_date)
            count_query = count_query.where(DreamEntry.dream_date >= start_date)

        if end_date:
            query = query.where(DreamEntry.dream_date <= end_date)
            count_query = count_query.where(DreamEntry.dream_date <= end_date)

        if dream_type:
            try:
                dream_type_enum = DreamType(dream_type.lower())
                query = query.where(DreamEntry.dream_type == dream_type_enum)
                count_query = count_query.where(
                    DreamEntry.dream_type == dream_type_enum
                )
            except ValueError:
                pass  # Invalid dream type, ignore filter

        if mood_range:
            mood_filter = self._get_mood_range_filter(mood_range)
            if mood_filter:
                query = query.where(mood_filter)
                count_query = count_query.where(mood_filter)

        # Sorting
        if pagination.sort_by == "date":
            order_col = DreamEntry.dream_date
        elif pagination.sort_by == "mood":
            order_col = DreamEntry.mood_after_waking
        else:
            order_col = DreamEntry.created_at

        if pagination.sort_order == "asc":
            query = query.order_by(asc(order_col))
        else:
            query = query.order_by(desc(order_col))

        # Pagination
        offset = (pagination.page - 1) * pagination.page_size
        query = query.offset(offset).limit(pagination.page_size)

        # Execute queries
        entries_result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)

        entries = list(entries_result.scalars().all())
        total_count = count_result.scalar()

        return entries, total_count

    async def update_dream_entry(
        self, entry_id: str, user_id: str, update_data: DreamEntryUpdate
    ) -> DreamEntry:
        """Update dream entry"""

        dream_entry = await self.get_dream_entry_by_id(entry_id, user_id)
        if not dream_entry:
            raise ValueError("Dream entry not found")

        # Update fields
        update_dict = update_data.dict(exclude_unset=True)

        for field, value in update_dict.items():
            if hasattr(dream_entry, field):
                if field == "mood_during_dream" and value:
                    setattr(dream_entry, field, [mood.value for mood in value])
                elif field == "mood_after_waking" and value:
                    setattr(dream_entry, field, value.value)
                else:
                    setattr(dream_entry, field, value)

        await self.db.commit()
        await self.db.refresh(dream_entry)

        return dream_entry

    async def delete_dream_entry(self, entry_id: str, user_id: str) -> bool:
        """Delete dream entry"""

        dream_entry = await self.get_dream_entry_by_id(entry_id, user_id)
        if not dream_entry:
            return False

        await self.db.delete(dream_entry)
        await self.db.commit()

        return True

    async def update_ai_analysis(
        self, entry_id: uuid.UUID, ai_analysis: Dict[str, Any]
    ) -> None:
        """Update AI analysis for dream entry"""

        result = await self.db.execute(
            select(DreamEntry).where(DreamEntry.id == entry_id)
        )
        dream_entry = result.scalar_one_or_none()

        if dream_entry:
            dream_entry.ai_dream_analysis = ai_analysis.get("ai_interpretation")
            dream_entry.symbol_interpretations = ai_analysis.get("symbol_meanings", {})
            dream_entry.emotional_insights = ai_analysis.get(
                "psychological_insights", []
            )

            await self.db.commit()

    # =============================================================================
    # Analytics & Statistics
    # =============================================================================

    async def get_dream_statistics(self, user_id: str, days: int) -> Dict[str, Any]:
        """Get dream statistics for time period"""

        start_date = datetime.now() - timedelta(days=days)

        result = await self.db.execute(
            select(DreamEntry).where(
                and_(
                    DreamEntry.user_id == uuid.UUID(user_id),
                    DreamEntry.created_at >= start_date,
                )
            )
        )

        entries = list(result.scalars().all())

        if not entries:
            return {"total_dreams": 0, "message": "Keine Träume in diesem Zeitraum"}

        # Basic statistics
        dream_types = [entry.dream_type.value for entry in entries]
        mood_scores = [entry.mood_after_waking for entry in entries]

        type_counter = Counter(dream_types)

        return {
            "total_dreams": len(entries),
            "avg_mood_after": round(sum(mood_scores) / len(mood_scores), 1),
            "dream_type_distribution": dict(type_counter),
            "most_common_type": (
                type_counter.most_common(1)[0][0] if type_counter else "none"
            ),
            "lucid_dreams": sum(1 for entry in entries if entry.became_lucid),
            "nightmares": sum(
                1 for entry in entries if entry.dream_type == DreamType.NIGHTMARE
            ),
            "dream_frequency": round(len(entries) / days, 2),
        }

    async def analyze_dream_patterns(self, user_id: str, days: int) -> Dict[str, Any]:
        """Analyze dream patterns over time"""

        start_date = datetime.now() - timedelta(days=days)

        result = await self.db.execute(
            select(DreamEntry)
            .where(
                and_(
                    DreamEntry.user_id == uuid.UUID(user_id),
                    DreamEntry.created_at >= start_date,
                )
            )
            .order_by(DreamEntry.dream_date)
        )

        entries = list(result.scalars().all())

        if len(entries) < 3:
            return {
                "total_dreams": len(entries),
                "message": "Mehr Träume für Muster-Analyse benötigt",
            }

        patterns = {
            "total_dreams": len(entries),
            "recurring_symbols": self._find_recurring_symbols(entries),
            "recurring_people": self._find_recurring_people(entries),
            "recurring_locations": self._find_recurring_locations(entries),
            "mood_patterns": self._analyze_mood_patterns(entries),
            "type_trends": self._analyze_type_trends(entries),
            "sleep_quality_correlation": self._analyze_sleep_correlation(entries),
        }

        return patterns

    async def get_common_dream_elements(
        self, user_id: str, limit: int = 30
    ) -> Dict[str, Any]:
        """Get most common dream elements for user"""

        # Get recent dreams
        start_date = datetime.now() - timedelta(days=limit)

        result = await self.db.execute(
            select(DreamEntry).where(
                and_(
                    DreamEntry.user_id == uuid.UUID(user_id),
                    DreamEntry.created_at >= start_date,
                )
            )
        )

        entries = list(result.scalars().all())

        # Collect all elements
        all_symbols = []
        all_people = []
        all_locations = []
        all_emotions = []

        for entry in entries:
            if entry.symbols:
                all_symbols.extend(entry.symbols)
            if entry.people_in_dream:
                all_people.extend(entry.people_in_dream)
            if entry.locations:
                all_locations.extend(entry.locations)
            if entry.emotions_felt:
                all_emotions.extend(entry.emotions_felt)

        return {
            "most_common_symbols": dict(Counter(all_symbols).most_common(5)),
            "most_common_people": dict(Counter(all_people).most_common(5)),
            "most_common_locations": dict(Counter(all_locations).most_common(5)),
            "most_common_emotions": dict(Counter(all_emotions).most_common(5)),
        }

    async def analyze_dream_quality_trends(self, user_id: str) -> Dict[str, Any]:
        """Analyze dream quality trends over time"""

        # Get last 30 dreams
        result = await self.db.execute(
            select(
                DreamEntry.mood_after_waking,
                DreamEntry.sleep_quality,
                DreamEntry.dream_date,
            )
            .where(DreamEntry.user_id == uuid.UUID(user_id))
            .order_by(desc(DreamEntry.dream_date))
            .limit(30)
        )

        data = list(result.all())

        if len(data) < 5:
            return {"message": "Mehr Daten für Trend-Analyse benötigt"}

        # Calculate trends
        mood_scores = [row.mood_after_waking for row in data]
        sleep_scores = [row.sleep_quality for row in data]

        # Simple trend calculation (first half vs second half)
        mid_point = len(mood_scores) // 2

        if mid_point > 0:
            early_mood = sum(mood_scores[:mid_point]) / mid_point
            late_mood = sum(mood_scores[mid_point:]) / (len(mood_scores) - mid_point)
            mood_trend = (
                "improving"
                if late_mood > early_mood + 0.5
                else "declining" if late_mood < early_mood - 0.5 else "stable"
            )

            early_sleep = sum(sleep_scores[:mid_point]) / mid_point
            late_sleep = sum(sleep_scores[mid_point:]) / (len(sleep_scores) - mid_point)
            sleep_trend = (
                "improving"
                if late_sleep > early_sleep + 0.5
                else "declining" if late_sleep < early_sleep - 0.5 else "stable"
            )
        else:
            mood_trend = "stable"
            sleep_trend = "stable"

        return {
            "mood_after_dreams_trend": mood_trend,
            "sleep_quality_trend": sleep_trend,
            "average_mood_after": round(sum(mood_scores) / len(mood_scores), 1),
            "average_sleep_quality": round(sum(sleep_scores) / len(sleep_scores), 1),
            "data_points": len(data),
        }

    def build_pattern_summary(self, patterns: Dict[str, Any]) -> str:
        """Build pattern summary for AI analysis"""

        summary_parts = [
            f"Gesamte Träume: {patterns.get('total_dreams', 0)}",
        ]

        if patterns.get("recurring_symbols"):
            symbols = ", ".join(patterns["recurring_symbols"][:3])
            summary_parts.append(f"Häufige Symbole: {symbols}")

        if patterns.get("recurring_people"):
            people = ", ".join(patterns["recurring_people"][:3])
            summary_parts.append(f"Häufige Personen: {people}")

        if patterns.get("mood_patterns"):
            mood_info = patterns["mood_patterns"]
            summary_parts.append(f"Stimmung nach Träumen: {mood_info}")

        return " | ".join(summary_parts)

    # =============================================================================
    # Helper Methods
    # =============================================================================

    def _get_mood_range_filter(self, mood_range: str):
        """Get SQL filter for mood range"""

        if mood_range == "low":
            return DreamEntry.mood_after_waking <= 4
        elif mood_range == "medium":
            return and_(
                DreamEntry.mood_after_waking > 4, DreamEntry.mood_after_waking <= 7
            )
        elif mood_range == "high":
            return DreamEntry.mood_after_waking > 7

        return None

    def _find_recurring_symbols(self, entries: List[DreamEntry]) -> List[str]:
        """Find symbols that appear in multiple dreams"""

        all_symbols = []
        for entry in entries:
            if entry.symbols:
                all_symbols.extend(entry.symbols)

        symbol_counts = Counter(all_symbols)
        # Return symbols that appear more than once
        return [symbol for symbol, count in symbol_counts.items() if count > 1]

    def _find_recurring_people(self, entries: List[DreamEntry]) -> List[str]:
        """Find people that appear in multiple dreams"""

        all_people = []
        for entry in entries:
            if entry.people_in_dream:
                all_people.extend(entry.people_in_dream)

        people_counts = Counter(all_people)
        return [person for person, count in people_counts.items() if count > 1]

    def _find_recurring_locations(self, entries: List[DreamEntry]) -> List[str]:
        """Find locations that appear in multiple dreams"""

        all_locations = []
        for entry in entries:
            if entry.locations:
                all_locations.extend(entry.locations)

        location_counts = Counter(all_locations)
        return [location for location, count in location_counts.items() if count > 1]

    def _analyze_mood_patterns(self, entries: List[DreamEntry]) -> Dict[str, Any]:
        """Analyze mood patterns in dreams"""

        mood_scores = [entry.mood_after_waking for entry in entries]

        return {
            "average": round(sum(mood_scores) / len(mood_scores), 1),
            "range": {"min": min(mood_scores), "max": max(mood_scores)},
            "distribution": {
                "low": sum(1 for mood in mood_scores if mood <= 4),
                "medium": sum(1 for mood in mood_scores if 4 < mood <= 7),
                "high": sum(1 for mood in mood_scores if mood > 7),
            },
        }

    def _analyze_type_trends(self, entries: List[DreamEntry]) -> Dict[str, Any]:
        """Analyze dream type trends over time"""

        # Group by weeks
        weekly_types = {}
        for entry in entries:
            week_key = entry.dream_date.strftime("%Y-W%U")
            if week_key not in weekly_types:
                weekly_types[week_key] = []
            weekly_types[week_key].append(entry.dream_type.value)

        return {
            "total_weeks": len(weekly_types),
            "nightmare_frequency": self._calculate_nightmare_frequency(entries),
            "lucid_frequency": self._calculate_lucid_frequency(entries),
        }

    def _analyze_sleep_correlation(self, entries: List[DreamEntry]) -> Dict[str, Any]:
        """Analyze correlation between sleep quality and dream mood"""

        sleep_scores = [entry.sleep_quality for entry in entries]
        mood_scores = [entry.mood_after_waking for entry in entries]

        # Simple correlation calculation
        if len(sleep_scores) > 1:
            correlation = self._calculate_simple_correlation(sleep_scores, mood_scores)

            return {
                "correlation_score": round(correlation, 2),
                "interpretation": self._interpret_correlation(correlation),
            }

        return {"message": "Nicht genug Daten für Korrelation"}

    def _calculate_nightmare_frequency(self, entries: List[DreamEntry]) -> float:
        """Calculate nightmare frequency"""

        nightmares = sum(
            1 for entry in entries if entry.dream_type == DreamType.NIGHTMARE
        )
        return round(nightmares / len(entries) * 100, 1) if entries else 0

    def _calculate_lucid_frequency(self, entries: List[DreamEntry]) -> float:
        """Calculate lucid dream frequency"""

        lucid_dreams = sum(1 for entry in entries if entry.became_lucid)
        return round(lucid_dreams / len(entries) * 100, 1) if entries else 0

    def _calculate_simple_correlation(self, x: List[float], y: List[float]) -> float:
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

    def _interpret_correlation(self, correlation: float) -> str:
        """Interpret correlation coefficient"""

        if abs(correlation) < 0.3:
            return "Schwacher Zusammenhang zwischen Schlafqualität und Traumstimmung"
        elif abs(correlation) < 0.7:
            return "Moderater Zusammenhang zwischen Schlafqualität und Traumstimmung"
        else:
            direction = "Positiver" if correlation > 0 else "Negativer"
            return f"{direction} starker Zusammenhang zwischen Schlafqualität und Traumstimmung"
