from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from ...camera.application.use_cases import (
    ShootCameraRequest,
    ShootCameraUseCase,
)
from ...camera.infrastructure.chdkptp_camera_service import (
    CHDKPTPCameraService,
    CHDKPTPScriptGenerator,
)
from ...sun_events.application.use_cases import (
    CheckUpcomingEventsRequest,
    CheckUpcomingSunEventsUseCase,
    GetCurrentEventRequest,
    GetCurrentSunEventUseCase,
)
from ...sun_events.infrastructure.json_repository import JSONSunEventRepository
from ...timelapse.application.use_cases import (
    CalculateTimelapseRequest,
    CalculateTimelapseUseCase,
)


class TimelapseRequestModel(BaseModel):
    """Pydantic model for timelapse calculation request."""

    period_type: str  # "sunrise" or "sunset"
    video_duration_seconds: int = 20
    video_fps: int = 60
    photo_size_mb: float = 10.0


class TimelapseResponseModel(BaseModel):
    """Pydantic model for timelapse calculation response."""

    period_type: str
    start_time: str
    end_time: str
    total_duration_seconds: float
    video_duration_seconds: int
    video_fps: int
    total_frames: int
    interval_seconds: float
    photos_needed: int
    estimated_file_size_mb: float


class ShootCameraRequestModel(BaseModel):
    """Pydantic model for camera shooting request."""

    subject_distance: float
    speed: float
    iso_value: int
    shots: int
    interval: float


class ShootCameraResponseModel(BaseModel):
    """Pydantic model for camera shooting response."""

    success: bool
    message: str
    shooting_id: Optional[str] = None


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="Sun Events API", version="1.0.0")

    # Initialize dependencies
    sun_event_repository = JSONSunEventRepository()
    get_current_use_case = GetCurrentSunEventUseCase(sun_event_repository)
    get_upcoming_use_case = CheckUpcomingSunEventsUseCase(sun_event_repository)
    calculate_timelapse_use_case = CalculateTimelapseUseCase(sun_event_repository)

    # Initialize camera dependencies
    script_generator = CHDKPTPScriptGenerator()
    camera_service = CHDKPTPCameraService(script_generator)
    shoot_camera_use_case = ShootCameraUseCase(camera_service)

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {"message": "Sun Events API"}

    @app.get("/current")
    async def get_current_event():
        """Get current sun event period if any."""
        response = get_current_use_case.execute(
            GetCurrentEventRequest(current_time=datetime.now())
        )

        if response.current_period:
            return {
                "period_type": response.current_period.period_type,
                "start_time": response.current_period.start_time.isoformat(),
                "end_time": response.current_period.end_time.isoformat(),
                "event_date": (response.current_period.event_date.strftime("%Y-%m-%d")),
            }
        else:
            return {"message": "No current sun event period"}

    @app.get("/upcoming")
    async def get_upcoming_events():
        """Get upcoming sun event periods."""
        response = get_upcoming_use_case.execute(
            CheckUpcomingEventsRequest(
                current_time=datetime.now(), look_ahead_minutes=1440
            )
        )

        upcoming_periods = []
        for period in response.upcoming_periods:
            upcoming_periods.append(
                {
                    "period_type": period.period_type,
                    "start_time": period.start_time.isoformat(),
                    "end_time": period.end_time.isoformat(),
                    "event_date": period.event_date.strftime("%Y-%m-%d"),
                }
            )

        return {"upcoming_periods": upcoming_periods}

    @app.post("/timelapse", response_model=TimelapseResponseModel)
    async def calculate_timelapse(request: TimelapseRequestModel):
        """Calculate timelapse parameters for a sun event period."""
        try:
            response = calculate_timelapse_use_case.execute(
                CalculateTimelapseRequest(
                    period_type=request.period_type,
                    video_duration_seconds=request.video_duration_seconds,
                    video_fps=request.video_fps,
                    photo_size_mb=request.photo_size_mb,
                )
            )

            params = response.timelapse_parameters
            return TimelapseResponseModel(
                period_type=params.period_type,
                start_time=params.start_time.isoformat(),
                end_time=params.end_time.isoformat(),
                total_duration_seconds=params.total_duration_seconds,
                video_duration_seconds=params.video_duration_seconds,
                video_fps=params.video_fps,
                total_frames=params.total_frames,
                interval_seconds=params.interval_seconds,
                photos_needed=params.photos_needed,
                estimated_file_size_mb=params.estimated_file_size_mb,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/camera/shoot", response_model=ShootCameraResponseModel)
    async def shoot_camera(request: ShootCameraRequestModel):
        """Shoot camera with given parameters."""
        try:
            response = shoot_camera_use_case.execute(
                ShootCameraRequest(
                    subject_distance=request.subject_distance,
                    speed=request.speed,
                    iso_value=request.iso_value,
                    shots=request.shots,
                    interval=request.interval,
                )
            )

            return ShootCameraResponseModel(
                success=response.success,
                message=response.message,
                shooting_id=response.shooting_id,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return app
