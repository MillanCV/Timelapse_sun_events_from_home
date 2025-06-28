import asyncio
import logging
from datetime import datetime
from typing import Optional

from ..application.use_cases import (
    CheckUpcomingEventsRequest,
    CheckUpcomingSunEventsUseCase,
    GetCurrentEventRequest,
    GetCurrentSunEventUseCase,
)
from ..domain.entities import SunEventPeriod
from ..domain.repositories import SunEventRepository


class SunEventMonitorService:
    """Background service for monitoring sun events."""

    def __init__(
        self, sun_event_repository: SunEventRepository, check_interval_seconds: int = 60
    ):
        self.sun_event_repository = sun_event_repository
        self.check_interval_seconds = check_interval_seconds
        self.check_upcoming_use_case = CheckUpcomingSunEventsUseCase(
            sun_event_repository
        )
        self.get_current_use_case = GetCurrentSunEventUseCase(sun_event_repository)
        self.logger = logging.getLogger(__name__)
        self._running = False
        self._current_period: Optional[SunEventPeriod] = None
        self._next_check_time: Optional[datetime] = None

    async def start(self):
        """Start the background monitoring service."""
        self._running = True
        self.logger.info("Starting sun event monitor service")

        while self._running:
            try:
                await self._monitor_cycle()
            except Exception as e:
                self.logger.error(f"Error in monitor cycle: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error

    def stop(self):
        """Stop the background monitoring service."""
        self._running = False
        self.logger.info("Stopping sun event monitor service")

    async def _monitor_cycle(self):
        """Execute one monitoring cycle."""
        current_time = datetime.now()

        # Check if we're currently in a sun event period
        current_response = self.get_current_use_case.execute(
            GetCurrentEventRequest(current_time=current_time)
        )

        if current_response.current_period:
            if self._current_period != current_response.current_period:
                self._current_period = current_response.current_period
                self._log_period_start(current_response.current_period)

            # We're in a period, wait until it ends
            wait_seconds = (
                current_response.current_period.end_time - current_time
            ).total_seconds()

            if wait_seconds > 0:
                self.logger.info(
                    f"In {current_response.current_period.period_type} period, "
                    f"waiting {wait_seconds:.0f} seconds until it ends"
                )
                await asyncio.sleep(min(wait_seconds, 60))  # Check every minute
            else:
                self._log_period_end(current_response.current_period)
                self._current_period = None
        else:
            # Not in a period, check for upcoming events
            if self._current_period:
                self._log_period_end(self._current_period)
                self._current_period = None

            upcoming_response = self.check_upcoming_use_case.execute(
                CheckUpcomingEventsRequest(
                    current_time=current_time, look_ahead_minutes=30
                )
            )

            if upcoming_response.upcoming_periods:
                self._log_upcoming_periods(upcoming_response.upcoming_periods)
                # Wait until the first upcoming period starts
                first_period = min(
                    upcoming_response.upcoming_periods, key=lambda p: p.start_time
                )
                wait_seconds = (first_period.start_time - current_time).total_seconds()

                if wait_seconds > 0:
                    self.logger.info(
                        f"Next {first_period.period_type} period starts in "
                        f"{wait_seconds:.0f} seconds"
                    )
                    await asyncio.sleep(min(wait_seconds, 60))
                else:
                    # Period should start now, return to continue to next cycle
                    return
            else:
                # No upcoming periods, wait for next check
                self.logger.info("No upcoming sun events, waiting 1 minute")
                await asyncio.sleep(self.check_interval_seconds)  # 1 minute

    def _log_period_start(self, period: SunEventPeriod):
        """Log when a sun event period starts."""
        self.logger.info(
            f"🌅 {period.period_type.upper()} PERIOD STARTING\n"
            f"   Date: {period.event_date.strftime('%Y-%m-%d')}\n"
            f"   Start: {period.start_time.strftime('%H:%M:%S')}\n"
            f"   End: {period.end_time.strftime('%H:%M:%S')}\n"
            f"   Duration: {(period.end_time - period.start_time).total_seconds() / 60:.0f} minutes"
        )

    def _log_period_end(self, period: SunEventPeriod):
        """Log when a sun event period ends."""
        self.logger.info(
            f"🌅 {period.period_type.upper()} PERIOD ENDED\n"
            f"   Date: {period.event_date.strftime('%Y-%m-%d')}\n"
            f"   Duration: {(period.end_time - period.start_time).total_seconds() / 60:.0f} minutes"
        )

    def _log_upcoming_periods(self, periods: list[SunEventPeriod]):
        """Log upcoming sun event periods."""
        self.logger.info("🔍 UPCOMING SUN EVENTS:")
        for period in periods:
            time_until_start = (period.start_time - datetime.now()).total_seconds() / 60

            self.logger.info(
                f"   {period.period_type.upper()}: "
                f"{period.start_time.strftime('%H:%M:%S')} - "
                f"{period.end_time.strftime('%H:%M:%S')} "
                f"(in {time_until_start:.0f} minutes)"
            )
