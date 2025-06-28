from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from .entities import SunEvent


class SunEventRepository(ABC):
    """Repository interface for sun events."""

    @abstractmethod
    async def get_sun_event_by_date(self, date: datetime) -> Optional[SunEvent]:
        """Get sun event for a specific date."""
        pass

    @abstractmethod
    async def get_upcoming_sun_events(
        self, from_date: datetime, limit: int = 10
    ) -> list[SunEvent]:
        """Get upcoming sun events from a specific date."""
        pass

    @abstractmethod
    async def get_sun_events_in_range(
        self, start_date: datetime, end_date: datetime
    ) -> list[SunEvent]:
        """Get sun events within a date range."""
        pass
