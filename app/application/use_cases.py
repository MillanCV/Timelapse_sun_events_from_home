from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from ..domain.entities import SunEventPeriod
from ..domain.repositories import SunEventRepository


def is_same_day(dt1: datetime, dt2: datetime) -> bool:
    return dt1.date() == dt2.date()


@dataclass
class CheckUpcomingEventsRequest:
    """Request for checking upcoming sun events."""

    current_time: datetime
    look_ahead_minutes: int = 30


@dataclass
class CheckUpcomingEventsResponse:
    """Response containing upcoming sun event periods."""

    upcoming_periods: list[SunEventPeriod]
    next_check_time: datetime


class CheckUpcomingSunEventsUseCase:
    """Use case for checking upcoming sun events."""

    def __init__(self, sun_event_repository: SunEventRepository):
        self.sun_event_repository = sun_event_repository

    def execute(
        self, request: CheckUpcomingEventsRequest
    ) -> CheckUpcomingEventsResponse:
        """Execute the use case to check for upcoming sun events."""
        current_time = request.current_time
        look_ahead = timedelta(minutes=request.look_ahead_minutes)
        end_time = current_time + look_ahead

        today = current_time.date()
        tomorrow = today + timedelta(days=1)

        # Get events for today and tomorrow
        events = {}
        for date in [today, tomorrow]:
            event = self.sun_event_repository.get_sun_event_by_date_sync(
                datetime.combine(date, datetime.min.time())
            )
            if event:
                events[date] = event

        upcoming_periods = []

        # Check today's events
        if today in events:
            event = events[today]

            # SUNRISE PERIOD: dawn to golden_hour_morning_end + 30 min
            sunrise_end = event.golden_hour_morning_end + timedelta(minutes=30)
            if event.dawn > current_time and event.dawn <= end_time:
                upcoming_periods.append(
                    SunEventPeriod(
                        period_type="sunrise",
                        start_time=event.dawn,
                        end_time=sunrise_end,
                        event_date=event.date,
                        sun_event=event,
                    )
                )

            # SUNSET PERIOD: golden_hour_evening_start - 30 min to dusk
            sunset_start = event.golden_hour_evening_start - timedelta(minutes=30)
            if sunset_start > current_time and sunset_start <= end_time:
                upcoming_periods.append(
                    SunEventPeriod(
                        period_type="sunset",
                        start_time=sunset_start,
                        end_time=event.dusk,
                        event_date=event.date,
                        sun_event=event,
                    )
                )

        # Check tomorrow's sunrise period if within look_ahead
        if tomorrow in events:
            event = events[tomorrow]
            sunrise_end = event.golden_hour_morning_end + timedelta(minutes=30)
            if event.dawn > current_time and event.dawn <= end_time:
                upcoming_periods.append(
                    SunEventPeriod(
                        period_type="sunrise",
                        start_time=event.dawn,
                        end_time=sunrise_end,
                        event_date=event.date,
                        sun_event=event,
                    )
                )

        # Calculate next check time
        if upcoming_periods:
            latest_end = max(period.end_time for period in upcoming_periods)
            next_check_time = latest_end + timedelta(minutes=1)
        else:
            next_check_time = current_time + timedelta(minutes=5)

        return CheckUpcomingEventsResponse(
            upcoming_periods=upcoming_periods, next_check_time=next_check_time
        )


@dataclass
class GetCurrentEventRequest:
    """Request for getting current sun event."""

    current_time: datetime


@dataclass
class GetCurrentEventResponse:
    """Response containing current sun event period if any."""

    current_period: Optional[SunEventPeriod] = None


class GetCurrentSunEventUseCase:
    """Use case for getting current sun event period."""

    def __init__(self, sun_event_repository: SunEventRepository):
        self.sun_event_repository = sun_event_repository

    def execute(self, request: GetCurrentEventRequest) -> GetCurrentEventResponse:
        """Execute the use case to get current sun event period."""
        current_time = request.current_time
        today = current_time.date()

        event = self.sun_event_repository.get_sun_event_by_date_sync(
            datetime.combine(today, datetime.min.time())
        )

        if not event:
            return GetCurrentEventResponse()

        # Check sunrise period: dawn to golden_hour_morning_end + 30 min
        sunrise_end = event.golden_hour_morning_end + timedelta(minutes=30)
        if event.dawn <= current_time <= sunrise_end:
            return GetCurrentEventResponse(
                current_period=SunEventPeriod(
                    period_type="sunrise",
                    start_time=event.dawn,
                    end_time=sunrise_end,
                    event_date=event.date,
                    sun_event=event,
                )
            )

        # Check sunset period: golden_hour_evening_start - 30 min to dusk
        sunset_start = event.golden_hour_evening_start - timedelta(minutes=30)
        if sunset_start <= current_time <= event.dusk:
            return GetCurrentEventResponse(
                current_period=SunEventPeriod(
                    period_type="sunset",
                    start_time=sunset_start,
                    end_time=event.dusk,
                    event_date=event.date,
                    sun_event=event,
                )
            )

        return GetCurrentEventResponse()
