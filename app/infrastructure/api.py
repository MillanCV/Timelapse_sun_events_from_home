import asyncio
import logging
import threading
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ..application.use_cases import (
    CheckUpcomingEventsRequest,
    GetCurrentEventRequest,
    GetCurrentSunEventUseCase,
)
from .background_service import SunEventMonitorService
from .json_repository import JSONSunEventRepository


class SunEventPeriodResponse(BaseModel):
    """Response model for sun event period."""

    period_type: str
    start_time: datetime
    end_time: datetime
    event_date: datetime
    sun_altitude: float
    azimuth: float


class StatusResponse(BaseModel):
    """Response model for service status."""

    status: str
    current_period: Optional[SunEventPeriodResponse] = None
    next_check_time: Optional[datetime] = None


# Global variables for service management
monitor_service: Optional[SunEventMonitorService] = None
monitor_thread: Optional[threading.Thread] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global monitor_service, monitor_thread

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Initialize repository and service
    repository = JSONSunEventRepository()
    monitor_service = SunEventMonitorService(repository)

    # Start background task in a separate thread
    def run_monitor():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(monitor_service.start())

    monitor_thread = threading.Thread(target=run_monitor, daemon=True)
    monitor_thread.start()

    yield

    # Cleanup
    if monitor_service:
        monitor_service.stop()
    if monitor_thread and monitor_thread.is_alive():
        monitor_thread.join(timeout=5)


app = FastAPI(
    title="Sun Events Monitor",
    description="FastAPI service for monitoring sun events",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/", response_model=dict)
async def root():
    """Root endpoint."""
    return {
        "message": "Sun Events Monitor API",
        "version": "1.0.0",
        "endpoints": {
            "status": "/status",
            "current": "/current",
            "upcoming": "/upcoming",
        },
    }


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get current service status."""
    if not monitor_service:
        raise HTTPException(status_code=503, detail="Service not initialized")

    current_time = datetime.now()
    get_current_use_case = GetCurrentSunEventUseCase(
        monitor_service.sun_event_repository
    )

    current_response = get_current_use_case.execute(
        GetCurrentEventRequest(current_time=current_time)
    )

    current_period = None
    if current_response.current_period:
        current_period = SunEventPeriodResponse(
            period_type=current_response.current_period.period_type,
            start_time=current_response.current_period.start_time,
            end_time=current_response.current_period.end_time,
            event_date=current_response.current_period.event_date,
            sun_altitude=current_response.current_period.sun_event.sun_altitude,
            azimuth=current_response.current_period.sun_event.azimuth,
        )

    return StatusResponse(
        status="running",
        current_period=current_period,
        next_check_time=current_time + timedelta(minutes=5),
    )


@app.get("/current")
async def get_current_event():
    """Get current sun event period if any."""
    if not monitor_service:
        raise HTTPException(status_code=503, detail="Service not initialized")

    current_time = datetime.now()
    get_current_use_case = GetCurrentSunEventUseCase(
        monitor_service.sun_event_repository
    )

    current_response = get_current_use_case.execute(
        GetCurrentEventRequest(current_time=current_time)
    )

    if not current_response.current_period:
        return {"message": "No current sun event period"}

    period = current_response.current_period
    return {
        "period_type": period.period_type,
        "start_time": period.start_time,
        "end_time": period.end_time,
        "event_date": period.event_date,
        "sun_altitude": period.sun_event.sun_altitude,
        "azimuth": period.sun_event.azimuth,
        "remaining_minutes": (period.end_time - current_time).total_seconds() / 60,
    }


@app.get("/upcoming")
async def get_upcoming_events(look_ahead_minutes: int = 30):
    """Get upcoming sun events."""
    if not monitor_service:
        raise HTTPException(status_code=503, detail="Service not initialized")

    current_time = datetime.now()
    check_upcoming_use_case = monitor_service.check_upcoming_use_case

    upcoming_response = check_upcoming_use_case.execute(
        CheckUpcomingEventsRequest(
            current_time=current_time, look_ahead_minutes=look_ahead_minutes
        )
    )

    upcoming_periods = []
    for period in upcoming_response.upcoming_periods:
        time_until_start = (period.start_time - current_time).total_seconds() / 60

        upcoming_periods.append(
            {
                "period_type": period.period_type,
                "start_time": period.start_time,
                "end_time": period.end_time,
                "event_date": period.event_date,
                "sun_altitude": period.sun_event.sun_altitude,
                "azimuth": period.sun_event.azimuth,
                "minutes_until_start": time_until_start,
            }
        )

    return {
        "upcoming_periods": upcoming_periods,
        "next_check_time": upcoming_response.next_check_time,
    }
