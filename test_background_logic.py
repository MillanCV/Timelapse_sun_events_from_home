#!/usr/bin/env python3
"""
Test script to verify the background service logic without running the full server.
"""

import asyncio
import logging
from datetime import datetime

from app.application.use_cases import (
    CheckUpcomingEventsRequest,
    GetCurrentEventRequest,
    GetCurrentSunEventUseCase,
    CheckUpcomingSunEventsUseCase,
)
from app.infrastructure.json_repository import JSONSunEventRepository


async def test_background_logic():
    """Test the background service logic."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)

    # Initialize repository
    repository = JSONSunEventRepository()

    # Initialize use cases
    get_current_use_case = GetCurrentSunEventUseCase(repository)
    check_upcoming_use_case = CheckUpcomingSunEventsUseCase(repository)

    # Test current time
    current_time = datetime.now()
    logger.info(f"Current time: {current_time}")

    # Test getting current event
    current_response = get_current_use_case.execute(
        GetCurrentEventRequest(current_time=current_time)
    )

    if current_response.current_period:
        logger.info(
            f"Currently in {current_response.current_period.period_type} period"
        )
        logger.info(
            f"Period: {current_response.current_period.start_time} - {current_response.current_period.end_time}"
        )
    else:
        logger.info("Not currently in any sun event period")

    # Test checking upcoming events
    upcoming_response = check_upcoming_use_case.execute(
        CheckUpcomingEventsRequest(current_time=current_time, look_ahead_minutes=30)
    )

    if upcoming_response.upcoming_periods:
        logger.info(
            f"Found {len(upcoming_response.upcoming_periods)} upcoming periods:"
        )
        for period in upcoming_response.upcoming_periods:
            time_until_start = (period.start_time - current_time).total_seconds() / 60
            logger.info(
                f"  {period.period_type.upper()}: {period.start_time.strftime('%H:%M:%S')} - {period.end_time.strftime('%H:%M:%S')} (in {time_until_start:.0f} minutes)"
            )
    else:
        logger.info("No upcoming sun events in the next 30 minutes")

    logger.info(f"Next check time: {upcoming_response.next_check_time}")


if __name__ == "__main__":
    asyncio.run(test_background_logic())
