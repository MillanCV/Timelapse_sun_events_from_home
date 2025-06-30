from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from ..domain.entities import SunEventPeriod
from ..domain.repositories import SunEventRepository


@dataclass
class GetCurrentEventRequest:
    """Request for getting current sun event."""

    current_time: datetime


@dataclass
class GetCurrentEventResponse:
    """Response for getting current sun event."""

    current_period: Optional[SunEventPeriod]


@dataclass
class CheckUpcomingEventsRequest:
    """Request for checking upcoming sun events."""

    current_time: datetime
    look_ahead_minutes: int


@dataclass
class CheckUpcomingEventsResponse:
    """Response for checking upcoming sun events."""

    upcoming_periods: List[SunEventPeriod]


class GetCurrentSunEventUseCase:
    """Use case for getting the current sun event period."""

    def __init__(self, sun_event_repository: SunEventRepository):
        self.sun_event_repository = sun_event_repository

    def execute(self, request: GetCurrentEventRequest) -> GetCurrentEventResponse:
        """Execute the use case."""
        current_time = request.current_time
        current_date = current_time.date()

        # Get today's sun event
        today_event = self.sun_event_repository.get_sun_event_by_date_sync(
            datetime.combine(current_date, datetime.min.time())
        )

        if not today_event:
            return GetCurrentEventResponse(current_period=None)

        # Check if we're in a sunrise period
        sunrise_start = today_event.golden_hour_morning_start
        sunrise_end = today_event.golden_hour_morning_end + timedelta(minutes=30)

        if sunrise_start <= current_time <= sunrise_end:
            return GetCurrentEventResponse(
                current_period=SunEventPeriod(
                    period_type="sunrise",
                    event_date=today_event.date,
                    start_time=sunrise_start,
                    end_time=sunrise_end,
                )
            )

        # Check if we're in a sunset period
        sunset_start = today_event.golden_hour_evening_start - timedelta(minutes=30)
        sunset_end = today_event.dusk

        if sunset_start <= current_time <= sunset_end:
            return GetCurrentEventResponse(
                current_period=SunEventPeriod(
                    period_type="sunset",
                    event_date=today_event.date,
                    start_time=sunset_start,
                    end_time=sunset_end,
                )
            )

        return GetCurrentEventResponse(current_period=None)


class CheckUpcomingSunEventsUseCase:
    """Use case for checking upcoming sun events."""

    def __init__(self, sun_event_repository: SunEventRepository):
        self.sun_event_repository = sun_event_repository

    def execute(
        self, request: CheckUpcomingEventsRequest
    ) -> CheckUpcomingEventsResponse:
        """Execute the use case."""
        current_time = request.current_time
        look_ahead_minutes = request.look_ahead_minutes
        end_time = current_time + timedelta(minutes=look_ahead_minutes)

        upcoming_periods = []

        # Get events for the next few days
        current_date = current_time.date()
        for days_ahead in range(7):  # Check next 7 days
            check_date = current_date + timedelta(days=days_ahead)
            sun_event = self.sun_event_repository.get_sun_event_by_date_sync(
                datetime.combine(check_date, datetime.min.time())
            )

            if not sun_event:
                continue

            # Calculate sunrise period
            sunrise_start = sun_event.golden_hour_morning_start
            sunrise_end = sun_event.golden_hour_morning_end + timedelta(minutes=30)

            if sunrise_start >= current_time and sunrise_start <= end_time:
                upcoming_periods.append(
                    SunEventPeriod(
                        period_type="sunrise",
                        event_date=sun_event.date,
                        start_time=sunrise_start,
                        end_time=sunrise_end,
                    )
                )

            # Calculate sunset period
            sunset_start = sun_event.golden_hour_evening_start - timedelta(minutes=30)
            sunset_end = sun_event.dusk

            if sunset_start >= current_time and sunset_start <= end_time:
                upcoming_periods.append(
                    SunEventPeriod(
                        period_type="sunset",
                        event_date=sun_event.date,
                        start_time=sunset_start,
                        end_time=sunset_end,
                    )
                )

        # Sort by start time
        upcoming_periods.sort(key=lambda x: x.start_time)

        return CheckUpcomingEventsResponse(upcoming_periods=upcoming_periods)
