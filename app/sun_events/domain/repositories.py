from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from .entities import SunEvent


class SunEventRepository(ABC):
    """Abstract base class for sun event repositories."""

    @abstractmethod
    async def get_sun_event_by_date(self, date: datetime) -> Optional[SunEvent]:
        """Get sun event for a specific date."""
        pass

    @abstractmethod
    def get_sun_event_by_date_sync(self, date: datetime) -> Optional[SunEvent]:
        """Synchronous version for use in background tasks."""
        pass

    @abstractmethod
    async def get_upcoming_sun_events(
        self, from_date: datetime, limit: int = 10
    ) -> List[SunEvent]:
        """Get upcoming sun events from a specific date."""
        pass

    @abstractmethod
    def get_upcoming_sun_events_sync(
        self, from_date: datetime, limit: int = 10
    ) -> List[SunEvent]:
        """Synchronous version for getting upcoming sun events."""
        pass

    @abstractmethod
    async def get_sun_events_in_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[SunEvent]:
        """Get sun events within a date range."""
        pass
