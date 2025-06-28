import json
from datetime import datetime, time
from typing import List, Optional

from ..domain.entities import SunEvent
from ..domain.repositories import SunEventRepository


class JSONSunEventRepository(SunEventRepository):
    """JSON file implementation of SunEventRepository."""

    def __init__(self, config_file: str = "config/sun_events.json"):
        self.config_file = config_file
        self._cache = None
        self._load_data()

    def _load_data(self):
        """Load sun events data from JSON file."""
        try:
            with open(self.config_file, "r") as f:
                data = json.load(f)
                self._cache = data.get("sun_events", {})
        except FileNotFoundError:
            self._cache = {}
        except json.JSONDecodeError:
            self._cache = {}

    def _parse_time(self, time_str: str) -> time:
        """Parse time string to time object."""
        return datetime.strptime(time_str, "%H:%M:%S").time()

    def _combine_date_time(self, date: datetime, time_str: str) -> datetime:
        """Combine date with time string to create datetime."""
        time_obj = self._parse_time(time_str)
        return datetime.combine(date.date(), time_obj)

    def _row_to_sun_event(self, date_str: str, event_data: dict) -> SunEvent:
        """Convert JSON data to SunEvent domain entity."""
        date = datetime.strptime(date_str, "%Y-%m-%d")

        return SunEvent(
            id=hash(date_str),  # Use hash as simple ID
            date=date,
            dawn=self._combine_date_time(date, event_data["dawn"]),
            sunrise=self._combine_date_time(date, event_data["sunrise"]),
            culmination=self._combine_date_time(date, event_data["culmination"]),
            sunset=self._combine_date_time(date, event_data["sunset"]),
            dusk=self._combine_date_time(date, event_data["dusk"]),
            sun_altitude=event_data["sun_altitude"],
            azimuth=event_data["azimuth"],
            magic_hour_morning_start=self._combine_date_time(
                date, event_data["magic_hour_morning_start"]
            ),
            magic_hour_morning_end=self._combine_date_time(
                date, event_data["magic_hour_morning_end"]
            ),
            magic_hour_evening_start=self._combine_date_time(
                date, event_data["magic_hour_evening_start"]
            ),
            magic_hour_evening_end=self._combine_date_time(
                date, event_data["magic_hour_evening_end"]
            ),
            golden_hour_morning_start=self._combine_date_time(
                date, event_data["golden_hour_morning_start"]
            ),
            golden_hour_morning_end=self._combine_date_time(
                date, event_data["golden_hour_morning_end"]
            ),
            golden_hour_evening_start=self._combine_date_time(
                date, event_data["golden_hour_evening_start"]
            ),
            golden_hour_evening_end=self._combine_date_time(
                date, event_data["golden_hour_evening_end"]
            ),
            blue_hour_morning_start=self._combine_date_time(
                date, event_data["blue_hour_morning_start"]
            ),
            blue_hour_morning_end=self._combine_date_time(
                date, event_data["blue_hour_morning_end"]
            ),
            blue_hour_evening_start=self._combine_date_time(
                date, event_data["blue_hour_evening_start"]
            ),
            blue_hour_evening_end=self._combine_date_time(
                date, event_data["blue_hour_evening_end"]
            ),
        )

    async def get_sun_event_by_date(self, date: datetime) -> Optional[SunEvent]:
        """Get sun event for a specific date."""
        return self.get_sun_event_by_date_sync(date)

    def get_sun_event_by_date_sync(self, date: datetime) -> Optional[SunEvent]:
        """Synchronous version for use in background tasks."""
        date_str = date.strftime("%Y-%m-%d")

        if date_str in self._cache:
            return self._row_to_sun_event(date_str, self._cache[date_str])
        return None

    async def get_upcoming_sun_events(
        self, from_date: datetime, limit: int = 10
    ) -> List[SunEvent]:
        """Get upcoming sun events from a specific date."""
        return self.get_upcoming_sun_events_sync(from_date, limit)

    def get_upcoming_sun_events_sync(
        self, from_date: datetime, limit: int = 10
    ) -> List[SunEvent]:
        """Synchronous version for getting upcoming sun events."""
        from_date_str = from_date.strftime("%Y-%m-%d")

        events = []
        for date_str, event_data in self._cache.items():
            if date_str >= from_date_str and len(events) < limit:
                events.append(self._row_to_sun_event(date_str, event_data))

        # Sort by date
        events.sort(key=lambda x: x.date)
        return events

    async def get_sun_events_in_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[SunEvent]:
        """Get sun events within a date range."""
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        events = []
        for date_str, event_data in self._cache.items():
            if start_date_str <= date_str <= end_date_str:
                events.append(self._row_to_sun_event(date_str, event_data))

        # Sort by date
        events.sort(key=lambda x: x.date)
        return events
