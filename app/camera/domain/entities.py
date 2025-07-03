from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class CameraShootingResult:
    """Domain entity for camera shooting results."""

    success: bool
    message: str
    shooting_id: Optional[str] = None
    image_path: Optional[str] = None
    timestamp: datetime = None


@dataclass
class CameraCommand:
    """Domain entity for camera commands."""

    command_type: str  # "shoot", "auto_shoot", "burst_shoot", etc.
    parameters: dict
    timestamp: datetime = None


@dataclass
class CameraStatus:
    """Domain entity for camera status."""

    is_connected: bool
    is_recording: bool
    current_mode: Optional[str] = None
    battery_level: Optional[int] = None
    storage_available: Optional[int] = None  # in MB


@dataclass
class LiveViewResult:
    """Domain entity for live view results."""

    success: bool
    message: str
    image_data: Optional[bytes] = None
    image_format: Optional[str] = None  # "jpeg", "ppm", etc.
    timestamp: datetime = None


@dataclass
class LiveViewStream:
    """Domain entity for live view stream configuration."""

    framerate: float = 5.0  # FPS (max: 8 FPS due to camera hardware)
    quality: int = 80  # JPEG quality (1-100), default 80
