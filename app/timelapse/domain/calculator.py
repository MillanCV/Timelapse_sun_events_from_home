from datetime import datetime

from .entities import TimelapseParameters


class TimelapseCalculator:
    """Domain service for calculating timelapse parameters."""

    @staticmethod
    def calculate_parameters(
        period_type: str,
        start_time: datetime,
        end_time: datetime,
        video_duration_seconds: int = 20,
        video_fps: int = 60,
        photo_size_mb: float = 10.0,
    ) -> TimelapseParameters:
        """Calculate timelapse parameters for a given period."""

        # Calculate total duration of the period
        total_duration_seconds = (end_time - start_time).total_seconds()

        # Calculate total frames needed for the video
        total_frames = video_duration_seconds * video_fps

        # Calculate interval between photos
        interval_seconds = total_duration_seconds / total_frames

        # Calculate number of photos needed
        photos_needed = int(total_duration_seconds / interval_seconds)

        # Calculate estimated file size
        estimated_file_size_mb = photos_needed * photo_size_mb

        return TimelapseParameters(
            period_type=period_type,
            start_time=start_time,
            end_time=end_time,
            total_duration_seconds=total_duration_seconds,
            video_duration_seconds=video_duration_seconds,
            video_fps=video_fps,
            total_frames=total_frames,
            interval_seconds=interval_seconds,
            photos_needed=photos_needed,
            estimated_file_size_mb=estimated_file_size_mb,
        )

    @staticmethod
    def validate_period_type(period_type: str) -> bool:
        """Validate that the period type is supported."""
        return period_type.lower() in ["sunrise", "sunset"]

    @staticmethod
    def validate_video_parameters(video_duration_seconds: int, video_fps: int) -> bool:
        """Validate video parameters."""
        return (
            video_duration_seconds > 0
            and video_fps > 0
            and video_fps <= 120  # Reasonable upper limit
        )
