from dataclasses import dataclass
from datetime import datetime, timedelta

from ...sun_events.domain.repositories import SunEventRepository
from ..domain.entities import TimelapseParameters
from ..domain.calculator import TimelapseCalculator


@dataclass
class CalculateTimelapseRequest:
    """Request for calculating timelapse parameters."""

    period_type: str  # "sunrise" or "sunset"
    video_duration_seconds: int = 20
    video_fps: int = 60
    photo_size_mb: float = 10.0


@dataclass
class CalculateTimelapseResponse:
    """Response for calculating timelapse parameters."""

    timelapse_parameters: TimelapseParameters


class CalculateTimelapseUseCase:
    """Use case for calculating timelapse parameters."""

    def __init__(self, sun_event_repository: SunEventRepository):
        self.sun_event_repository = sun_event_repository
        self.timelapse_calculator = TimelapseCalculator()

    def execute(self, request: CalculateTimelapseRequest) -> CalculateTimelapseResponse:
        """Execute the use case."""
        # Validate inputs
        if not self.timelapse_calculator.validate_period_type(request.period_type):
            raise ValueError("Period type must be 'sunrise' or 'sunset'")

        if not self.timelapse_calculator.validate_video_parameters(
            request.video_duration_seconds, request.video_fps
        ):
            raise ValueError("Invalid video parameters")

        # Get today's sun event
        today = datetime.now().date()
        sun_event = self.sun_event_repository.get_sun_event_by_date_sync(
            datetime.combine(today, datetime.min.time())
        )

        if not sun_event:
            raise ValueError("No sun event data available for today")

        # Determine start and end times based on period type
        if request.period_type.lower() == "sunrise":
            start_time = sun_event.golden_hour_morning_start
            end_time = sun_event.golden_hour_morning_end + timedelta(minutes=30)
        elif request.period_type.lower() == "sunset":
            start_time = sun_event.golden_hour_evening_start - timedelta(minutes=30)
            end_time = sun_event.dusk
        else:
            raise ValueError("Period type must be 'sunrise' or 'sunset'")

        # Calculate timelapse parameters using domain service
        timelapse_parameters = self.timelapse_calculator.calculate_parameters(
            period_type=request.period_type,
            start_time=start_time,
            end_time=end_time,
            video_duration_seconds=request.video_duration_seconds,
            video_fps=request.video_fps,
            photo_size_mb=request.photo_size_mb,
        )

        return CalculateTimelapseResponse(timelapse_parameters=timelapse_parameters)
