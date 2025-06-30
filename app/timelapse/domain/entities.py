from dataclasses import dataclass
from datetime import datetime


@dataclass
class TimelapseParameters:
    """Domain entity representing timelapse parameters for a sun event period."""

    period_type: str
    start_time: datetime
    end_time: datetime
    total_duration_seconds: float
    video_duration_seconds: int
    video_fps: int
    total_frames: int
    interval_seconds: float
    photos_needed: int
    estimated_file_size_mb: float
