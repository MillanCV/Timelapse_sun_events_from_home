import asyncio
import logging
from datetime import datetime
from typing import Optional

from ...sun_events.application.use_cases import (
    CheckUpcomingEventsRequest,
    CheckUpcomingSunEventsUseCase,
    GetCurrentEventRequest,
    GetCurrentSunEventUseCase,
)
from ...sun_events.domain.entities import SunEventPeriod
from ...sun_events.domain.repositories import SunEventRepository
from .sun_event_orchestrator import SunEventOrchestrator


class SunEventMonitorService:
    """Background service for monitoring sun events."""

    def __init__(
        self,
        sun_event_repository: SunEventRepository,
        orchestrator: SunEventOrchestrator,
        check_interval_seconds: int = 60,
        look_ahead_minutes: int = 1440,  # 24 hours
        error_retry_seconds: int = 60,
        no_events_retry_seconds: int = 3600,  # 1 hour
    ):
        self.sun_event_repository = sun_event_repository
        self.orchestrator = orchestrator
        self.check_interval_seconds = check_interval_seconds
        self.look_ahead_minutes = look_ahead_minutes
        self.error_retry_seconds = error_retry_seconds
        self.no_events_retry_seconds = no_events_retry_seconds

        # Initialize use cases
        self.get_current_use_case = GetCurrentSunEventUseCase(sun_event_repository)
        self.check_upcoming_use_case = CheckUpcomingSunEventsUseCase(
            sun_event_repository
        )

        self.logger = logging.getLogger(__name__)
        self._is_running = False
        self._current_period: Optional[SunEventPeriod] = None

    async def start(self):
        """Start the background monitoring service."""
        self._is_running = True
        self.logger.info("Starting sun event monitor service")

        while self._is_running:
            try:
                wait_seconds = await self._execute_monitor_cycle()
                if wait_seconds > 0:
                    await asyncio.sleep(wait_seconds)
            except Exception as e:
                self.logger.error(f"Error in monitor cycle: {e}")
                await asyncio.sleep(self.error_retry_seconds)

    def stop(self):
        """Stop the background monitoring service."""
        self._is_running = False
        self.logger.info("Stopping sun event monitor service")

    async def _execute_monitor_cycle(self) -> float:
        """Execute one monitoring cycle and return wait time in seconds."""
        current_time = datetime.now()

        # Check if we're currently in a sun event period
        current_response = self.get_current_use_case.execute(
            GetCurrentEventRequest(current_time=current_time)
        )

        if current_response.current_period:
            return await self._handle_current_period(
                current_response.current_period, current_time
            )
        else:
            return await self._handle_no_current_period(current_time)

    async def _handle_current_period(
        self, current_period: SunEventPeriod, current_time: datetime
    ) -> float:
        """Handle case when we're in a sun event period."""
        # Check if this is a new period
        if self._current_period != current_period:
            # Delegate to orchestrator for handling period start
            await self.orchestrator.handle_period_start(current_period)
            self._current_period = current_period

        # Calculate wait time until period ends
        wait_seconds = (current_period.end_time - current_time).total_seconds()

        if wait_seconds > 0:
            self.logger.info(
                f"In {current_period.period_type} period, "
                f"waiting {wait_seconds:.0f} seconds until it ends"
            )
        else:
            # Delegate to orchestrator for handling period end
            await self.orchestrator.handle_period_end(current_period)
            self._current_period = None

        return max(0, wait_seconds)

    async def _handle_no_current_period(self, current_time: datetime) -> float:
        """Handle case when we're not in a sun event period."""
        # Log end of previous period if any
        if self._current_period:
            await self.orchestrator.handle_period_end(self._current_period)
            self._current_period = None

        # Check for upcoming events
        upcoming_response = self.check_upcoming_use_case.execute(
            CheckUpcomingEventsRequest(
                current_time=current_time,
                look_ahead_minutes=self.look_ahead_minutes,
            )
        )

        if upcoming_response.upcoming_periods:
            self._log_upcoming_periods(upcoming_response.upcoming_periods)

            # Find the first upcoming period
            first_period = min(
                upcoming_response.upcoming_periods, key=lambda p: p.start_time
            )
            wait_seconds = (first_period.start_time - current_time).total_seconds()

            if wait_seconds > 0:
                self.logger.info(
                    f"Next {first_period.period_type} period starts in "
                    f"{wait_seconds:.0f} seconds "
                    f"(at {first_period.start_time.strftime('%H:%M:%S')})"
                )
            else:
                # Period should start now, continue immediately
                wait_seconds = 0

            return max(0, wait_seconds)
        else:
            # No upcoming periods, wait longer
            self.logger.info(
                "No upcoming sun events in 24 hours, checking again in 1 hour"
            )
            return self.no_events_retry_seconds

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

    @property
    def is_running(self) -> bool:
        """Check if the service is running."""
        return self._is_running

    @property
    def current_period(self) -> Optional[SunEventPeriod]:
        """Get the current period if any."""
        return self._current_period
