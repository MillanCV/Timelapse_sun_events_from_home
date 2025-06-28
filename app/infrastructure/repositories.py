import sqlite3
from datetime import datetime
from typing import List, Optional

from ..domain.entities import SunEvent
from ..domain.repositories import SunEventRepository


class SQLiteSunEventRepository(SunEventRepository):
    """SQLite implementation of SunEventRepository."""

    def __init__(self, db_path: str = "sun_events.db"):
        self.db_path = db_path

    def _parse_datetime(self, dt_str: str) -> datetime:
        """Parse datetime string from SQLite to Python datetime."""
        # Handle timezone info if present
        if "+" in dt_str:
            dt_str = dt_str.split("+")[0]
        elif "-" in dt_str and dt_str.count("-") > 2:
            # Handle timezone offset in the middle
            parts = dt_str.split("-")
            if len(parts) > 3:
                dt_str = "-".join(parts[:-2]) + parts[-1]

        # Try different formats
        formats = [
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(dt_str, fmt)
            except ValueError:
                continue

        raise ValueError(f"Could not parse datetime: {dt_str}")

    def _row_to_sun_event(self, row: tuple) -> SunEvent:
        """Convert database row to SunEvent domain entity."""
        return SunEvent(
            id=row[0],
            date=self._parse_datetime(row[1]),
            dawn=self._parse_datetime(row[2]),
            sunrise=self._parse_datetime(row[3]),
            culmination=self._parse_datetime(row[4]),
            sunset=self._parse_datetime(row[5]),
            dusk=self._parse_datetime(row[6]),
            sun_altitude=float(row[7]),
            azimuth=float(row[8]),
            magic_hour_morning_start=self._parse_datetime(row[9]),
            magic_hour_morning_end=self._parse_datetime(row[10]),
            magic_hour_evening_start=self._parse_datetime(row[11]),
            magic_hour_evening_end=self._parse_datetime(row[12]),
            golden_hour_morning_start=self._parse_datetime(row[13]),
            golden_hour_morning_end=self._parse_datetime(row[14]),
            golden_hour_evening_start=self._parse_datetime(row[15]),
            golden_hour_evening_end=self._parse_datetime(row[16]),
            blue_hour_morning_start=self._parse_datetime(row[17]),
            blue_hour_morning_end=self._parse_datetime(row[18]),
            blue_hour_evening_start=self._parse_datetime(row[19]),
            blue_hour_evening_end=self._parse_datetime(row[20]),
        )

    async def get_sun_event_by_date(self, date: datetime) -> Optional[SunEvent]:
        """Get sun event for a specific date."""
        return self.get_sun_event_by_date_sync(date)

    def get_sun_event_by_date_sync(self, date: datetime) -> Optional[SunEvent]:
        """Synchronous version for use in background tasks."""
        date_str = date.strftime("%Y-%m-%d")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM sun_events WHERE date LIKE ?", (f"{date_str}%",)
            )
            row = cursor.fetchone()

            if row:
                return self._row_to_sun_event(row)
            return None

    async def get_upcoming_sun_events(
        self, from_date: datetime, limit: int = 10
    ) -> List[SunEvent]:
        """Get upcoming sun events from a specific date."""
        from_date_str = from_date.strftime("%Y-%m-%d")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM sun_events WHERE date >= ? ORDER BY date LIMIT ?",
                (from_date_str, limit),
            )
            rows = cursor.fetchall()

            return [self._row_to_sun_event(row) for row in rows]

    async def get_sun_events_in_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[SunEvent]:
        """Get sun events within a date range."""
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM sun_events WHERE date BETWEEN ? AND ? ORDER BY date",
                (start_date_str, end_date_str),
            )
            rows = cursor.fetchall()

            return [self._row_to_sun_event(row) for row in rows]
