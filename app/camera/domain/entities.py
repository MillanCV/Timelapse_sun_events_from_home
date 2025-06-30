from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class TimelapseRecordingParameters:
    """Domain entity for timelapse recording parameters."""

    shots: int
    interval_seconds: float
    output_directory: str
    period_type: str  # "sunrise" or "sunset"
    start_time: datetime
    end_time: datetime


@dataclass
class CameraCommand:
    """Domain entity for camera commands."""

    command_type: str  # "start_timelapse", "stop_timelapse", etc.
    parameters: dict
    timestamp: datetime


@dataclass
class CameraStatus:
    """Domain entity for camera status."""

    is_connected: bool
    is_recording: bool
    current_mode: Optional[str] = None
    battery_level: Optional[int] = None
    storage_available: Optional[int] = None  # in MB
